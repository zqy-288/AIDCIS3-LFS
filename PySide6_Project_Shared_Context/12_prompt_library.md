# 提示库

本文件为与 Gemini 等 AI 助手交互提供了一个提示库，专门针对“管孔检测系统”项目。使用这些提示可以帮助 AI 更快地理解上下文并生成更相关的代码或建议。

## 1. 代码生成

### 添加新的 UI 功能

**提示**:
"""
在 `main_window.py` 中，我想在“工具”菜单下添加一个新的菜单项，名为“数据导出”。当用户点击这个菜单项时，弹出一个 `QFileDialog` 让用户选择保存路径，然后将 `H001` 孔的测量数据从数据库中导出为 CSV 文件。请实现 `export_data` 方法，并将其连接到新的菜单项。
"""

### 添加新的数据库查询

**提示**:
"""
在 `modules/models.py` 的 `DatabaseManager` 类中，添加一个名为 `get_all_workpieces` 的新方法。这个方法应该查询数据库并返回所有工件的列表，每个工件以字典形式包含 `workpiece_id` 和 `name`。请确保包含必要的 session 管理。
"""

## 2. 代码理解与解释

### 解释特定文件

**提示**:
"""
请解释 `modules/main_detection_view.py` 文件的主要功能。它是如何绘制孔洞布局的？它又是如何处理用户点击事件的？
"""

### 解释特定函数

**提示**:
"""
在 `modules/realtime_chart.py` 中，`update_data` 函数的具体作用是什么？它是如何与 `pyqtgraph` 交互来更新图表的？
"""

## 3. 重构

### 重构 UI 组件

**提示**:
"""
目前，`realtime_chart.py` 中的所有 UI 元素都是在 `__init__` 方法中创建的。请将 UI 创建部分重构到一个名为 `setup_ui` 的新方法中，以遵循项目编码规范。同时，将信号连接部分重构到 `setup_connections` 方法中。
"""

### 优化数据库查询

**提示**:
"""
`modules/models.py` 中的 `get_hole_measurements` 方法目前返回一个字典列表。请修改它，使其直接返回 `Measurement` 对象的列表。调用者将负责处理对象。同时，请评估此查询的性能，并说明是否有优化的空间。
"""

## 4. 调试

### 调试 UI 问题

**提示**:
"""
当我在“主检测视图”中点击一个孔时，应用程序有时会卡顿。请分析 `main_detection_view.py` 和 `main_window.py` 中与 `navigate_to_realtime` 信号相关的代码，找出可能导致 UI 阻塞的原因，并提出修复建议。
"""

### 调试数据问题

**提示**:
"""
我发现保存到数据库中的 `diameter` 值有时会不准确。请检查 `modules/worker_thread.py`（或当前的数据导入逻辑）和 `modules/models.py` 中的 `add_measurement_data` 方法，追踪数据从生成到存储的整个流程，以识别潜在的计算或类型转换错误。
"""

## 5. 文档

### 生成函数文档

**提示**:
"""
请为 `modules/history_viewer.py` 文件中的 `load_history_data` 方法生成符合 PEP 257 规范的 Python 文档字符串（docstring），包括对其功能、参数和返回值的描述。
"""
