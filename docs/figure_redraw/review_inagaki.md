# Inagaki 来源与 Figure 3 / 8 本轮复审

日期：2026-10-28。来源专家角色：`/root/fig01_03`。独占本文件。

本角色实现了 Figure 1–3，因此 Figure 3 的以下检查属于作者自检与来源语义复审，**不能作为未参与实现的独立 G5 验收**。Figure 8 由另一实现者编写，本角色只读代码并实际看图。未运行作者 MATLAB，未下载或执行原始实验多 session 数据，也未重新构建阅读包。

## 1. 原数据契约

实际读取强制技能 `C:/Users/Totheinfinity/.codex/skills/paper2agent/SKILL.md`；本轮沿用已有本地来源包，不猜测 Paper2Agent API。读取 `audit/paper2agent/inagaki/INPUT_CONTRACT.json`、`FIGURE_CONTRACT.json`、`REFERENCE_METHODS.md`、`FINAL_FIDELITY_REVIEW.md`、`source_manifest.json`、`source_text.txt` 及 `communication/round1.json`。

原论文题名为 *Discrete attractor dynamics underlies persistent activity in the frontal cortex*，Inagaki、Fontolan、Romani、Svoboda，DOI `10.1038/s41586-019-0919-7`。题名与 DOI 本轮由本地原文文字直接核对。实际打开来源包的 `assets/figure/figure-5.jpg`：a 是单细胞 spike raster/PSTH 与光抑制，b–d 是 CD 轨迹和中段/终段分布，e 是多条件轨迹叠加，f 是含 shuffle 的 phase line，g 是 session 内配对差异。原图颜色含 right/left、perturbed correct/error，以及绿色中段和紫色终段抽样语义。

本轮直接读取原文 CD analysis：实验 100 ms 平滑窗、10 ms 步长，最后 600 ms 的 right-minus-left 均值差取单位向量；固定 2 s delay 使用 50% control correct trials 拟合与另一半投影，交换 folds；随机 delay 使用非 2 s trials 拟合、2 s trials 测试；session 内 endpoint 规范化后汇总。phase line 使用 delay 最后 1200 ms，中心差分与 0.2 AU 分箱；原实验具有真实 trials/sessions 和层级 bootstrap。

历史四轮咨询记录位于 `audit/paper2agent/inagaki/communication/round1.json`、`round2.json`、`round3.json`、`round4*.json`。它们是历史证据，本文件四节**不是四次新的独立专家咨询**。历史 strict build、完整逐页审阅与数值证书不冒充本轮重跑。

## 2. LDS 兼容性

| 项目 | 判定 | 原因 |
| --- | --- | --- |
| 真实 132 维活动与条件身份 | PASS | Figure 1–3 REC 与 ZIP 逐元素匹配；三种编码分别验证原 ZIP 和受保护源码 SHA256。 |
| 规则均值差投影 | ADAPT | Figure 3 使用完整 24 条件平衡均值，固定 delay-end / Response-readout anchor；是描述性规则轴，不是原实验 CD 泛化估计。 |
| 多 session/动物统计 | INCOMPATIBLE | 每编码仅一条确定性轨迹/条件；未制造 SEM、bootstrap 或生物学重复。 |
| 原 Fig5 数值/作者代码 | BLOCKED | 本轮未执行作者 MATLAB 或原实验数据；没有 source-exact 成功声明。 |
| 六位置固定点与有限方向恢复 | ADAPT | Figure 8 为固定同一 D/S 下六个端点的全状态残差、局部谱/折点证书与 state-kick；原 Fig5 不直接包含这些诊断。 |
| 六位置的完整全局吸引盆 | 未建立 | 特定二维 affine slice 不能等同完整 132 维 basin；有限方向比例不能给全局概率。 |

## 3. Adapter 与数值自检

只读检查 `artifacts/paper2agent_reproduction/reproduced_papers/inagaki/source_methods.py`：CD 是均值差单位向量，phase-line 是中心差分后显式换算到每 10 ms，空 bin 保留 NaN。此为 Methods reconstruction，不等于执行作者代码。

只读检查 `handcrafted_ei/evaluation/figure_data_dynamics.py` 与 `visualization/paper_figures_dynamics.py`：F8 每 branch 按 D/S 选六个实际条件；PCA 由同一六个完整端点拟合；B 使用真实 `basin_full.npz` 积分路径；恢复按全状态恢复且保持身份；二维 slice 使用合法率状态 mask、不 clip，完整方程积分后按全状态残差及 max norm 分类。显示投影不承担 basin 分类。

F1–3 本轮执行独立表达式自检：三编码 REC 身份均通过；R2–R4 branch 峰值由逐分支循环重算，与新 NPZ 全数组逐元素相同；R1 competitor / margin 全 NaN；九份 manifest 所列输出和两个分析源码 SHA256 全通过。R1 没有竞争者，CSV 写 NA，图中不绘制假 competitor=0。

F3 复用实际 baseline、lesion_feedback_D/S、随机反馈控制 seed 7/11/19，并保存正常 R2/R3 曲线；干预幅度、符号、时窗、边数由原 lesion 记录保留。另保存 A/B/C/D 交接前后输出切断与随机对照的逐 stage 和完整序列准确率。低幅度 memory 可读出与否和幅度下降分开解释。

## 4. 实际图反向审阅

### F1–3：三编码共九 PNG

本轮实际通过 `view_image` 打开最终 `fig01/02/03_one_hot.png`、`fig01/02/03_ring.png`、`fig01/02/03_topology.png`，包括标题增加编码身份、R1 NA 修复后的最终版本。三编码没有缓存串用：分别校验输入档案，图题明确编码。图像无空白、坐标裁切或缺图；图例和线型可读。

