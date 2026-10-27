# 局部稳定不动点绘图状态

## 需求及范围

A核对来源稳定点/鞍点语义；B以本项目动力学绘制不动点及真实扰动轨迹；C通过完整状态数值与独立审查验证。正常模型与历史结果不变。

## 已完成证据

- 来源：Janson与Marsden2017 Figure1，来源专家inagaki独占source目录，METHOD_CONTRACT.md及SOURCE_EVIDENCE.json。
- 数据：实际归档选活跃R3/对应I_decay_S；独立副本构造高态初猜并求完整平衡，不伪称archive终点。
- 数值：三个编码各含稳定静息、鞍点、稳定保持；完整残差≤1.32e−19/ms。折点采用共同三角广义斜率分类；非只凭中点谱。
- 绘图：artifacts/local_fixed_points_v2三编码各主图/谱及恢复补图，PNG300dpi/SVG/PDF、NPZ/CSV/config/provenance；6组完整性PASS。已实际打开全部六张，由独立审查员检查。补充蓝粗轨迹方向箭头、红双向朝鞍点箭头，移开Held注释。
- 回归：新增模块前ImportError红测试已实际运行；实现后三项新判据通过，全部77项通过tests.txt。
- 独立验收：reviewer/INDEPENDENT_REVIEW.md，PASS_WITH_LIMITS。原model.step复算全路径误差≤3.99e−12，54次扰动trace误差≤2.78e−17，最大恢复末距2.09e−7。
- 科学边界：METHOD ADAPTED；非源作者方程/代码复现，非两个位置吸引子，非全局盆；二维红稳定流形不等于完整稳定集合。

## 收尾状态

来源专家最终反审已返回：source/LDS_ADAPTATION_REVIEW.md与round3_4.json，PASS_WITH_LIMITS / METHOD ADAPTED。实际打开最终6图并独立复算全部10201网格点、完整根、DAG和蓝支Euler一致性，源图视觉语义通过；完整根残差≤2.78e−18，蓝支逐步一致性误差≤5.55e−17。末态距平衡的有限时间误差不冒称根残差。附加CSV/hash读取未完成已明确披露。

Git提交未完成。自动审批服务额度用尽导致最新只读Git检查未执行，属于review服务失败，不是安全拒绝。不绕过检查、不声称已提交。此前Git状态中PPTX为无关用户改动，必须排除。
