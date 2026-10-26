# 改造前基线

source.zip保存HEAD对应的v1源码与基础规范；commit.txt标识祖先，git-status.txt记录原有未提交PPTX。tests.txt为本次运行的旧16测试，全部通过。新机制实现前的direct_red/decay_red/new_tests_red保留真实失败，包含缺少接口的错误及旧memory终末仍为1的行为失败。

远端origin/main只读核对为02c27dbd131ac274033d3b12712405d9663b9101，本地HEAD为937efdf（额外文档提交）。本次不推送、不覆盖历史v1归档。

attractor_red/subspace_red为分析实现前失败。扰动探测发现0.1 RMS不总恢复；正式实验保留所有幅度和阈值，不将局部恢复预设为科学通过条件。
