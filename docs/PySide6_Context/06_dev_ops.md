# 开发者指南 (DevOps)

**最后更新时间: 2025-07-07**

本文档为开发者提供参与本项目所需的环境配置、工作流程和编码规范。

## 1. 环境设置

### 1.1. 先决条件

*   **Python**: 版本 3.8 或更高。
*   **Git**: 用于版本控制。

### 1.2. 步骤

1.  **克隆仓库**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **创建虚拟环境**

    为了保持项目依赖的隔离，强烈建议使用虚拟环境。

    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖**

    使用 `requirements.txt` 文件安装所有必需的库。

    ```bash
    pip install -r requirements.txt
    ```

## 2. 启动与调试

### 2.1. 运行应用程序

直接执行 `main.py` 即可启动整个应用程序。

```bash
python main.py
```

程序启动时，会自动检查根目录下是否存在 `detection_system.db`。如果不存在，它将自动创建该数据库文件并填充一些初始的样本数据，方便开发和测试。

### 2.2. 独立运行模块

为了方便调试，部分UI模块被设计为可以独立运行。你可以直接执行对应的Python文件来单独查看和测试该模块的UI。

例如，要单独测试 `MainWindow`:

```bash
python main_window.py
```

或者测试 `RealtimeChart`:

```bash
python modules/realtime_chart.py
```

**注意**: 独立运行时，模块可能无法访问完整的应用上下文（如数据库连接），但对于纯UI的调试非常有用。

## 3. 代码风格与规范

*   **编码**: 所有 `.py` 文件应使用 `UTF-8` 编码。
*   **格式化**: 遵循 **PEP 8** 代码风格指南。建议使用 `autopep8` 或 `black` 等工具进行自动格式化。
*   **命名**: 
    *   类名使用 `CamelCase` (例如 `MainWindow`, `WorkerThread`)。
    *   函数和变量名使用 `snake_case` (例如 `setup_ui`, `worker_thread`)。
    *   常量使用 `UPPER_SNAKE_CASE` (例如 `DATABASE_URL`)。
*   **文档字符串**: 关键的模块、类和函数应包含文档字符串（Docstrings），解释其用途、参数和返回值。
*   **类型提示**: 鼓励在函数签名中使用Python的类型提示，以提高代码的可读性和健壮性。

    ```python
    def get_holes_by_workpiece(self, workpiece_id: int) -> list[Hole]:
        # ...
    ```

## 4. 数据库管理

*   数据库的结构由 `modules/models.py` 中的 `SQLAlchemy` 模型定义。任何对数据结构的修改都应在此文件中进行。
*   **不要**手动修改 `detection_system.db` 文件，除非是为了测试目的。如需重置数据库，直接删除该文件并重启应用即可重新生成。
