"""Real multi-format export and source/NA contract regression checks."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from handcrafted_ei.visualization.style import configure,panels,save_figure
from handcrafted_ei.visualization.quality_check import check
from handcrafted_ei.evaluation.population_activity import save_rows
from handcrafted_ei.evaluation.population_data import load_dataset,source_identity


class PopulationFigureTests(unittest.TestCase):
    def test_three_formats_including_3d_panel_and_integrity(self):
        import matplotlib.pyplot as plt
        configure()
        with tempfile.TemporaryDirectory() as p:
            root=Path(p); fig=plt.figure(figsize=(5,4),layout='constrained'); ax=fig.add_subplot(projection='3d')
            t=np.linspace(0,4*np.pi,120); ax.plot(np.cos(t),np.sin(t),t); panels([ax]); ax.set(xlabel='x',ylabel='y',zlabel='t')
            paths=save_figure(fig,root/'figures/one_hot','synthetic_math_export')
            self.assertEqual({Path(x).suffix for x in paths},{'.png','.svg','.pdf'})
            manifest={'figures':[{'id':'synthetic_math_export','encoding':'one_hot','paths':paths,'output_sha256':{x:sha256(Path(x).read_bytes()).hexdigest() for x in paths}}]}
            (root/'figure_manifest.json').write_text(json.dumps(manifest))
            self.assertEqual(len(check(root)),1)
            Path(paths[0]).write_bytes(b'broken')
            with self.assertRaises(ValueError): check(root)

    def test_nonfinite_csv_is_explicit_NA(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/'metric.csv'; save_rows(path,[{'value':np.nan,'condition':'degenerate'},{'value':1.,'condition':'defined'}])
            with path.open() as f: rows=list(csv.DictReader(f))
            self.assertEqual(rows[0]['value'],'NA'); self.assertEqual(rows[1]['value'],'1.0')

    def test_protected_source_matches_archived_dynamics(self):
        root=Path(__file__).parents[1]/'artifacts/v2/run'
        if not root.exists(): self.skipTest('research archive is optional for package distribution')
        identity=source_identity(root)
        self.assertTrue(identity); self.assertTrue(all(x['matches'] for x in identity.values()))

    def test_corrupted_archive_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as p:
            path=Path(p); (path/'ring__baseline.zip').write_bytes(b'not a scientific archive')
            (path/'archives.json').write_text(json.dumps({'ring__baseline.zip':'0'*64}))
            with self.assertRaisesRegex(ValueError,'checksum'): load_dataset(path,'ring')


if __name__=='__main__': unittest.main()
