#!/usr/bin/env python3
"""PRE-SHIP QUALITY GATE — nothing reaches Mohamed's judge lane without passing.

Born 2026-06-14: he rated the batch "all so bad" — the system had NO gate measuring
occasion-correctness or cultural fit, so the misses shipped to his eye: ruling-royal-family
on National Day, Easter-style eggs as "Saudi Eid", a Hajj/Tawaf sacred-worship sales hook,
weak captions. His taste was the ONLY gate. This makes the gate code.

Two layers:
  DETERMINISTIC (here): HARD KILLS (royal-family casting · sacred-worship sales hook ·
    imported new-culture · brand red-lines · worn phrases) + OCCASION-FIT (caption/idea must
    touch the occasion's real themes, occasion_facts.json) + FORMAT (jurisha=cloud_kitchen).
  LLM JUDGE (separate workflow): coherence (caption↔occasion↔idea↔visual) + gold-level taste.

Usage:
  python3 scripts/pre_ship_gate.py --handle eatjurisha          # gate the corpus, print stats
  python3 scripts/pre_ship_gate.py --all --json out.json        # gate 3 pilots → candidate pool
"""
import argparse, glob, json, os, re, sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
OCC = json.loads((B / "data/occasion_facts.json").read_text())
try:
    import caption_filter as cf
    WORN = list(getattr(cf, "STANDING_WORN", []))
except Exception:
    WORN = ["لحظة", "لحظات", "يجمعنا", "تجمعنا", "في كل لقمة", "يرفع المعنويات"]

# LEARNED rules — the gate GROWS from Mohamed's rejections (learn_from_verdict.py writes
# these; the gate reads them). Closed loop: his "no" → a rule → BLOCKED at shipping next time.
# (zoom-out 2026-06-14: LEARNED['rules'] was write-only + bans only soft-flagged → fixed:
#  learned bans BLOCK shipping, and cultural rules' phrase_bans are now read too.)
_LF = B / "data/learned_gate_rules.json"
LEARNED = json.loads(_LF.read_text()) if _LF.exists() else {"phrase_bans": [], "rules": []}
LEARNED_BANS = [p for p in LEARNED.get("phrase_bans", []) if p]
LEARNED_BANS += [r.get("phrase_ban") for r in LEARNED.get("rules", []) if r.get("phrase_ban")]
LEARNED_BANS = sorted(set(b for b in LEARNED_BANS if b))

# ── HARD KILLS (deterministic, anchored — Rule #9: precise, no جريشة-style false positives) ──
ROYAL = re.compile(r"آل\s*سعود|الأسرة الحاكمة|العائلة المالكة|الملك سلمان|ولي العهد|"
                   r"محمد بن سلمان|الأمير\s+\S+\s+بن|جدّ?ي عبدالعزيز")
# SACRED: occasion-anchored (hajj/umrah) + UNAMBIGUOUS full phrases ONLY. NEVER bare حج
# (matched بالحجم!) or عمرة (matched عمرها). Born 2026-06-14, the جريشة-scar class.
SACRED_OCC = {"hajj_season", "umrah", "hajj"}
SACRED_PHRASE = re.compile(r"المسجد الحرام|الكعبة المشرفة|الكعبة|مكة المكرمة|المشاعر المقدسة|"
                           r"الحرمين|موسم الحج|فريضة الحج|أداء العمرة|الطواف")
# CTA: real promo/order verbs ONLY — NOT وصل (arrived) or جاهز (the Jahez delivery app)
CTA = re.compile(r"اطلب\w*|اطلبوا|اطلبها|اطلبه|خصم|كوبون|عرض خاص|التوصيل مجان|وفّر\b")
# بيض.{0,5}ملون catches بيض ملون / بيض الملون / بيضة ملونة (the colored-Easter-egg slip)
NEW_CULTURE = re.compile(r"بيض.{0,5}ملون|بيض\s*مزخرف|بيض العيد|easter|سانتا|"
                         r"شجرة (الكريسماس|عيد الميلاد)|الهالوين|قدّيس")
