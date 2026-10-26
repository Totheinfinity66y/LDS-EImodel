# 三编码神经群体分析总结

结论：三种外部编码经过相同固定E/I网络后，在读出期趋向相同的六位置Response表征。分支分离主要由handcrafted坐标支持决定；当前Response六位置等距。完整网络中微小环排序来自共享Y的读出尾迹。所测离散状态有局部固定点稳定与小扰动恢复证据，没有连续环吸引子证据。

## 十个研究问题

1. **招募哪些群体？** 三编码均依次招募R1→R2→R3→R4的一个活动分支，并伴随规则memory、兴奋gate、tonic/decay/竞争/退役I和共享Y。132维全网络没有删去静息单元。

2. **局部化来源？** 六单元branch支持直接写入固定连接；结构/功能并列和support-folded近1重合表明主要是handcrafted branch specialization。共享群体参与不等于新涌现分区。

3. **Response subspace？** 可辨认，但它是既定坐标中实际活动的事后统计；不支持自发正交的说法。全网络共享成分使角度小于90°。

4. **有效维数？** 当前Response各branch位置rank=5、PR≈5；全网络R1 rank7/PR≈5.55，R2各branch rank6/PR≈4.73，R3/R4各branch rank5/PR≈5。每个精确值及dim90/95在metrics/<encoding>/subspace_geometry.csv；不能把1/2/4/4分支数当rank。

5. **D/S交接？** M_D到R2、M_S到R3的规则条件差异在交接后保留于Response，memory经I_decay反馈终止；反馈阻断保留memory，原有必要性与继承测试限制因果解释。它不是信息守恒量估计。

6. **六位置邻接？** 当前Response没有邻近更相似的几何，非对角距离常数，rho=NA、tie-corrected邻居分数0.4。全网络R2–R4高rank相关对应约0.014%–0.024%相对距离差，来自共享Y尾迹，不能称为强内部圆环。

7. **三编码几何差异？** 输入原始维数不同且one_hot早期sample轨迹不同，ring/topology干净电流等价。读出期Response几何趋同，不能声称三种不同内部流形。

8. **哪些状态稳定？** 72个快照覆盖D=+1,S=1、六L、四阶段、三编码；撤sample/clock后保留tonic的自主端点及固定clock端点具有低残差与rho<1。小RMS .02有效目标全部身份保留恢复，较大扰动常跳转或失败。

9. **吸引子证据？** 有所测离散状态的局部稳定固定点候选及有限盆证据；没有连续环或动态吸引轨迹证据。每编码观察到24个任务端点加3个随机初态端点；不能声称穷尽全部盆。clip拐点局部导数有局限，结论不扩展为全局证明。

10. **结构与动力学？** 分支数量/支持和固定位置变换属于先验。撤输入保持、门控形成、反馈终止、饱和后编码趋同、有限扰动恢复/跳转是实际积分观察。Y尾迹造成微弱环距离效应值得注意，但不是Response连续流形。

## 原始数值与入口

[逐图结果](RESULTS.md) · [方法](METHODS.md) · [数据审计](DATA_AUDIT.md) · [参考图核对](FIGURE_REFERENCES.md) · [定量指标](metrics/encoding_summary.csv)

相对one_hot全轨迹max绝对差（包括sample）为：{'one_hot': 0.0, 'ring': 0.006046570572147303, 'topology': 0.006046570572147303}。三编码不使用同一缓存冒充；每个录制包保留独立来源ZIP哈希。

完整局部动力学原始NPZ保留本地，输出hash在data/dynamics/summary.json；论文原图仅供本地核验，均不作为模型结果。测试和视觉验收见manifests，提交状态以Git读回为准。

## 信息交接的必要限定

独立噪声seed测试在readout2的R2/D和readout3的R3/S为1.0，同时M_D/D和M_S/S仍为1.0；残余小活动不等于信息被擦除。严格留出任务组合的baseline probe在相关时刻仅机会水平。因此问题5的“交接”指Response已可承载规则并能继承路由，同时memory活动经反馈衰减；不表示规则信息在memory中彻底消失，也不表示未见条件泛化。
