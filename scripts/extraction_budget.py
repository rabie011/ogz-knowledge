#!/usr/bin/env python3
"""Fail-closed per-run budget contract for paid observation extraction.

Pure planning happens before credentials or provider imports. Live runs reserve their full
ceiling, reserve each call, then settle provider usage through the canonical spend ledger.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import struct
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_UP
from pathlib import Path
from typing import Any, Callable, Iterable


MODEL = "claude-haiku-4-5-20251001"
WRITER_ID = "02-Platform-AI/Knowledge/brain/scripts/batch_extract.py"
MAX_IMAGE_TOKENS = 1600
MAX_IMAGE_EDGE = 1568
MAX_IMAGE_PIXELS = 1_150_000
MILLION = Decimal(1_000_000)
HARD_MAX_CALLS = 5
HARD_MAX_USD = Decimal("0.15")
HARD_MAX_TOKENS = 60_000


class BudgetRefusal(RuntimeError):
    """A hard budget or ledger boundary refused the run."""


@dataclass(frozen=True)
class BudgetCaps:
    max_calls: int
    max_usd: Decimal
    max_tokens: int


@dataclass(frozen=True)
class CallEstimate:
    index: int
    image: Path
    image_tokens: int
    text_tokens: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    usd: Decimal
    dimension_method: str
    image_sha256: str


@dataclass(frozen=True)
class RunPlan:
    model: str
    prices: dict[str, Decimal]
    calls: tuple[CallEstimate, ...]
    estimated_tokens: int
    estimated_usd: Decimal
    caps: BudgetCaps

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "prices_per_mtok": {key: float(value) for key, value in self.prices.items()},
            "estimate": {
                "calls": len(self.calls),
                "tokens": self.estimated_tokens,
                "usd": float(self.estimated_usd),
            },
            "caps": {
                "max_calls": self.caps.max_calls,
                "max_tokens": self.caps.max_tokens,
                "max_usd": float(self.caps.max_usd),
            },
            "machine_ceiling": {
                "max_calls": HARD_MAX_CALLS,
                "max_tokens": HARD_MAX_TOKENS,
                "max_usd": float(HARD_MAX_USD),
            },
            "call_estimates": [
                {
                    "index": call.index,
                    "image": call.image.name,
                    "image_tokens": call.image_tokens,
                    "text_tokens": call.text_tokens,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "total_tokens": call.total_tokens,
                    "usd": float(call.usd),
                    "dimension_method": call.dimension_method,
                    "image_sha256": call.image_sha256,
                }
                for call in self.calls
            ],
        }


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_UP)


def load_prices(config_path: Path, model: str = MODEL) -> dict[str, Decimal]:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        row = config["prices_per_mtok"][model]
        prices = {"in": Decimal(str(row["in"])), "out": Decimal(str(row["out"]))}
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise BudgetRefusal(f"pricing missing or invalid for {model}: {exc}") from exc
    if prices["in"] <= 0 or prices["out"] <= 0:
        raise BudgetRefusal(f"pricing must be positive for paid model {model}")
    return prices


def _jpeg_dimensions(path: Path) -> tuple[int, int] | None:
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            return None
        while True:
            marker_start = handle.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if not marker:
                return None
            code = marker[0]
            if code in {0xD8, 0xD9}:
                continue
            raw_length = handle.read(2)
            if len(raw_length) != 2:
                return None
            length = struct.unpack(">H", raw_length)[0]
            if length < 2:
                return None
            if code in sof:
                payload = handle.read(5)
                if len(payload) != 5:
                    return None
                height, width = struct.unpack(">HH", payload[1:5])
                return width, height
            handle.seek(length - 2, os.SEEK_CUR)


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:32]
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        return _jpeg_dimensions(path)
    except (OSError, struct.error):
        return None


def estimate_image_tokens(path: Path) -> tuple[int, str]:
    dimensions = image_dimensions(path)
    if not dimensions:
        return MAX_IMAGE_TOKENS, "fallback_max_1600"
    width, height = dimensions
    if width <= 0 or height <= 0:
        return MAX_IMAGE_TOKENS, "fallback_max_1600"
    scale = min(
        Decimal(1),
        Decimal(MAX_IMAGE_EDGE) / Decimal(width),
        Decimal(MAX_IMAGE_EDGE) / Decimal(height),
        Decimal(str(math.sqrt(MAX_IMAGE_PIXELS / (width * height))))
        if width * height > MAX_IMAGE_PIXELS else Decimal(1),
    )
    scaled_width = max(1, int(Decimal(width) * scale))
    scaled_height = max(1, int(Decimal(height) * scale))
    tokens = min(MAX_IMAGE_TOKENS, math.ceil((scaled_width * scaled_height) / 750))
    return max(1, tokens), "dimensions_area_div_750"


def estimate_text_tokens(system: str, user: str) -> int:
    # One token per UTF-8 byte plus envelope overhead is deliberately conservative.
    return len((system + user).encode("utf-8")) + 256


def price_tokens(input_tokens: int, output_tokens: int, prices: dict[str, Decimal]) -> Decimal:
    return _money(
        Decimal(input_tokens) / MILLION * prices["in"]
        + Decimal(output_tokens) / MILLION * prices["out"]
    )


def build_plan(
    images: Iterable[Path],
    user_prompts: Iterable[str],
    system_prompt: str,
    max_output_tokens: int,
    caps: BudgetCaps,
    pricing_path: Path,
) -> RunPlan:
    if caps.max_calls <= 0 or caps.max_tokens <= 0 or caps.max_usd <= 0:
        raise BudgetRefusal("max-calls, max-tokens, and max-usd must all be positive")
    if (
        caps.max_calls > HARD_MAX_CALLS
        or caps.max_tokens > HARD_MAX_TOKENS
        or caps.max_usd > HARD_MAX_USD
    ):
        raise BudgetRefusal(
            "requested caps exceed machine ceiling "
            f"({HARD_MAX_CALLS} calls, {HARD_MAX_TOKENS} tokens, ${HARD_MAX_USD})"
        )
    if max_output_tokens <= 0:
        raise BudgetRefusal("provider max output tokens must be positive")
    image_list = tuple(images)
    prompt_list = tuple(user_prompts)
    if not image_list or len(image_list) != len(prompt_list):
        raise BudgetRefusal("estimate requires one prompt for every selected image")
    prices = load_prices(pricing_path)
    calls = []
    for index, (image, prompt) in enumerate(zip(image_list, prompt_list), start=1):
        image_tokens, method = estimate_image_tokens(image)
        text_tokens = estimate_text_tokens(system_prompt, prompt)
        input_tokens = image_tokens + text_tokens
        total_tokens = input_tokens + max_output_tokens
        calls.append(CallEstimate(
            index=index,
            image=image,
            image_tokens=image_tokens,
            text_tokens=text_tokens,
            input_tokens=input_tokens,
            output_tokens=max_output_tokens,
            total_tokens=total_tokens,
            usd=price_tokens(input_tokens, max_output_tokens, prices),
            dimension_method=method,
            image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
        ))
    estimated_tokens = sum(call.total_tokens for call in calls)
    estimated_usd = _money(sum((call.usd for call in calls), Decimal(0)))
    reasons = []
    if len(calls) > caps.max_calls:
        reasons.append(f"calls {len(calls)}>{caps.max_calls}")
    if estimated_tokens > caps.max_tokens:
        reasons.append(f"tokens {estimated_tokens}>{caps.max_tokens}")
    if estimated_usd > caps.max_usd:
        reasons.append(f"usd {estimated_usd}>{caps.max_usd}")
    if reasons:
        raise BudgetRefusal("budget cap refused estimate: " + ", ".join(reasons))
    return RunPlan(MODEL, prices, tuple(calls), estimated_tokens, estimated_usd, caps)


def assert_writer_registered(registry_path: Path) -> None:
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        spend = next(row for row in registry["ledgers"] if row.get("name") == "spend")
        writers = spend.get("writers") or []
    except (OSError, StopIteration, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise BudgetRefusal(f"spend registry unreadable: {exc}") from exc
    if WRITER_ID not in writers:
        raise BudgetRefusal(f"spend writer not FABLE-registered: {WRITER_ID}")


def canonical_receipt_writer(system_root: Path) -> Callable[[dict[str, Any]], None]:
    ledger_path = system_root / "tools" / "jail" / "ledger.py"
    spec = importlib.util.spec_from_file_location("ogz_extraction_spend_ledger", ledger_path)
    if spec is None or spec.loader is None:
        raise BudgetRefusal(f"canonical ledger writer unavailable: {ledger_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def write(row: dict[str, Any]) -> None:
        try:
            module.append("spend", row, actor="batch_extract")
        except Exception as exc:
            raise BudgetRefusal(f"spend receipt append failed: {exc}") from exc

    return write


def _note(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class BudgetRun:
    def __init__(
        self,
        plan: RunPlan,
        writer: Callable[[dict[str, Any]], None],
        run_id: str,
    ) -> None:
        self.plan = plan
        self.writer = writer
        self.run_id = run_id
        self.calls = 0
        self.tokens = 0
        self.usd = Decimal(0)
        self.reserved = False
        self.closed = False
        self.authorized_call_index: int | None = None

    def _write(self, *, calls: int, usd: Decimal, status: str, note: dict[str, Any]) -> None:
        try:
            self.writer({
                "id": self.run_id,
                "worker": "batch_extract",
                "lane": "brain-extraction",
                "calls": calls,
                "usd": float(_money(usd)),
                "minutes": 0.0,
                "status": status,
                "note": _note(note),
            })
        except BudgetRefusal:
            raise
        except Exception as exc:
            raise BudgetRefusal(f"spend receipt writer failed: {type(exc).__name__}") from exc

    def reserve(self) -> None:
        if self.reserved:
            raise BudgetRefusal("run budget already reserved")
        self._write(calls=0, usd=Decimal(0), status="reserved", note={
            "event": "estimate_reserve",
            "model": self.plan.model,
            "reserved_calls": len(self.plan.calls),
            "reserved_tokens": self.plan.estimated_tokens,
            "reserved_usd": float(self.plan.estimated_usd),
            "caps": self.plan.as_dict()["caps"],
        })
        self.reserved = True

    def authorize_call(self, call: CallEstimate) -> None:
        if not self.reserved or self.closed:
            raise BudgetRefusal("call attempted outside an open reservation")
        if call.index != self.calls + 1:
            raise BudgetRefusal(f"call order drift: expected {self.calls + 1}, got {call.index}")
        if self.authorized_call_index is not None:
            raise BudgetRefusal(f"call {self.authorized_call_index} is already authorized")
        current_sha = hashlib.sha256(call.image.read_bytes()).hexdigest()
        if current_sha != call.image_sha256:
            raise BudgetRefusal(f"image changed after estimate: {call.image.name}")
        self._write(calls=0, usd=Decimal(0), status="reserved", note={
            "event": "call_reserve",
            "call_index": call.index,
            "image_sha256": call.image_sha256,
            "reserved_tokens": call.total_tokens,
            "reserved_usd": float(call.usd),
        })
        self.authorized_call_index = call.index

    def _assert_authorized(self, call: CallEstimate) -> None:
        if not self.reserved or self.closed:
            raise BudgetRefusal("settlement attempted outside an open reservation")
        if self.authorized_call_index != call.index:
            raise BudgetRefusal(
                f"settlement call mismatch: authorized={self.authorized_call_index}, got={call.index}"
            )

    def settle_success(self, call: CallEstimate, usage: Any) -> None:
        self._assert_authorized(call)
        try:
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            input_tokens += int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
            input_tokens += int(getattr(usage, "cache_read_input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        except (TypeError, ValueError, OverflowError) as exc:
            refusal = BudgetRefusal("provider usage malformed; conservatively settling reserved call")
            self.settle_error(call, refusal)
            raise refusal from exc
        if input_tokens <= 0 or output_tokens < 0:
            refusal = BudgetRefusal("provider usage missing; conservatively settling reserved call")
            self.settle_error(call, refusal)
            raise refusal
        actual_tokens = input_tokens + output_tokens
        actual_usd = price_tokens(input_tokens, output_tokens, self.plan.prices)
        self.calls += 1
        self.tokens += actual_tokens
        self.usd = _money(self.usd + actual_usd)
        self._write(calls=1, usd=actual_usd, status="done", note={
            "event": "call_settle",
            "call_index": call.index,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": actual_tokens,
            "actual_usd": float(actual_usd),
            "model": self.plan.model,
        })
        self.authorized_call_index = None
        breaches = []
        if self.calls > self.plan.caps.max_calls:
            breaches.append("calls")
        if self.tokens > self.plan.caps.max_tokens:
            breaches.append("tokens")
        if self.usd > self.plan.caps.max_usd:
            breaches.append("usd")
        if breaches:
            raise BudgetRefusal("actual usage breached reserved cap: " + ",".join(breaches))

    def settle_error(self, call: CallEstimate, error: Exception) -> None:
        self._assert_authorized(call)
        self.calls += 1
        self.tokens += call.total_tokens
        self.usd = _money(self.usd + call.usd)
        self._write(calls=1, usd=call.usd, status="parked", note={
            "event": "call_error_conservative_settle",
            "call_index": call.index,
            "error_type": type(error).__name__,
            "reserved_tokens_charged": call.total_tokens,
            "reserved_usd_charged": float(call.usd),
        })
        self.authorized_call_index = None

    def close(self, status: str, reason: str = "") -> None:
        if self.closed or not self.reserved:
            return
        self._write(calls=0, usd=Decimal(0), status=status, note={
            "event": "reservation_close",
            "actual_calls": self.calls,
            "actual_tokens": self.tokens,
            "actual_usd": float(self.usd),
            "reason": reason,
        })
        self.closed = True
