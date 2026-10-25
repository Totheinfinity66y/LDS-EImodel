# 精读任务规范（单篇论文）

本文件是本仓库使用 `jzks-pdf-viewer` 技能进行单篇论文精读的作业规范。所有精读任务必须先读本文件，再读技能参考文档，最后按本文件规定的路径与格式产出。

## 必读文档

1. 技能主文件：`.agents/skills/jzks-pdf-viewer/SKILL.md`
2. 五步精读过程要求：`.agents/skills/jzks-pdf-viewer/references/deep-reading.md`
3. 卡片结构定义：`.agents/skills/jzks-pdf-viewer/references/card-schema.md`
4. 五步提示词：`.agents/skills/jzks-pdf-viewer/references/five-steps.md`

`references/deep-reading.md` 与 `references/card-schema.md` 必须在动笔前完整读一遍，两者对质量的要求具有约束力。

## 输入

- PDF：`artifacts/papers/<目录>/<ID>.pdf`
- 带页码标记的纯文本：`artifacts/papers/<目录>/text.txt`
  该文件每页以 `===== PDF PAGE N =====` 开头，N 是物理页码，与 PDF 页序号一致（从 1 开始）。**所有引句必须来自此文件，且引句所在页必须与 `annotations[].page` 一致。**

## 产出（每个论文目录内）

1. `evidence-conclusions.md`：写正文前的证据账本。至少包含：
   - 实际读过的范围（哪些章节、哪些图表、哪些页）
   - 已接触作者结论的说明（本仓库已存在同主题文献清单和部分论文摘要，因此一律按“证据复核”处理，不得称为盲读）
   - 支撑关键判断的直接证据（带物理页码）
   - 未能核实的部分与原因
   - 已检查但本任务未实施的补充材料、数据、代码
2. `reading.json`：符合 `card-schema.md` 的五步卡片，schema 必须为 `jzks-pdf-viewer/v1`。

## reading.json 硬性要求

- `paper`：`title`、`authors`、`doi`（`doi` 可为空字符串）。
- `summary`：一段连贯的中文概括，说明研究对象、机制主张与证据强度，不是关键词清单。
- `steps`：恰好 5 个，`id` 为 1—5，`title` 依次为
  `作者想解决什么问题`、`用了什么方法`、`得到了什么结果`、`结果能否支持结论`、`有哪些局限与启发`。
- 每个 step 至少 2 个 `paragraphs`；每个 paragraph 含 `title`、`text`、`layer`、`refs`。
  - `layer` 取 `author` 或 `analysis`。作者明确报告的内容用 `author`，AI 的推断、检验建议与替代解释用 `analysis`。
  - `refs` 是本篇 `annotations` 中存在的 ID 数组，每段至少 1 个。
  - 正文必须解释事实、为什么重要以及必要边界，不能只列结论。
- `annotations`：至少 10 条。
  - 字段：`id`（形如 `E01`，全局唯一）、`step`（1—5）、`page`（物理页码）、`title`、`kind`、`quote`、`explanation`、`layer`。
  - `kind` 取 `background` / `method` / `result` / `question` / `implication`。
  - `quote` 是**原文的实际短引句**，逐字来自 `text.txt`，长度足够在目标页唯一定位（归一化后不少于 12 个字符）。不得使用中文翻译、改写或概括代替原文。
  - `explanation` 为中文解释，说明这条证据支持什么判断。
  - `layer` 取 `author` 或 `analysis`；引用作者结论的证据标 `author`，由原文推断出的解读标 `analysis`。

## 五个步骤各自必须回答的内容

1. **问题与全局地图**：研究类型、对象、输入输出、主要比较、2—3 个关键图表；作者声称的知识缺口（已有方法做到什么、剩下什么、本文新增什么）；可检验的预测，并写明什么结果会削弱该解释。区分作者陈述与 AI 还原。
2. **方法是否回答了问题**：先解释关键方法原理与作用，再按研究类型（计算模拟 / 实验 / 综述 / 理论）检查影响结论的环节。要点明关键假设与信息缺口，区分“本文未报告”“设计风险”“分析风险”“无法判断”。没有执行代码或实验时不得写成已复现。
3. **结果先还原再解释**：核心结果带比较对象、指标含义与方向、数值与单位、条件、已报告的不确定性；说明关键图表在回答什么。未报告区间不能写成没有效果；不从低清曲线估精确值；区分相关与因果。
4. **对照两套结论**：逐项比较作者主张与直接证据，给出可支持的表述与差异类型（一致 / 作者更强 / 更弱 / 范围不同 / 证据不足）。数值冲突并列保留。指出最强证据与最薄弱连接，同时解释论文贡献，不能只挑错。
5. **替代解释与使用决定**：给 1—3 条与论文直接相关的替代解释，每条写明机制、预期现象、区分检验、当前证据是否排除。分清作者未来工作与 AI 检验建议；说明哪些发现适合引用或借鉴、最关键的待补材料。

## 引句校验（必须执行）

写完 `reading.json` 后运行：

```powershell
C:\Users\Totheinfinity\.conda\envs\pymol_env\python.exe tools\check_quotes.py artifacts\papers\<目录>\<ID>.pdf artifacts\papers\<目录>\reading.json
```

必须做到 **全部引句 `matched`**，即在该页唯一命中。出现 `not_found`（引句与该页文本不符，多半是页码写错或引句抄错）、`ambiguous`（该页出现多次，换更长或更独特的引句）、`quote_too_short`（引句太短）时，修改后重跑，直到没有 problems。

允许的改动只有两种：改正页码，或替换引句。**禁止**为了让定位通过而填写与解读无关的引句。

## 写作风格

- 正文用中文，术语首次出现时给出英文原词，例如“去抑制（disinhibition）”。
- 不夸大因果与适用范围，不把综述结论当作实验证据。
- 关键数字回到原表原图核对，不使用工具生成的摘要替代原文。
- 作者未报告的信息写“本文未报告”，并说明已查范围。
- 每个 paragraph 是一个有主题的完整论述，不是短句堆叠。

## 交付前自检

1. `check_quotes.py` 全部 `matched`。
2. 5 个 step 齐备，每步至少 2 段，每段 `refs` 非空且 ID 都存在。
3. `annotations` 至少 10 条，ID 唯一。
4. `summary` 为连贯概括而非清单。
5. 五步内容互相衔接：步骤 3 还原的结果在步骤 4 被逐项对照，步骤 4 的差异在步骤 5 被用作限制或检验依据。
