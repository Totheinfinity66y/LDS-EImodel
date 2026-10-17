from dataclasses import replace
import tempfile
from pathlib import Path
import unittest
import numpy as np

from lds_competitive import CompressedCode, RateDecompressor
from lds_competitive.timeline import RateTimeline, build_timeline


class TimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = RateDecompressor().decompress(CompressedCode(1, 1, 2))
        cls.timeline = build_timeline(cls.result)

    def test_all_29_units_and_true_modes_present(self):
        t = self.timeline
        self.assertEqual(t.rates.shape, (1201, 29))
        self.assertEqual(len(set(t.labels)), 29)
        self.assertEqual(np.count_nonzero(t.modes == "held"), 8)
        self.assertEqual(np.count_nonzero(t.modes == "integrated"), 21)
        self.assertTrue(np.all(t.modes[np.isin(t.groups, ["Readout V", "Gate G"])] == "integrated"))

    def test_raw_rates_exactly_match_records_without_row_normalization(self):
        timeline, traces = self.timeline, self.result.transitions
        for name, group in (("e_rates", "Position E"), ("v_rates", "Readout V"),
                            ("g_rates", "Gate G"), ("m_rates", "Shared M")):
            expected = np.concatenate([getattr(traces[0], name)[:-1], getattr(traces[1], name)[:-1], getattr(traces[2], name)])
            np.testing.assert_array_equal(timeline.columns(group), expected)
        self.assertGreater(timeline.columns("Position E").max(), 1)

    def test_held_encoding_is_actual_unnormalized_rate(self):
        enc = self.result.initial_state.encoding
        for group, pop in (("Direction", enc.direction), ("Step", enc.step), ("Joint", enc.joint)):
            np.testing.assert_array_equal(self.timeline.columns(group), np.tile(pop.rates, (1201, 1)))

    def test_boundary_keeps_E_I_V_G_continuous_and_resets_M(self):
        t = self.timeline
        np.testing.assert_allclose(t.rank_times, [0, .8, 1.6, 2.4], atol=1e-14, rtol=0)
        for k, index in ((1, 400), (2, 800)):
            trace = self.result.transitions[k]
            np.testing.assert_array_equal(t.columns("Position E")[index], trace.e_rates[0])
            np.testing.assert_array_equal(t.columns("Readout V")[index], trace.v_rates[0])
            np.testing.assert_array_equal(t.columns("Gate G")[index], trace.g_rates[0])
            np.testing.assert_array_equal(t.columns("Shared M")[index], 0)

    def test_discontinuous_records_are_rejected(self):
        traces = list(self.result.transitions)
        changed = traces[1].v_rates.copy()
        changed[0, 0] += .1
        traces[1] = replace(traces[1], v_rates=changed)
        with self.assertRaisesRegex(ValueError, "Discontinuous"):
            build_timeline(replace(self.result, transitions=tuple(traces)))

    def test_stale_output_labels_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "labels"):
            build_timeline(replace(self.result, positions=(1, 2, 3, 4)))

    def test_npz_roundtrip_preserves_every_rate_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timeline.npz"
            self.timeline.save(path)
            with np.load(path, allow_pickle=False) as data:
                loaded = RateTimeline(**dict(data))
            np.testing.assert_array_equal(loaded.rates, self.timeline.rates)
            np.testing.assert_array_equal(loaded.labels, self.timeline.labels)


if __name__ == "__main__":
    unittest.main()
