# 本项目流线相图调整

目标：A、核实参考图坐标和流线方法；B、用真实项目动力学绘制三编码论文式相图；C、完成数值/视觉复审、归档及提交提案。

## 方法与执行

已核实截图来自Saighi/Rozenberg2025 Figure2，而不是Inagaki或Zhou目标图。来源专家实际查看原图、PDF与Methods，合同及证据见source目录。LDS采用率状态平面、共同B/dual、每条件实际积分背景、固定sample-off/tonic/clock；不用训练阶段假标签。

新评价与绘图模块独占由root实现；来源专家独占source审稿；fresh phase_reviewer独占reviewer。没有并发改同文件。测试实现前真实失败ModuleNotFoundError，4项判据实现后通过；完整回归74/74通过。原始红测试失败为模块不存在，并非伪造机制bug。保护源码由原hash核对，正常model/task/simulation/config未修改。

统一命令已实际执行：`python -m handcrafted_ei.visualization.plot_all --phase-portraits`，输出artifacts/phase_portraits_v2，不覆盖历史图。

## 数值事实

3编码×3条件×5041格全部合法，未clip；common dual在非正交合成基底测试通过。独立full field/全108条轨迹均通过；36/71网格共点field相同。dt2.5仅为独立refinement核验，正式dt5不改，全部终点身份保持，瞬态率差最高.0537已披露。

主图显式给出noninvariant、场平面外比例中位数37.3/37.3/55.3%和最大真实轨迹离面量.206/.206/.436。filled numbered anchor只代表fullfield stationarity，不以投影点宣称稳定吸引子。前两列相同以及共同活动1+2是实际结果，不能为了像原图隐藏。

## 验收追踪

| 内容 | 证据 | 状态 |
| --- | --- | --- |
| 来源/方案 | source/METHOD_CONTRACT.md、SOURCE_EVIDENCE.json | 方法适配通过 |
| 实际数值 | source/independent_plane_check.py/json、reviewer/recompute.py/json | 独立复算通过 |
| 回归 | tests_full.txt | 74/74通过 |
| 正式图 | 新归档主图/补图，各PNG300dpi/SVG/PDF | 6组18文件完整性QA通过；实际6PNG最终视觉复核通过 |
| Source reverse fidelity | source/FINAL_FIDELITY_REVIEW.md、round4_1_final.json | PASS_WITH_LIMITS；两项图面问题修复后已实际重开 |
| Fresh independent review | reviewer/REVIEW.md、independent_checks.json | PASS_WITH_LIMITS；108全状态轨迹、9源码/41产物/每编码8受保护源码hash通过 |
| 提交 | Nimbalyst commit proposal及Git readback | 提交只经交互工具，不推送 |
