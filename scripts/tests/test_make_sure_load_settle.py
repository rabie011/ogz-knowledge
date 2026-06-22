"""B283 — pre-flight load-settle (de-conflict the orchestra stampede).

Deterministic tests for the load-spike defer that stops make_sure's load-sensitive probes from
flapping a FALSE RED when the :13/:43 fire collides with session-start. Pure `load_saturated` +
the bounded `settle_load_spike` loop with injected load-reader & sleeper (no real sleep, no real
load — the test never waits and never depends on the host's actual load)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import make_sure as ms  # noqa: E402


class LoadSaturatedTest(unittest.TestCase):
    def test_baseline_not_saturated(self):
        # 1.4 on 10 cores = 0.14/core, well under the 0.7 bar
        self.assertFalse(ms.load_saturated(1.4, 10))

    def test_exactly_at_bar_is_saturated(self):
        self.assertTrue(ms.load_saturated(7.0, 10))           # 0.7/core, inclusive

    def test_well_above_bar_is_saturated(self):
        self.assertTrue(ms.load_saturated(25.0, 10))

    def test_zero_cpu_coerced_to_one(self):
        self.assertFalse(ms.load_saturated(0.5, 0))           # <0.7 on 1 core
        self.assertTrue(ms.load_saturated(0.8, 0))            # >=0.7 on 1 core

    def test_custom_per_core_threshold(self):
        self.assertTrue(ms.load_saturated(10.0, 10, per_core=1.0))
        self.assertFalse(ms.load_saturated(9.9, 10, per_core=1.0))


class SettleLoadSpikeTest(unittest.TestCase):
    def test_calm_box_does_not_wait(self):
        slept = []
        out = ms.settle_load_spike(read_load=lambda: 1.0,
                                   sleeper=lambda s: slept.append(s), ncpu=10)
        self.assertEqual(out["deferred_s"], 0)
        self.assertTrue(out["settled"])
        self.assertEqual(slept, [])                           # never slept

    def test_transient_spike_waits_then_settles(self):
        reads = iter([20.0, 20.0, 1.0, 1.0])                  # saturated twice, then clears
        slept = []
        out = ms.settle_load_spike(read_load=lambda: next(reads),
                                   sleeper=lambda s: slept.append(s),
                                   ncpu=10, max_wait=60, step=10)
        self.assertEqual(out["deferred_s"], 20)              # two 10s steps
        self.assertTrue(out["settled"])
        self.assertEqual(slept, [10, 10])

    def test_sustained_outage_gives_up_at_ceiling(self):
        # never clears → bounded by max_wait, settled False (caller still runs probes → honest RED)
        slept = []
        out = ms.settle_load_spike(read_load=lambda: 50.0,
                                   sleeper=lambda s: slept.append(s),
                                   ncpu=10, max_wait=30, step=10)
        self.assertEqual(out["deferred_s"], 30)             # 3 steps then stop
        self.assertFalse(out["settled"])
        self.assertEqual(slept, [10, 10, 10])

    def test_zero_max_wait_is_noop_probe(self):
        slept = []
        out = ms.settle_load_spike(read_load=lambda: 50.0,
                                   sleeper=lambda s: slept.append(s),
                                   ncpu=10, max_wait=0)
        self.assertEqual(out["deferred_s"], 0)
        self.assertFalse(out["settled"])                    # honestly reports still-hot
        self.assertEqual(slept, [])

    def test_diagnostic_shape(self):
        out = ms.settle_load_spike(read_load=lambda: 1.0, sleeper=lambda s: None, ncpu=8)
        self.assertEqual(set(out), {"deferred_s", "final_load", "ncpu", "settled"})
        self.assertEqual(out["ncpu"], 8)
        self.assertEqual(out["final_load"], 1.0)

    def test_load_settle_is_not_a_phone_gate(self):
        # _load_settle is a "_"-prefixed diagnostic → must never page Mohamed even if it looked falsey
        checks = {"_load_settle": {"settled": False}, "portal_mini": True}
        self.assertEqual(ms._phone_dead(checks, {}), [])


if __name__ == "__main__":
    unittest.main()
