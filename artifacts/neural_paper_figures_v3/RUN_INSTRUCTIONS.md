# Run instructions

Run in repository root with the existing `analysis` Conda environment. No installation is needed. These PowerShell variables affect only the current process:

```powershell
$env:PATH='C:/Users/Totheinfinity/.conda/envs/analysis;C:/Users/Totheinfinity/.conda/envs/analysis/Library/bin;C:/Users/Totheinfinity/.conda/envs/analysis/Scripts;'+$env:PATH
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$analysisPython='C:/Users/Totheinfinity/.conda/envs/analysis/python.exe'
& $analysisPython -m handcrafted_ei.evaluation.paper_v3_dynamics --grid-size 21
& $analysisPython -m handcrafted_ei.visualization.paper_v3
& $analysisPython -m unittest discover -s handcrafted_ei/tests -v
& $analysisPython artifacts/neural_paper_figures_v3/reports/independent_check.py
& $analysisPython -m handcrafted_ei.visualization.paper_v3_reports
```

The default renderer verifies and copies reusable Figure1/2/3/6/7/10 exports and derived data from the local v1 manifest; it never infers curves from PNGs. To independently rebuild all figures without relying on that figure archive, use:

```powershell
& $analysisPython -m handcrafted_ei.evaluation.paper_v3_dynamics --output artifacts/neural_paper_figures_v3_rebuild
& $analysisPython -m handcrafted_ei.visualization.paper_v3 --rebuild-reused --output artifacts/neural_paper_figures_v3_rebuild
```

These commands use the formal raw ZIP archive for existing ablation/noise assays and comparison calculations. They do not change the baseline model. V3 geometry reads standardized recordings and verified metrics; v3 dynamics requires existing reference fixed_points/basin/input NPZs. Missing inputs raise explicit errors. See data_inventory.json for exact keys, availability and hashes. Rebuilding original reference arrays when absent requires the full reference-grounded pipeline and its own evidence gates, not a PNG adapter. The default commands were executed for this delivery; the slower complete-rebuild branch is exposed for reproducibility and was not redundantly rerun.

Large stage-perturbation/comparison NPZs stay local and are SHA-indexed. Baseline ZIPs and original literature materials must remain locally available. The code/data contract does not promise source-exact paper reproduction.
