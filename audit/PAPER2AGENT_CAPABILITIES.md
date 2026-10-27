# Paper2Agent 能力实测审计

## 身份与调用

真实入口：`C:/Users/Totheinfinity/.codex/skills/paper2agent/SKILL.md`。本任务开始已实际读取；该文件无语义版本字段，不虚构版本号。组件包括 paper2skill、paper2mcp、paper2agent-paper、scripts。组件及脚本身份以本任务最终 manifest 的SHA256为准。

这是一套供 Codex 读取执行的工作流，不是一个名为 paper2agent 的自动科研CLI。文献输入走 `paper2skill/scripts/paper_bundle.py`；作者代码封装走 Paper2MCP 的实际源码执行、最小wrapper、独立验证与运行时验收。两位专家分别读取组件规则并保持独立工作区。

| 能力 | 实测与边界 |
| --- | --- |
| PDF/本地论文 | 支持，真实运行 prepare/extract/review-aid/build/verify；两篇均有来源快照 |
| DOI/URL | 是定位来源的线索；须另取得真实PDF/代码，再交转换器，不是prepare的PDF替代物 |
| 补充材料/表格/图片 | Paper2Skill支持；每份实际输入必须逐页/逐资产审阅 |
| 作者代码仓库 | Paper2MCP支持Python/R/CLI，必须绑定现有实现；MATLAB需已有可用runtime |
| 执行论文算法 | Paper2Skill明确“不执行论文中的方法/代码”；Codex专家审查并执行真实作者入口或明确Methods重建 |
| Figure–Methods对应 | 阅读包保留可检索正文、图注和原图；科学映射由专家建立，不是自动保证 |
| 接受LDS本地数据/适配 | 不原生提供任意论文适配器；本次Codex专家给出契约，另写严格adapter和测试 |
| 反向审图 | 非Skill内置审核API；同一持久专家结合已构建阅读包、源码与实际数据进行Codex反向审阅，记录替代机制与局限 |
| 持久工作区 | 支持来源快照、review plans、验证JSON；本次另保存多轮communication请求响应 |
| MCP注册/安装 | 未请求全局注册，本任务不修改客户端；没有上游代码/运行时就不伪造同名MCP工具 |

## 已实际使用的命令族

以各论文目录执行日志和 `ORIGINAL_REPRODUCTION_REPORT.md` 中的**完整命令**为准：`paper_bundle.py prepare`、`extract`、`review-aid`、`build`、`verify --strict`。参数由真实 `--help` 和Skill文档核对。reviewed package须经过 `build --require-reviewed` 与严格验证，不以草稿机械完整冒充通过。

作者执行：Zhou未修改的 `task.py generate_trials` 实际生成输入，神经网络训练权重及Figure7扰动/绘图入口并未公开，不能据此声称运行了Figure7。Inagaki公开MATLAB脚本只覆盖ED1/ED9，缺MATLAB/Octave及部分绘图辅助依赖，作者模拟未实际运行。基于Methods重建的CD、phase-line和距离函数另标 reconstructed implementation。

## 环境与限制

已检查项目 `handcrafted_ei/requirements.txt`，analysis环境实际验证Python3.12.12/NumPy2.3.5/SciPy1.16.3/Matplotlib3.10.7/PyYAML6.0.3，CPU足够；当前进程加入对应Library/bin解决Conda DLL导入问题，未全局修改PATH。文献转换复用已存在paper2agent-test环境，由两专家保存版本与调用证据。缺失fontTools的字体提取警告按真实图像审核处理，不擅自安装。原作者缺失数据、模型权重、MATLAB运行时均保留阻塞，不下载替代论文、不伪造原实验重复。

Gate0的“工作流能力已核实”不代表Gate1原论文全部分析可精确复现，也不代表生成图已通过Gate4/5。
