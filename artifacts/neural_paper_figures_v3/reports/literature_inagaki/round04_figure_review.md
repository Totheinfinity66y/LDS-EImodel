# 第四轮：Figure 8 反向忠实度审阅

专家 ID：`inagaki_v3`。范围：文献方法与实际图像反向核验，不代替另一独立验收员的数值 gate。

## 实际检查的文件

已实际打开 one_hot 主图 `fig08_one_hot_six_point_attractors_branch0.png`、one_hot 的 4 branch×3 初态截面补图、ring branch0 补图。原参考已实际打开 Inagaki Figure 5/ED1 及 Sussillo–Barak Figure 3；原图只作方法/语义参考，不作为 LDS 数据。

读取 `visualization/paper_v3.py` 的 Figure 8 renderer、`evaluation/paper_v3_dynamics.py` 的真实积分和分类、三编码 basin NPZ、one_hot 固定点证书 CSV。对应数组计数另存 `round04_array_counts.json`。

## Panel 与文献语义

| Panel | 实际检查 | 判定 |
|---|---|---|
| A | 同 branch 六真实端点，固定共同 PCA；两轴各约20%解释方差；未人为排正六边形或圆周连线 | PASS；40%二维投影不能表示完整几何，六端点的其余方向须由3D补图/完整距离补足 |
| B | 实际 basin_full 的完整132维积分轨迹在A同一基投影；起点cross可见；部分终点进入原点附近 | 数据真实；需区分原位置保持与R3失活，原始L颜色不是终态身份 |
| C | 完整系统初态仿射截面；非法域独立mask，R3-inactive已明确，不叫全网络rest | PASS_WITH_LIMITS；21×21有限截面非全局吸引域，三种位置三元组补图必需 |
| D | 完整132维max残差和1e-7/ms阈值，点远低于阈值 | PASS；不是只测PCA残差 |
| E | 连续最大实部及Euler谱半径；标题明确clip-kink证书另外提供 | PASS_WITH_LIMITS；经典Jacobian非唯一时稳定依据应引用piecewise证书 |
| F | 独立state-kick协议和6位置×3方向分母；不与50ms输入脉冲混合 | 数据可追溯；same-position endpoint判据不能不加说明叫完整状态恢复 |

## 独立数组检查与负结果

三编码各 2772 个合法网格点：216 single-position、2556 R3-inactive、0 multiple、0 outside、0 unconverged。三编码最大完整场残差均为 `4.1480625081171164e-10 /ms`。因此本次三截面没有发现多位置终态；不能写成发现混合吸引子，也不能由0样本排除其他初态中的混合稳定点。

多数混合初态丢失R3活动是必须保留的真实动力学结果。它不同于 Inagaki 原实验的双选择恢复/切换范式，也不同于 Sussillo–Barak 受训 flip-flop 多记忆间的鞍点转移。LDS 24个任务端点附近有局部稳定证书不等于恰好24个全局吸引子；本图没有寻找/标注鞍点，不应借参考论文的红线语义暗示已发现鞍点或分界流形。

## 必须解释的视觉语义与修订状态

1. B 原图终点沿用原始L色/marker，部分失活终点看起来像彩色位置稳态。已向主 Agent 要求标题/图注明确“kick relaxation；颜色表示起始L，部分终态R3-inactive”，或改失活终点marker。
2. F 的 `recover` 实现为完整场收敛后单位置且与原位置相同，没有直接要求全状态与参考的距离阈值。已要求改为 same-position endpoint 或在图注明确，与Figure9完整状态恢复分开。
3. 初态截面补图标题包含 `np.int64(...)`，已要求转为普通整数显示；这是排版问题。

## 修订后实际复审与最终裁决

已重新实际打开主图写盘时间 2026-10-28 09:02:30 的 one_hot PNG。B 标题明确 `True kick relaxation; colors = original L`，失活/其他终态采用黑空心圆，图内文字解释起点和终点符号；轨迹向R3失活状态的负结果可辨。F 使用同一 state-kick 分类CSV，明确 `full-state recovered` 与 `same position; state differs`，并分列位置切换、多位置、分支外、R3失活和未收敛；横轴改成实际 clipping 后 RMS。初审两项科学视觉语义均落实。

最终裁决：**METHOD ADAPTED / PASS_WITH_LIMITS（one_hot 主图实际复审通过）**。原论文方法的区别、有限截面和投影限制不消失；不授予作者代码精确执行或原实验数值复现PASS。图像及renderer身份绑定在 `consultations.json` 的第4.1轮。
