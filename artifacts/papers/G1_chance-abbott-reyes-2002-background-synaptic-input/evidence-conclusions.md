# G1 证据与结论对照（Chance, Abbott & Reyes 2002）

## 1. 版本与材料范围

- PDF：`artifacts/papers/G1_chance-abbott-reyes-2002-background-synaptic-input/G1.pdf`，共 10 个物理页（期刊页 773–782），来源为 Columbia 作者机构 PDF（`https://columbia.edu/cu/neurotheory/Larry/ChanceNeuron02.pdf`），已通过 `tools/verify_papers.py` 与 `tools/dump_text.py` 校验，正文与图注均可提取文字。
- 实际读过的章节：Summary、Introduction（第1页）、Results 全部小节（Introducing In Vivo Synaptic Input into In Vitro Neurons；Multiplicative Gain Modulation of Neurons In Vitro；Contributions of Shunting and Noise to Gain Modulation；Effects of Background Input on Response Variability；Gain Modulation in a Model Neuron；第2–7页）、Discussion、Predictions、Conclusion（第8页）、Experimental Procedures（第8–9页）、Appendix（第9页）、References（第9–10页）。Figure 1–5 的图注全部读过。
- 附录的解析发放率表达式在第9页以文字形式给出，已读；但该式涉及的高斯／误差函数积分 f 的显式形式作者声明“不需要在本文讨论中写出”，因此本卡的定量复核只到 r ∝ xF(I/x) 与 gσV 的标度关系层面。
- **未获得**：Supplementary Information；本文未附带数据文件或模型代码。Figure 4 的解析模型参数在正文与 Experimental Procedures 中给出，但作者未提供可运行实现。
- **证据等级说明**：本任务属于“证据复核”，不是盲读。本仓库 `docs/gating_gain_modulation_paperlist_20261020.md` 已记录本文的结论摘要（“平衡增加背景兴奋与抑制输入可产生除性增益变化，而不只是提高平均放电”），且本文的引言、讨论与结论在本次阅读中先于结果被看到。故本卡不宣称结果盲读。

## 2. 作者明确报告的结论（来自 Summary、Discussion、Conclusion 与 Predictions）

1. 平衡地同时增加兴奋与抑制背景突触输入，会使神经元对兴奋性驱动（driving current）的增益下降，且这一下降不伴随信号无关的发放率升高或发放变异性的显著增加。
2. 机制可以分解：输入噪声（input noise）造成发放率曲线的斜率变化与左移，分流（shunting）造成右移；两者同时存在时左右位移相互抵消，留下纯粹的增益下降。
3. 分流单独不改变曲线斜率，只造成位移；因此“分流即可产生乘性增益调制”这一常见假设在多种神经元模型中并不成立。
4. 增益调制可以相当准确地表现为乘性缩放（Figure 2E），但需要分流幅度与噪声水平恰当匹配；不匹配时曲线会交叉而非收敛。
5. 背景输入对响应变异性的影响在本文条件下很小（CV 变化不显著，膜电位标准差变化 <30%），因此背景输入是增益的调制者而非变异性的来源。
6. 两条可检验签名：增益上升伴随背景输入与神经元电导下降；增益调制时膜电位波动方差与发放变异率不显著改变。
7. 皮层神经元在体内可能以“晶体管式”（transistor-like）方式工作：共变发放率的兴奋／抑制输入集合充当对推拉式驱动输入的增益控制信号。

## 3. 直接证据与主张的逐项核对

| 主张 | 直接证据 | 核对结果 |
| --- | --- | --- |
| 平衡增加背景输入降低增益 | 18 个神经元中 15 个在各水平下增益一致下降；1X→3X 增益下降超过 2 倍，且延伸至至少 100 Hz | 一致（Figure 2D、2A、2C） |
| 增益调制是乘性的 | Figure 2E 中经缩放后曲线对齐；0X/2X/3X 驱动电流按 2、0.65、0.45 缩放 | 一致，但作者自己给出反例 Figure 2F（部分神经元存在位移成分） |
| 分流造成位移而非斜率变化 | 32 nS 恒定附加电导、反转电位 −57 mV、无噪声，n=8：曲线右移，斜率不变 | 一致（Figure 3A） |
| 噪声造成斜率变化与左移 | 固定电导下增加噪声，n=6：低速率下抬升最大，随速率单调减弱 | 一致（Figure 3B） |
| 噪声与分流叠加得到纯增益下降 | Figure 3C 为 Figure 2A 的 1X 与 3X 重绘，无抬升而斜率下降 | 一致 |
| 背景输入不改变响应变异性 | 1X→3X（速率四倍）时 CV 无明显变化；亚阈值膜电位标准差变化 <30% | 一致（Figure 3E、3F） |
| 需要约 5 mV 膜电位波动才能覆盖宽速率范围 | 解析模型：σV=5 mV 时 0–200 Hz 全程有效；σV=2 mV 时 50 Hz 以上减弱 | 一致（Figure 4B、4C）；但此处是模型结果，真实神经元用更低噪声即可获得增益调制（作者自述） |
| 模型中缩放因子为 gσV，发放率形如 xF(I/x) | 附录解析式 | 一致（Appendix、第7页） |

## 4. 最强与最薄弱的连接

**最强**：机制被拆成两个可以独立操纵的成分（恒定电导无噪声 vs 固定电导加噪声），并构成近似 2×2 的条件矩阵（Figure 3A、3B、3C 与 Figure 2A 的组合）。这使“噪声还是分流”的争论变成可证伪的因子分解，而非各自举例。

**最薄弱**：
- 乘性缩放并非普遍成立。作者报告对一部分神经元改变速率因子会同时造成位移（Figure 2F），并明确说明没有去逐神经元调整兴奋／抑制配比来把它调成纯乘性（“we did not do this because we wanted to avoid fine tuning of parameters for each of the neurons studied”）。
- 网络层面的放大论断没有数据支撑：“as we have verified in model networks (results not shown)”，该模拟未在本文中给出。
- 体内证据是间接的。本文全部机制结论来自体外皮层切片；体内 5 mV 量级波动属引用他人测量，不是本文数据。
- 分流与噪声的配平假设强：结论依赖“抑制性输入近端、兴奋性输入可远端”的配置。作者自己说明若兴奋输入过远端而不能产生分流，则需要靠平衡比来补偿，这构成对机制适用条件的额外约束。
- 与 Doiron 等（2001）的差异未被消除：Doiron 的乘法效应仅出现在低速率，因为噪声只来自抑制性输入；本文的噪声以兴奋为主导。作者把差异归因于噪声来源而非矛盾，属解释而非实验排除。

## 5. 已记录但不属于本卡范围的事项

- 附录中 f 函数的显式形式未给出（作者声明不需写出），因此本卡未对解析式做逐项数值复算。
- Figure 4D 中“兴奋速率增加 1.3 倍、抑制速率增加 4 倍”的失衡条件，本文只报告曲线在约 35 Hz 处交叉，未报告对该条件做重复测量。
- 皮层反馈通路产生平衡抑制的讨论（第8页）是作者引用的其他工作，本文未做实验检验。
