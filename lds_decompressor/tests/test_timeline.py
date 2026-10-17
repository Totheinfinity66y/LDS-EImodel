"""Check that presentation preserves recorded rates and boundary semantics."""

from pathlib import Path
import unittest

import numpy as np

from lds_decompressor.timeline import RateRecording, build_sequence_timeline


class SequenceTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / "artifacts" / "activities.npz"
        with np.load(path, allow_pickle=False) as data:
            cls.recorded = {key: data[key].copy() for key in data.files}

    def test_every_rate_unit_is_present_and_unscaled(self):
        line = build_sequence_timeline(self.recorded)
        self.assertEqual(line.rates.shape, (1201, 47))
        self.assertEqual(len(set(line.labels)), 47)
        self.assertEqual(np.count_nonzero(line.modes == "integrated"), 31)
        self.assertEqual(np.count_nonzero(line.modes == "held"), 16)
        np.testing.assert_array_equal(line.positions, [1, 2, 4, 5])
        np.testing.assert_array_equal(line.condition, [1, 1, 2])
        np.testing.assert_array_equal(line.columns("Position E")[:400], self.recorded["example_e"][0, :-1])
        self.assertGreater(line.columns("Position E").max(), 1)
        self.assertTrue(np.all(np.diff(line.time) > 0))
        self.assertAlmostEqual(line.time[-1], 2.4)

    def test_rank_switch_keeps_ei_and_resets_relays_using_actual_samples(self):
        line = build_sequence_timeline(self.recorded)
        for rank in range(3):
            index = rank * 400
            self.assertAlmostEqual(line.time[index], rank * 0.8)
            np.testing.assert_array_equal(line.columns("Position E")[index], self.recorded["example_e"][rank, 0])
            self.assertEqual(line.columns("Global I")[index, 0], self.recorded["example_i"][rank, 0])
            for path, name in enumerate(("CW1", "CW2", "CCW1", "CCW2")):
                np.testing.assert_array_equal(line.columns(f"Relay {name}")[index],
                                              self.recorded["example_relays"][rank, 0, path])
        np.testing.assert_array_equal(line.columns("Position E")[-1], self.recorded["example_e"][-1, -1])
        np.testing.assert_array_equal(line.columns("Relay CW1")[-1], self.recorded["example_relays"][-1, -1, 0])

    def test_control_snapshots_are_held_not_interpolated(self):
        line = build_sequence_timeline(self.recorded)
        for rank in range(3):
            block = slice(rank * 400, (rank + 1) * 400)
            for group, key in (("Displacement", "displacement_rates"), ("Gate I", "gate_i_rates")):
                expected = self.recorded[key][1, rank]
                np.testing.assert_array_equal(line.columns(group)[block], np.tile(expected, (400, 1)))
        for group, key in (("Direction", "direction_rates"), ("Step", "step_rates"), ("Joint", "joint_rates")):
            np.testing.assert_array_equal(line.columns(group), np.tile(self.recorded[key][1], (1201, 1)))

    def test_raw_control_rates_are_not_normalized_for_display(self):
        data = self.recorded.copy()
        data["gate_i_rates"] = data["gate_i_rates"].copy()
        data["gate_i_rates"][1, 0, 2] = 2.7
        line = build_sequence_timeline(data)
        self.assertEqual(line.columns("Gate I")[0, 2], 2.7)

    def test_discontinuous_recording_is_rejected(self):
        data = self.recorded.copy()
        data["example_e"] = data["example_e"].copy()
        data["example_e"][1, 0, 0] += 0.1
        with self.assertRaises(ValueError):
            build_sequence_timeline(data)

    def test_stale_decoding_labels_are_rejected(self):
        data = self.recorded.copy()
        data["positions"] = data["positions"].copy()
        data["positions"][1, -1] = 6
        with self.assertRaises(ValueError):
            build_sequence_timeline(data)


class RecordingBoundaryTests(unittest.TestCase):
    def record(self, time=(0, 1), rates=((1, 0), (2, 3)), labels=("E1", "R")):
        return RateRecording(time, rates, labels,
                             ("Position E", "Relay CW1"), ("integrated",) * 2)

    def test_boundary_uses_next_control_and_relay_sample(self):
        a = self.record()
        b = self.record(rates=((2, 0), (4, 5)))
        joined = RateRecording.concatenate((a, b))
        np.testing.assert_array_equal(joined.time, [0, 1, 2])
        np.testing.assert_array_equal(joined.rates, [[1, 0], [2, 0], [4, 5]])
        self.assertFalse(joined.rates.flags.writeable)

    def test_model_recording_rejects_discontinuous_ei_and_nonlocal_time(self):
        a = self.record()
        for b in (self.record(rates=((9, 0), (4, 5))),
                  self.record(time=(1, 2), rates=((2, 0), (4, 5))),
                  self.record(time=(0,), rates=((2, 0),))):
            with self.subTest(time=b.time), self.assertRaises(ValueError):
                RateRecording.concatenate((a, b))
        # The same continuity requirement applies to global inhibition.
        a = RateRecording([0, 1], [[0], [1]], ["I_global"], ["Global I"], ["integrated"])
        with self.assertRaises(ValueError):
            RateRecording.concatenate((a, a))

    def test_incompatible_metadata_and_invalid_rates_fail_before_join(self):
        a = self.record()
        b = self.record(rates=((2, 0), (4, 5)), labels=("E2", "R"))
        with self.assertRaises(ValueError):
            RateRecording.concatenate((a, b))
        for time, rates in (((0, 0), ((1, 0), (2, 3))),
                            ((0, 1), ((1, 0), (-2, 3))),
                            ((0, 1), ((1, 0), (np.nan, 3)))):
            with self.subTest(time=time, rates=rates), self.assertRaises(ValueError):
                self.record(time=time, rates=rates)

    def test_legacy_import_and_model_recordings_are_identical(self):
        from lds_decompressor import CompressedCode, RateDecompressor

        result = RateDecompressor().decompress(CompressedCode(1, 1, 2))
        path = Path(__file__).parents[1] / "artifacts" / "activities.npz"
        with np.load(path, allow_pickle=False) as data:
            line = build_sequence_timeline(data)
        for key in ("time", "rates", "labels", "groups", "modes"):
            np.testing.assert_array_equal(getattr(result.recording, key), getattr(line, key))
        samples = {name: neurons.rates for name, neurons in RateDecompressor().neurons.items()}
        with self.assertRaises(ValueError):  # Integrated groups need sampled histories.
            RateRecording.from_groups([0, 1], samples)
        samples.pop("Joint")
        with self.assertRaises(ValueError):
            RateRecording.from_groups([0, 1], samples)


if __name__ == "__main__":
    unittest.main()