- F1：四 panel 实际率轨迹、gate/memory/feedback、固定位置单元跨六 L 和 E/I active fraction / total rate。率为无量纲；时间标记由记录事件读取。多条静息曲线重合是实际结果。
- F2：四个 R3 branch 的六单元 tuning 小倍图可分辨，替换了起初重叠的时间曲线；D panel 的 R1 只画 selected，其他阶段显示实际 paired selected/competitor 点，不伪称独立重复。
- F3：局部 D/S 交接曲线、固定规则轴、反馈切断/随机对照及严格 condition-held-out probe 分开；不把 memory 幅度下降写成信息消失。第六格是解释边界，不是新数据。

### F8：one-hot 四 branch 与切片补图

实际打开 `fig08_one_hot_branch0.png`（主图）、branch1/2/3（补图）及 `fig08_one_hot_basin_slices.png`。

- 每幅五 panel 的 branch 身份、六个 L、全 132 维残差与三固定方向恢复语义清楚。没有人为把六点摆成规则六边形，也没有连接六点声称连续环。
- 残差图 log 轴保留实际量级，谱图提供连续最大实部及 Euler 谱半径；已通知集成者要求图注明确 clip kink 时采用的代表性斜率和 piecewise-cascade 证书责任，不能以唯一经典 Jacobian 解释折点。这项图注要求尚待集成者读回确认。
- 切片补图四 branch 均显示 144 个合法初态，其余 mask；实际看到合法区域均为 `other_equilibrium (-1)`，而非六目标固定点的彩色 basin。此为有信息的阴性结果：预指定切片没有进入六目标盆，不能声称已画出六目标的完整吸引盆，更不能为了出现彩色盆修改动力学。
- 这些图是 LDS 方法适配、附加数值诊断，不能冒充原 Fig5 的实验 CD、光抑制、层级 bootstrap 或作者模型复现。

F8 本次视觉核对的 branch0 PNG SHA256：`754d5359192474c3b84e2372d6fcd673290057123d956c6191c0869dae9cff4c`。如后续 renderer 或文件变更，必须重新打开更新版并记录身份。

裁决：来源方法语义 **PASS_WITH_LIMITS / METHOD_ADAPTED**；source-exact 复现 **BLOCKED**；F1–3 九图数据/渲染自检通过；F8 已审 one-hot 版本，其他编码须由最终集成审阅确认。本角色不替代项目最终 G5 验收。

## 5. 最终双切片与折点标注追加复审

本节追加于最终 renderer 冻结后；上文 six-mean 切片阴性结果和第一次审阅 SHA256 保留，不以新增切片覆写。

本轮再次实际打开最终 `fig08_one_hot_branch0.png`，确认 B 已称 real full-state-kick trajectories（不预先保证都回原点），D 明确显示 `Representative kink slope 0.5 + certificate`，且仍有 `6/6 piecewise-cascade certificates` 和 kink 个数。原折点标注要求已落实。最终该 PNG SHA256 为 `dcbacada11630449e080cd0c1c1bad50bf78a8a16bbdf396f03c3d2a6b34b5f9`。

进一步实际打开三编码共六幅最终双切片补图：每编码的 `fig08_<encoding>_sixmean_control_slices.png` 与 `fig08_<encoding>_three_endpoint_slices.png`，四 D/S branch 分开，非法区域 mask 与其他平衡态分类明确。未见空白、裁切或把阴性区域隐藏的情况。两种切片名称明确区分，未把新增 plane 当作原 plane 的新结果。

读回三编码全部四 branch、两种切片共 24 个 NPZ 的 `classification` / `legal_mask` / 实际积分轨迹数量：

| 初态切片 | 每 branch 合法点 | 分类读回 | 允许的结论 |
| --- | --- | --- | --- |
| sixmean control | 144 / 1681 | 144 全为其他平衡态，1537 非法；三编码和四 branch 均一致 | 原切片未显示目标固定点盆交集，阴性对照保留 |
| three endpoint | 551 / 1681 | 534 其他平衡态，17 匹配该 branch 的三个参考端点，1130 非法 | 此特定平面切到三个目标盆附近有限区域，不是六位置完整全局盆 |

three-endpoint 的 branch0 参考索引计数是 `0:6, 4:6, 8:5`；branch1 为 `1:6,5:6,9:5`；branch2 为 `2:6,6:6,10:5`；branch3 为 `3:6,7:6,11:5`。三编码一致。身份来自全 132 维匹配，不由二维颜色或投影距离反推。两 plane 的并列不能解释成恢复概率或独立实验重复。

最终 sixmean / three-endpoint 图的 SHA256（按此顺序）：

- one_hot：`d17c67e55cf624f1861befca06fbc194aaa9edb9d51415ba9b7d0bb89af04548` / `4b9afe360657e9c0b33a31862d032075fdebe0b87515ffda85b2f01eb85e7369`。
- ring：`1fc10ed649c95c453907e3bd2d3636b8da11e16f9ee7d2397fa35a8acf0f2a2f` / `0730bae10e4b4f3721165ede8be342bb6457eb3ccc73d4ea2c4522d85ef9d11f`。
- topology：`4790dd15e951f6f2b433302b6d283c3620cf6a10a80f03c3a72971c721d0e5d3` / `f772de809db2a6d099f295f0d977952d85b08d4678c3fb6a4fb865808fda52fa`。

追加裁决：**双切片语义与实际图 PASS_WITH_LIMITS**，局限是 plane 依赖、只覆盖三参考端点局部切片、其他平衡态占多数；不改变 source-exact BLOCKED，也不把有限平面扩张成全局 basin 证明。