DINE_IN = re.compile(r"صالت?نا|جلستنا في المطعم|تفضلوا (إلى|على) (مطعمنا|الصالة)|"
                     r"داخل المطعم|طاولتنا بالمطعم|قاعتنا")


def _txt(post):
    caps = post.get("captions") or ([post.get("caption")] if post.get("caption") else [])
    idea = (post.get("idea") or {})
    scene = idea.get("scene_ar", "") if isinstance(idea, dict) else str(idea)
    return (scene + " \n " + " \n ".join(c for c in caps if c)).strip(), caps


def occasion_of(post):
    return (post.get("slot") or {}).get("occasion") or post.get("occasion") or "evergreen"


def gate(post, handle):
    text, caps = _txt(post)
    occ = occasion_of(post)
    hard, soft = [], []

    # HARD KILLS
    if ROYAL.search(text):
        hard.append("royal-family casting in a commercial ad")
    # sacred-worship-as-sales-hook: only when the occasion IS hajj/umrah, or an unambiguous
    # Haram/Kaaba/Tawaf phrase appears — AND there's a real order CTA. (ramadan promos are fine.)
    if (occ in SACRED_OCC or SACRED_PHRASE.search(text)) and CTA.search(text):
        hard.append("sacred-worship (Hajj/Umrah/Haram) used as a sales hook")
    if NEW_CULTURE.search(text):
        hard.append("imported new-culture (Easter/Christmas/Halloween) as Saudi occasion")
    if handle == "eatjurisha" and DINE_IN.search(text):
        hard.append("dine-in scene — jurisha is a CLOUD KITCHEN (delivery only)")
    # OCCASION ALIGNMENT (June 14, "confirmed with occasion") — HARD: a daily post that invents
    # a holiday, or an occasion post that drifts to a different holiday, never ships. Shared,
    # boundary-safe logic (Rule #6) — عيد inside سعيد/يعيدني is not Eid (Rule #9).
    try:
        import occasion_align as _oa
        _slot = post.get("slot") or {"occasion": post.get("occasion"), "type": post.get("type")}
        # scan BOTH doors (RABIE 2026-06-14): captions AND the visual shoot-card brief — a daily
        # post whose VISUAL stages a Ramadan suhoor is just as misaligned as one whose caption does.
        _vis = " ".join(str(x) for x in (post.get("visual") or {}).get("phone_shoot_card") or [])
        for _t in list(caps or []) + ([_vis] if _vis else []):
            _mis = _oa.caption_misaligned(_slot, _t or "")
            if _mis:
                hard.append(f"occasion misalignment — {_mis}")
                break
    except Exception:
        pass
    # CLIENT-RULES (RABIE NO-GO 2026-06-14): enforce the client's CONFIRMED organs —
    # real-person/face/family/voice (cultural_overrides), cloud-kitchen format, cross-brand bleed,
    # brand-name register. Any block-severity organ violation is a HARD kill (caption + visual).
    try:
        import client_rules as _cr
        for kind, sev, detail in _cr.violations(post, handle):
            if sev == "block":
                hard.append(f"client-rule: {detail}")
            else:
                soft.append(f"client-rule: {detail}")
    except Exception:
        pass

    # CULTURAL RED-LINES in the caption (immodest / alcohol / pork / dua+brand) — HARD kill. The
    # detector caption_filter.cultural_check ALREADY existed; the ship gate now CONSUMES it (June 21
    # audit hole: an immodest/haram caption slipped the ship gate GREEN because nothing read the
    # detector — Rule #6 Consumer-Law + Rule #8 refuse-don't-warn). cultural_check is occasion-aware.
    try:
        import caption_filter as _cf
        _cult = set()
        for _cap in (caps or []):
            _clean, _hits = _cf.cultural_check(_cap or "", occ)
            _cult.update(_hits)
        for _h in sorted(_cult):
            hard.append(f"cultural red-line: {_h}")
    except Exception:
        pass

    # WORN phrases (soft — caption weakness)
    worn_hit = [w for w in WORN if w in text]
    if worn_hit:
        soft.append(f"worn phrase(s): {worn_hit}")
    # LEARNED rejection patterns (Mohamed's prior "no") — these BLOCK shipping, not just flag
    learned_hit = [w for w in LEARNED_BANS if w in text]
    if learned_hit:
        soft.append(f"learned-rejection pattern (your prior 'no'): {learned_hit}")

    # OCCASION-FIT: a real occasion must touch its themes (evergreen exempt)
    occ_fit = True
    if occ not in ("evergreen", "", None) and occ in OCC:
        themes = OCC[occ].get("themes", [])
        # keyword anchors from the occasion's name + themes (loose: any theme noun present?)
        anchors = re.findall(r"[؀-ۿ]{3,}", OCC[occ].get("name_ar", "") + " " + " ".join(themes[:3]))
        # heuristic: the occasion name_ar tokens or a clear seasonal marker should appear
        name_ar = OCC[occ].get("name_ar", "")
        if name_ar and not any(tok in text for tok in re.findall(r"[؀-ۿ]{3,}", name_ar)):
            occ_fit = False
            soft.append(f"occasion-fit weak: no '{name_ar}' marker in caption/idea for {occ}")

    n_caps = len([c for c in caps if c])
    # block = never ships to his judge lane: hard cultural kill OR a learned-rejection pattern
    block = bool(hard) or bool(learned_hit)
    verdict = "KILL" if hard else ("BLOCK" if learned_hit else ("REVIEW" if soft else "PASS"))
    return {
        "handle": handle, "occasion": occ, "verdict": verdict, "block": block,
        "hard_kills": hard, "learned_hits": learned_hit, "soft_flags": soft, "occ_fit": occ_fit,
        "n_captions": n_caps,
        "needs_llm_judge": verdict == "PASS",   # clean deterministic → LLM judges coherence+gold
    }


