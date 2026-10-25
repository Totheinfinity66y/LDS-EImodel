# Neuronal Arithmetic 精读与批注交付

对象：R. Angus Silver, “Neuronal arithmetic,” *Nature Reviews Neuroscience* 11 (2010), 474–489. DOI: 10.1038/nrn2864。

## 文件

- `Neuronal_arithmetic_2010.pdf`：本次提供的 16 页原文 PDF。
- `evidence-conclusions.md`：五步写作前建立的证据账本，记录来源范围、直接报告及边界。
- `reading.json`：五步精读结构化源数据。
- `reader/index.html`：离线自包含阅读器，可直接在浏览器打开，无需联网服务。
- `reader/paper-card.md`：可复制的五步精读正文。
- `reader/annotated-paper.pdf`：保留原页并附原文高亮、中文批注边栏的 PDF。
- `reader/evidence-index.json`、`reader/annotation-map.json`：主张—证据映射和高亮坐标。
- `reader/build-report.json`：生成与定位验证结果。

## 本地构建与验证

使用 `C:\Users\Totheinfinity\.conda\envs\pymol_env\python.exe`（Python 3.13.13、PyMuPDF 1.28.2）运行项目技能 `.agents/skills/jzks-pdf-viewer/scripts/build_viewer.py`。16 页输入、17 条原文批注均成功唯一定位；`build-report.json` 中未定位项为 0。阅读器、精读卡、映射文件、报告及批注 PDF 均已生成。

精读注明本任务在此前已见过摘要/结论和相关文献清单，因此按“证据复核”而非盲读处理。PDF 物理页 1–13 为正文（期刊页 474–486），14–16 为参考文献；Supplementary Information S1 未随附件提供。本文是机制综述，没有在本任务中复现被引用实验或 Figure 6 模型。

