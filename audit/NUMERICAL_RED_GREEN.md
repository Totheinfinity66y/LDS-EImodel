# 新数值契约的红绿证据

测试实现前已实际运行 `python -m unittest handcrafted_ei.tests.test_reference_dynamics -v`：

1. 数值模块尚不存在时，真实失败为 `ModuleNotFoundError: No module named 'handcrafted_ei.evaluation.reference_dynamics'`，exit1。
2. 四项首次实现后的测试全部通过，包含Pythagorean恒等式、五类合成轨迹、phase单位和输入脉冲不等于状态跳变。
3. 新增分段稳定性负例后、函数实现前再次真实失败为 `ImportError: cannot import name 'piecewise_cascade_certificate'`，exit1；实现后完整70项回归全部通过。

这是本会话工具输出的观察记录，并非另造一次stdout。适配器更完整的red/green原始日志见 `audit/data/tests_red.txt` 与 `tests_green.txt`。全回归原始输出在 `audit/tests_full.txt`。独立D/A/F审计另外直接重算真实数组，未将“导入成功”视为科学验收。