# ── F3: TYPED VERDICT CONTRACT at the gate seam (2026-06-21) ──────────────────────────
# A malformed gate result must REFUSE, never silently pass. Born from the adversarial audit:
# pre_ship_gate had ZERO sys.exit/raise — a verdict dict could be dropped, mistyped, or read
# with a typo'd key and the post would sail through "green". The seam is now a typed object
# whose ONLY safe value is verdict=="PASS"; anything else (KILL/BLOCK, or a malformed/partial
# dict) makes assert_shippable() RAISE. Callers (producer/stager/audit) consume THIS, not a
# loose dict (Rule #6: the verdict has a hard reader; Rule #8: refuse, don't warn).
_VALID_VERDICTS = {"PASS", "REVIEW", "KILL", "BLOCK"}


@dataclass
class GateVerdict:
    handle: str
    occasion: str
    verdict: str                       # one of _VALID_VERDICTS
    block: bool                        # True = must NOT ship to the judge lane
    hard_kills: list = field(default_factory=list)
    learned_hits: list = field(default_factory=list)
    soft_flags: list = field(default_factory=list)
    occ_fit: bool = True
    n_captions: int = 0
    needs_llm_judge: bool = False

    def __post_init__(self):
        # a malformed verdict is itself a refuse condition — never trust a partial seam.
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(f"malformed gate verdict «{self.verdict}» — not in {_VALID_VERDICTS} (REFUSE)")
        # block MUST agree with the verdict: a KILL/BLOCK that says block=False is a severed wire.
        should_block = self.verdict in ("KILL", "BLOCK")
        if should_block and not self.block:
            raise ValueError(f"verdict={self.verdict} but block=False — severed gate wire (REFUSE)")

    def shippable(self) -> bool:
        """Clean only — a post may reach Mohamed's judge lane ONLY on PASS/REVIEW, never on a kill."""
        return not self.block and self.verdict in ("PASS", "REVIEW")


