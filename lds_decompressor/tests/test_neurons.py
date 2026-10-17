"""Neuron state ownership, independent snapshots and faithful plotting."""

from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from lds_decompressor import (
    CompressedCode, ENeurons, INeurons, JNeurons, Neurons, RateDecompressor,
    VNeurons,
)
from lds_decompressor.timeline import SequenceTimeline


class NeuronOwnershipTests(unittest.TestCase):
    def test_subclasses_initialize_all_47_printable_rate_variables(self):
        model = RateDecompressor()
        for cls, neurons in ((ENeurons, model.e), (INeurons, model.i),
                             (INeurons, model.gate_i), (VNeurons, model.v),
                             (JNeurons, model.j)):
            self.assertIsInstance(neurons, cls)
            self.assertIsInstance(neurons, Neurons)
        self.assertTrue(all(isinstance(n, Neurons) for n in model.neurons.values()))
        self.assertEqual(len(set(model.unit_names)), 47)
        np.testing.assert_array_equal(model.rate_potentials, np.zeros(47))
        output = StringIO()
        print(dict(zip(model.unit_names, model.rate_potentials)), file=output)
        for name in model.unit_names:
            self.assertIn(name, output.getvalue())

    def test_neuron_states_and_histories_are_actual_transition_rates(self):
        model = RateDecompressor()
        initial = model.initialize(CompressedCode(1, 1, 2))
        np.testing.assert_array_equal(model.e.rates, initial.e_rates)
        self.assertEqual(model.i.rates[0], initial.i_rate)
        final, trace = model.advance(initial)
        np.testing.assert_array_equal(model.e.history, trace.e_rates)
        np.testing.assert_array_equal(model.i.history[:, 0], trace.i_rates)
        np.testing.assert_array_equal(model.relay.history.reshape(-1, 4, 6), trace.relay_rates)
        np.testing.assert_array_equal(model.v.rates, trace.readout.rates)
        np.testing.assert_array_equal(model.gate_i.rates, trace.gate_i_rates)
        np.testing.assert_array_equal(model.rate_potentials, trace.recording.rates[-1])
        np.testing.assert_array_equal(model.e.rates, final.e_rates)
        self.assertFalse(model.rate_potentials.flags.writeable)

    def test_model_recording_exactly_preserves_original_visualization(self):
        result = RateDecompressor().decompress(CompressedCode(1, 1, 2))
        recording = result.recording
        path = Path(__file__).parents[1] / "artifacts" / "sequence_timeline.npz"
        with np.load(path, allow_pickle=False) as saved:
            for key in ("time", "rates", "labels", "groups", "modes"):
                np.testing.assert_array_equal(getattr(recording, key), saved[key])
        self.assertEqual(recording.rates.shape, (1201, 47))
        self.assertGreater(recording.rates.max(), 1)
        self.assertIs(recording.rate_potentials, recording.rates)
        self.assertFalse(recording.rates.flags.writeable)

    def test_all_recorded_columns_match_each_original_source(self):
        model = RateDecompressor()
        result = model.decompress(CompressedCode(3, -1, 2))
        for trace in result.transitions:
            record = trace.recording
            def group(name):
                return record.rates[:, record.groups == name]
            np.testing.assert_array_equal(group("Position E"), trace.e_rates)
            np.testing.assert_array_equal(group("Global I")[:, 0], trace.i_rates)
            for path, name in enumerate(("CW1", "CW2", "CCW1", "CCW2")):
                np.testing.assert_array_equal(group(f"Relay {name}"), trace.relay_rates[:, path, :])
            for name, expected in (("Direction", result.initial_state.encoding.direction.rates),
                                   ("Step", result.initial_state.encoding.step.rates),
                                   ("Joint", result.initial_state.encoding.joint.rates),
                                   ("Displacement", trace.readout.rates),
                                   ("Gate I", trace.gate_i_rates)):
                np.testing.assert_array_equal(group(name), np.tile(expected, (len(record.time), 1)))

    def test_interleaved_calls_restore_supplied_state_and_do_not_mutate_recordings(self):
        model = RateDecompressor()
        initial = model.initialize(CompressedCode(3, -1, 2))
        state, first = model.advance(initial)
        saved = first.recording.rates.copy()
        expected = model.resume(state)
        model.decompress(CompressedCode(6, 1, 1))
        model.encode_tuning(1, 1)
        # Even edited inspection buffers cannot supply inference state.
        model.e.initialize(np.ones(6) * 9)
        model.i.initialize([7])
        actual = model.resume(state)
        np.testing.assert_array_equal(actual.recording.rates, expected.recording.rates)
        np.testing.assert_array_equal(first.recording.rates, saved)
        other = RateDecompressor()
        np.testing.assert_array_equal(other.rate_potentials, np.zeros(47))

    def test_plotter_reads_saved_values_without_activity_file_or_rate_generation(self):
        from lds_decompressor.sequence_plotting import plot_sequence_artifacts
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure

        result = RateDecompressor().decompress(CompressedCode(1, 1, 2))
        timeline = SequenceTimeline.from_recording(
            result.recording, [0, 0.8, 1.6, 2.4], result.positions, [1, 1, 2])
        # A changed stored sample must be plotted as-is, not regenerated.
        timeline = SequenceTimeline(timeline.time, timeline.rates.copy(), timeline.labels,
                                    timeline.groups, timeline.modes, timeline.rank_times,
                                    timeline.positions, timeline.condition)
        timeline.rates[17, 0] = 3.7
        with tempfile.TemporaryDirectory(prefix=".lds-plot-test-", dir=Path(__file__).parents[2]) as folder:
            folder = Path(folder)
            timeline.save(folder / "sequence_timeline.npz")
            original = (folder / "sequence_timeline.npz").read_bytes()
            try:
                with patch.object(Figure, "savefig"), patch.object(plt, "close"), \
                     patch.object(Neurons, "respond", side_effect=AssertionError("rate generation")), \
                     patch.object(SequenceTimeline, "save", side_effect=AssertionError("plot wrote rates")):
                    plotted = plot_sequence_artifacts(folder)
                    figures = [plt.figure(n) for n in plt.get_fignums()]
                    np.testing.assert_array_equal(figures[-2].axes[0].lines[0].get_ydata(), timeline.rates[:, 0])
                    np.testing.assert_array_equal(figures[-1].axes[0].collections[0].get_array(), timeline.rates.T)
                np.testing.assert_array_equal(plotted.rates, timeline.rates)
                self.assertEqual((folder / "sequence_timeline.npz").read_bytes(), original)
                self.assertFalse((folder / "activities.npz").exists())
            finally:
                plt.close("all")


if __name__ == "__main__":
    unittest.main()
