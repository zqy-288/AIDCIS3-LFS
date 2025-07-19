好的，这是一个非常棒的工程问题。将大型重构任务分解为可并行的子任务，是高效团队协作的关键。我们可以将您的 v2.1 架构设计文档作为“单一事实来源”，为多个 AI 编程助手生成一系列精确、有序、可并行执行的提示词。

### **执行总纲：并行重构策略**

我们将采用“波次”（Waves）的策略。同一波次内的任务是相互独立的，可以分配给不同的 AI 助手并行执行。完成一个波次的所有任务后，再进入下一个波次。

*   **人类协调员 (您的角色)**：您是项目经理，负责分发提示词、收集代码、将代码放置到正确的文件路径，并在每个波次结束后进行简单的整合与审查。
*   **AI 编程助手 (AI Assistant 1, 2, 3...)**：他们是程序员，严格按照您提供的提示词和设计文档生成代码骨架。

---

### **WAVE 1: 基础模型与核心组件的并行构建**

**目标**：创建所有不依赖于其他新组件的基础模块。这些是整个架构的基石。

**并行执行**：以下三个提示词可以 **同时** 分发给 **三个不同** 的 AI 编程助手。

---

#### **【提示词 1/3】-> AI 助手 1：创建数据模型与常量**

```
角色: 你是一位专业的 Python/PyQt 高级开发人员。

任务: 根据提供的架构设计文档，创建项目所需的核心数据模型、状态枚举和事件类型常量。

上下文:
--- START OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---
[在此处粘贴 v2.1 架构设计文档的全部内容]
--- END OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---

具体要求:
1.  **创建 `EventTypes` 类**:
    *   文件路径: `src/models/event_types.py`
    *   严格按照文档中 `EventTypes` 类的定义，包含所有指定的事件常量。

2.  **创建 `DetectionState` 枚举**:
    *   文件路径: `src/models/detection_state.py`
    *   严格按照文档中 `DetectionState` 类的定义，实现一个 `Enum`。

3.  **创建 `ApplicationModel` 类**:
    *   文件路径: `src/models/application_model.py`
    *   实现文档中定义的 `ApplicationModel` 类。
    *   确保它继承自 `QObject` 并定义了所有指定的 `Signal`。
    *   实现 `__init__` 方法和 `current_workpiece` 的 property。
    *   对于 `update_hole_data` 和 `get_detection_summary` 等方法，只需创建方法签名和文档字符串，方法体内可以使用 `pass` 或返回默认值，无需实现完整逻辑。
    *   确保从 `PyQt6.QtCore` 或 `PySide6.QtCore` 导入 `QObject` 和 `Signal`。
    *   在文件顶部导入 `DetectionState`。

输出: 请为这三个文件分别提供完整的、可直接复制的代码块。
```

---

#### **【提示词 2/3】-> AI 助手 2：创建并细化控制器（主检测视图部分）**

```
角色: 你是一位专业的 Python/PyQt 高级开发人员，擅长构建清晰的控制器。

任务: 根据提供的架构设计文档，为"主检测"选项卡创建所有细分的控制器，包括协调器。

上下文:
--- START OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---
[在此处粘贴 v2.1 架构设计文档的全部内容]
--- END OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---

具体要求:
1.  **为以下四个控制器创建代码骨架**：
    *   `DXFViewController` (路径: `src/controllers/dxf_view_controller.py`)
    *   `SidebarController` (路径: `src/controllers/sidebar_controller.py`)
    *   `ViewportController` (路径: `src/controllers/viewport_controller.py`)
    *   `DetectionController` (路径: `src/controllers/detection_controller.py`)

2.  **对每个控制器**:
    *   实现文档中定义的类结构、`__init__` 方法和所有指定的局部 `Signal`。
    *   `__init__` 方法的参数应为 `(self, parent, model: ApplicationModel, event_bus: EventBus)`。
    *   创建所有在文档中提到的方法（如 `setup_ui`, `load_dxf_file` 等），但方法体内只需使用 `pass` 或添加注释说明其功能。重点是搭建好类结构和接口。
    *   假设所有依赖（如 `ApplicationModel`, `EventBus`, `DXFParser`）都可以在相应的路径下被正确导入。

3.  **创建 `MainDetectionCoordinator`**:
    *   文件路径: `src/controllers/main_detection_coordinator.py`
    *   实现文档中定义的协调器类。
    *   在 `__init__` 方法中，实例化上面创建的四个子控制器。
    *   实现 `setup_coordination` 方法，并在其中编写事件订阅的逻辑 (`self.event_bus.subscribe(...)`)。

输出: 请为这五个控制器文件分别提供完整的、可直接复制的代码块。
```

---

#### **【提示词 3/3】-> AI 助手 3：创建其他视图的控制器与UI管理器**