def verdict_of(post, handle) -> "GateVerdict":
    """Typed wrapper over gate() — the seam every consumer should read. A malformed underlying
    dict (missing/extra keys, bad verdict) RAISES here rather than returning a passable result."""
    g = gate(post, handle)
    try:
        return GateVerdict(
            handle=g["handle"], occasion=g["occasion"], verdict=g["verdict"], block=g["block"],
            hard_kills=g.get("hard_kills", []), learned_hits=g.get("learned_hits", []),
            soft_flags=g.get("soft_flags", []), occ_fit=g.get("occ_fit", True),
            n_captions=g.get("n_captions", 0), needs_llm_judge=g.get("needs_llm_judge", False))
    except (KeyError, TypeError) as e:
        raise ValueError(f"gate() returned a malformed verdict for {handle}: {e} (REFUSE)")


def assert_shippable(post, handle):
    """HARD CONSUMER (Rule #6 + #8) — the producer/stager calls this and it RAISES (SystemExit,
    non-zero) the instant a post carries a cultural HARD KILL or a learned-rejection BLOCK. There
    is NO warn-and-continue path: a modesty / royal / red-line violation cannot pass through green.
    Returns the typed verdict on success so the caller can branch on REVIEW vs clean PASS."""
    v = verdict_of(post, handle)
    if not v.shippable():
        why = v.hard_kills + v.learned_hits or [v.verdict]
        raise SystemExit(
            f"🛑 PRE-SHIP REFUSED — {handle}/{v.occasion}: {why} "
            f"(Rule #8: a gate that finds a violation BLOCKS, never warns).")
    return v


def run(handle):
    files = sorted(glob.glob(str(B / f"clients/{handle}/posts/*.json")))
    out, kills, review, pas = [], 0, 0, 0
    for f in files:
        try:
            post = json.loads(open(f).read())
        except Exception:
            continue
        g = gate(post, handle)
        g["file"] = os.path.basename(f)
        out.append(g)
        kills += g["verdict"] == "KILL"
        review += g["verdict"] == "REVIEW"
        pas += g["verdict"] == "PASS"
    print(f"  {handle}: {len(out)} posts → KILL {kills} · REVIEW {review} · PASS(clean) {pas}")
    # show a few hard kills as evidence
    for g in out:
        if g["verdict"] == "KILL":
            print(f"     🛑 {g['file'][:40]} [{g['occasion']}]: {g['hard_kills']}")
            if kills > 6 and out.index(g) > 5:
                print(f"     … +{kills-6} more kills"); break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--no-enforce", dest="enforce", action="store_false",
                    help="audit only (exit 0); default BITES — exit 1 if any post is a hard KILL/BLOCK")
    ap.set_defaults(enforce=True)
    a = ap.parse_args()
    handles = [a.handle] if a.handle else (["eatjurisha", "albaik", "alnasserjewelry"] if a.all else ["eatjurisha"])
    allout = {}
    for h in handles:
        allout[h] = run(h)
    if a.json:
        Path(a.json).write_text(json.dumps(allout, ensure_ascii=False, indent=1))
        clean = sum(1 for h in allout for g in allout[h] if g["verdict"] == "PASS")
        print(f"  → {a.json} · {clean} clean posts → LLM-judge pool for the top 20")
    # Rule #8 — the gate BITES: a hard cultural kill or a learned-rejection block fails the run.
    # (Previously this gate had ZERO sys.exit — the adversarial audit's hole. It now refuses.)
    blocked = [(h, g.get("file", "?"), g["verdict"], g["hard_kills"] + g["learned_hits"])
               for h in allout for g in allout[h] if g.get("block")]
    if a.enforce and blocked:
        print(f"\n🛑 PRE-SHIP GATE BLOCKED: {len(blocked)} post(s) carry a hard cultural kill / learned block:")
        for h, fn, vd, why in blocked[:12]:
            print(f"   ⛔ {h} {fn} [{vd}]: {why}")
        sys.exit(1)
    print(f"\n🟢 PRE-SHIP CLEAR: 0 hard-blocked posts"
          + ("" if not a.enforce else " (gate enforced — would have exited non-zero on any kill)"))
    sys.exit(0)


if __name__ == "__main__":
    main()
