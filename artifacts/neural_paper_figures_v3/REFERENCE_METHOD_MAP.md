# Reference method map

This is a METHOD ADAPTED analysis of a fixed handcrafted LDS E/I model. It is not source-exact reproduction. Paper2Skill packages source evidence; Codex experts separately audited methods, adapters and actual output PNGs.

- [Inagaki/Mante/Gallego/Sussillo source contracts and four-round review](reports/REFERENCE_METHOD_MAP_INAGAKI.md).
- [Zhou source contract](reports/REFERENCE_METHOD_MAP_ZHOU.md).
- [Inagaki actual Figure8 review](reports/literature_inagaki/round04_figure_review.md).
- [Zhou actual Figure9 review](reports/literature_zhou/round04_actual_figure_review.md).

Inagaki uses coding directions and independent experimental trials; LDS uses actual 132-state rates and endpoint PCA, no animal repeats. Gallego Fig3c across/within VAF ratio is not identical to the archived target-variance-capture fraction. Mante third-party notebook is not author code. Sussillo fixed-point concepts are adapted to the existing NumPy bounded-rate integrator; no TensorFlow/PyTorch migration. Zhou Fig7 uses trained-network ensembles and different external timing; LDS control-only PCA is an explicit choice because the source fit set is unknown. Source-exact author-code execution remains BLOCKED by missing source data/checkpoints/analysis components, independently of successful LDS adaptation.