```
角色: 你是一位专业的 Python/PyQt 高级开发人员。

任务: 根据提供的架构设计文档，创建除"主检测"外的其他选项卡控制器，以及UI状态管理器和选项卡管理器。

上下文:
--- START OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---
[在此处粘贴 v2.1 架构设计文档的全部内容]
--- END OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---

具体要求:
1.  **创建以下控制器类的代码骨架**:
    *   `RealtimeController` (路径: `src/controllers/realtime_controller.py`)
    *   `HistoryController` (路径: `src/controllers/history_controller.py`)
    *   `ReportController` (路径: `src/controllers/report_controller.py`)
    *   对于每个控制器，创建 `__init__` 方法和 `setup_ui` 方法骨架，方法体内使用 `pass`。

2.  **创建 `TabManager` 类**:
    *   文件路径: `src/ui/tab_manager.py`
    *   实现文档中定义的 `TabManager` 类。
    *   创建 `__init__`, `create_tabs`, `switch_tab` 等方法的骨架。

3.  **创建 `UIStateManager` 类**:
    *   文件路径: `src/managers/ui_state_manager.py`
    *   实现文档中定义的 `UIStateManager` 类。
    *   创建 `__init__`, `save_window_state`, `restore_window_state` 等方法的骨架。

输出: 请为这五个文件分别提供完整的、可直接复制的代码块。
```

---

### **WAVE 2: 最终集成**

**目标**：在所有基础组件和控制器都生成完毕后，对最终的 `main_window.py` 进行重构，将所有新模块组装起来。

**执行**：此任务**必须在 WAVE 1 的所有代码都已生成并放置到正确位置后**才能执行。可以将其交给任意一个空闲的 AI 助手。

---

#### **【提示词 4/1】-> 任意 AI 助手：重构并集成 MainWindow**

```
角色: 你是一位专业的 Python/PyQt 架构师，负责将各个独立的组件集成为一个功能完整的应用程序。

任务: 根据提供的架构设计文档，重构 `src/main_window.py` 文件，使其职责简化，并负责初始化和协调所有新创建的控制器和模型。

重要前提: 假设 WAVE 1 中所有文件 (所有模型、所有控制器、TabManager, UIStateManager) 均已按照设计文档创建完毕并放置在正确的路径下。

上下文:
--- START OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---
[在此处粘贴 v2.1 架构设计文档的全部内容]
--- END OF FILE MAIN_WINDOW_REFACTORING_DESIGN.md ---

具体要求:
1.  **重构 `MainWindow` 类**:
    *   文件路径: `src/main_window.py`
    *   完全替换旧的 `MainWindow` 实现，采用文档中 "简化后的主窗口" 部分的设计。
    *   在 `__init__` 方法中，实例化 `ApplicationModel`, `EventBus`, `UIStateManager`, `TabManager` 以及所有顶层控制器/协调器 (`MainDetectionCoordinator`, `RealtimeController` 等)。
    *   **关键**: 不要在此文件中重新实现任何业务逻辑。它的职责是“组装”。

2.  **实现初始化与连接方法**:
    *   创建 `setup_ui`, `setup_global_connections`, 和 `setup_event_subscriptions` 方法的骨架。
    *   在 `setup_global_connections` 中，添加文档示例中的 `dxf_loaded` 信号连接。
    *   在 `setup_event_subscriptions` 中，添加文档示例中的事件订阅。

3.  **实现事件处理器**:
    *   创建 `on_dxf_loaded` 和 `on_navigate_to_tab` 方法，并根据文档实现其逻辑（如更新窗口标题和状态栏）。

4.  **导入所有必要的模块**:
    *   在文件顶部，添上所有需要用到的新模块的 `import` 语句。

输出: 请提供重构后的、完整的 `src/main_window.py` 文件代码。
```

### **如何执行**

1.  **启动 WAVE 1**: 将【提示词 1/3】, 【提示词 2/3】, 【提示词 3/3】分别复制到三个不同的 AI 助手聊天会话中，让它们同时开始工作。
2.  **收集 WAVE 1 成果**: 当三个助手分别返回代码后，您作为“人类协调员”，将这些代码片段创建到本地项目中对应的文件和路径下。
3.  **启动 WAVE 2**: 确认 WAVE 1 的所有文件都已就位后，将【提示词 4/1】复制给任意一个 AI 助手。
4.  **最终整合**: 收集 AI 助手返回的重构后的 `main_window.py` 代码，并用它替换您项目中的旧文件。
5.  **审查与迭代**: 至此，整个项目的代码骨架已按新架构重构完毕。您可以开始进行审查，并逐步向各个方法的 `pass` 中填充具体的业务逻辑和 UI 代码。