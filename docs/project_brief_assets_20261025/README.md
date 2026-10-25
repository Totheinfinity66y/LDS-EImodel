# 项目进展汇报配图与证据素材

本目录为项目汇报 PPT 提供逐页视觉素材、AI 生图提示词和原始结果凭据。配图采用暖白底、克制朱红、细线与留白的简约科学期刊风格；没有沿用旧版的植物／动物题材。

汇报成稿为仓库中的 `docs/项目进展简报_交大红色科学期刊风.pptx`，共 10 页。`build_student_brief.py` 是生成该演示文稿的脚本；配图和提示词规划留在本目录，便于复用和修改。

## 逐页图片

| 幻灯片 | 图片 | 用途与证据属性 |
| --- | --- | --- |
| 01 | `slide01_cover_v2.png` | 神经活动群组成的圆环与连续路径，封面概念图。 |
| 02 | `slide02_task_v2.png` | 六位置圆环和三段移动；位置编号与任务值须由 PPT 原生文字添加。 |
| 03 | `slide03_question_v2.png` | 输入、保持、选择、继承、读出的概念流。 |
| 04 | `slide04_network_v2.png` | 分阶段神经群体与共享读出概念图。 |
| 05 | `slide05_disinhibition_v2.png` | E 通路、抑制门与释放单元概念图。 |
| 06 | `slide06_inheritance_v2.png` | 活跃分支身份延续至后续响应的概念图。 |
| 07 | `v1_validation_trajectories.png` | 项目 v1 归档原始验证图；不是 AI 重绘。 |
| 08 | `slide08_interventions_v2.png` | 不同阶段因果切断位置的概念图；数据由 PPT 原生表格／图示呈现。 |
| 09 | `slide09_evidence_limits_v2.png` | 已检验机制与未检验脑尺度结论的证据边界图。 |
| 10 | `slide10_roadmap_v2.png` | 扰动、结构简化和自主时序三类后续方向的概念图。 |

AI 插画不含模型测量值，亦不代表真实神经结构或真实实验照片。准确标签、公式与数值均在 PPT 中以可编辑文字制作。

## 原始证据

- `v1_validation_trajectories.png`：来自 `handcrafted_ei/artifacts/v1/validation.png`。
- `v1_trajectory_recheck.json`：来自 `handcrafted_ei/artifacts/v1/verification.json`，归档 39 项实验、936 个 trial 的独立重算状态。
- 实验结果和解释边界：`handcrafted_ei/artifacts/v1/REPORT.md`。

## 生图与版面规划

- `prompt_plan_v2.md`：统一视觉规范、每页布局建议和图像生成提示词。
- 精确公式、标签、24/24、16/16、39/936 及干预结果不交给图像生成模型绘制，须从项目规格／结果档案原样写入幻灯片。
