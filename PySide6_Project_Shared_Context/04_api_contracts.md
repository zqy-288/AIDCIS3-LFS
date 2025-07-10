# API文档 (API Contracts)

**最后更新时间: 2025-07-07**

本文档提供了对项目中关键类和模块的API说明，旨在帮助开发者理解其功能和使用方法。

## 1. `main_window.MainWindow`

**文件**: `main_window.py`

**描述**: 应用程序的主窗口，作为所有UI组件的容器。

### 主要方法

*   `__init__(self)`: 构造函数，初始化UI、菜单栏、状态栏和信号连接。
*   `setup_ui(self)`: 设置主窗口的布局，创建并添加 `QTabWidget` 和各个功能视图（`MainDetectionView`, `RealtimeChart` 等）。
*   `setup_menu(self)`: 初始化顶部的菜单栏（文件、工具、帮助）。
*   `setup_status_bar(self)`: 初始化底部的状态栏。
*   `setup_connections(self)`: 连接子视图发出的信号到对应的槽函数。
*   `navigate_to_realtime(self, hole_id)`: [SLOT] 切换到“实时监控”选项卡。
*   `navigate_to_history(self, hole_id)`: [SLOT] 切换到“历史数据”选项卡。

---

## 2. `modules.realtime_chart.RealtimeChart`

**文件**: `realtime_chart.py`

**描述**: 实时监控视图，负责显示动态图表和处理数据导入。

### 主要方法

*   `__init__(self)`: 初始化UI组件，包括 `pyqtgraph` 图表和控制按钮。
*   `setup_charts(self)`: 配置 `pyqtgraph` 图表的样式和数据系列。
*   `update_data(self, data)`: [SLOT] 接收来自 `WorkerThread` 的新数据并更新图表。
*   `import_csv_data(self)`: [SLOT] 响应“导入CSV”按钮点击事件，打开文件对话框并处理CSV数据。
*   `set_current_hole(self, hole_id)`: 设置当前正在检测的孔ID。

---

## 3. `modules.history_viewer.HistoryViewer`

**文件**: `history_viewer.py`

**描述**: 历史数据查看器，用于查询和展示存储在数据库中的检测数据。

### 主要方法

*   `__init__(self)`: 初始化UI，包括用于查询的输入框、按钮和显示结果的表格或图表。
*   `load_workpieces(self)`: 从数据库加载所有工件信息并填充到下拉列表中。
*   `load_holes_for_workpiece(self, workpiece_id)`: 根据选定的工件ID，加载其对应的所有孔信息。
*   `load_measurement_data(self)`: 根据用户选择的条件，从数据库查询测量数据并显示。

---

## 4. `modules.worker_thread.WorkerThread`

**文件**: `worker_thread.py`

**描述**: 后台工作线程，用于执行耗时的数据采集任务，防止UI阻塞。

### 信号 (Signals)

*   `data_updated(data)`: 当获取到新数据时发射此信号。`data` 是一个包含新数据点的字典或列表。
*   `status_updated(status_message)`: 当测量状态发生变化时发射此信号。
*   `finished()`: 任务完成时发射。

### 主要方法

*   `run(self)`: `QThread` 的主执行函数。循环调用硬件控制器获取数据，并通过信号发送出去。
*   `start_measurement(self, hole_id)`: 开始测量过程。
*   `stop_measurement(self)`: 停止测量过程。

---

## 5. `modules.models.DBManager`

**文件**: `models.py`

**描述**: 数据库管理器，封装了所有与数据库交互的操作。

### 主要方法

*   `__init__(self, db_url)`: 初始化数据库连接。
*   `create_sample_data(self)`: 创建数据库表并插入一些用于演示的样本数据。
*   `get_all_workpieces(self)`: 查询并返回所有的工件记录。
*   `get_holes_by_workpiece(self, workpiece_id)`: 根据工件ID查询其所有的孔记录。
*   `add_measurement(self, hole_id, data)`: 向数据库中添加一条新的测量记录。

---

## 6. `hardware.CR1500_controller.CR1500Controller`

**文件**: `CR1500_controller.py`

**描述**: 模拟的硬件控制器，用于生成测试数据。

### 主要方法

*   `connect(self)`: 模拟连接到硬件设备。
*   `disconnect(self)`: 模拟断开与硬件的连接。
*   `get_data(self)`: 生成并返回一条模拟的测量数据。
