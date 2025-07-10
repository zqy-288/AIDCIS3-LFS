# 编码规范

本文件定义了“管孔检测系统”项目的编码规范，旨在确保代码的一致性、可读性和可维护性。

## 1. Python 编码风格

- **PEP 8**: 所有 Python 代码应遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范。
- **命名约定**:
    - `模块`: `lower_case_with_underscores.py` (例如: `main_window.py`, `realtime_chart.py`)
    - `类名`: `CamelCase` (例如: `MainWindow`, `WorkerThread`)
    - `函数/方法`: `lower_case_with_underscores()` (例如: `setup_ui`, `start_measurement`)
    - `变量`: `lower_case_with_underscores` (例如: `main_layout`, `worker_thread`)
    - `常量`: `UPPER_CASE_WITH_UNDERSCORES` (例如: `DATABASE_URL`)
- **文档字符串**:
    - 所有模块、类和函数都应包含文档字符串（docstrings）。
    - 文档字符串应使用三重双引号 `"""Docstring goes here"""`。
    - 文档字符串应简要说明其功能、参数和返回值。
- **类型提示**:
    - 强烈建议在函数签名中使用类型提示，以提高代码清晰度和健壮性。
    - 示例: `def get_hole_measurements(self, hole_id: str) -> list[dict]:`
- **Imports**:
    - `import` 语句应分组，顺序如下:
        1. 标准库
        2. 第三方库
        3. 本地应用程序/库特定导入
    - 每个 `import` 语句应在单独的行上。

## 2. PySide6 (Qt) 编码风格

- **UI 和逻辑分离**:
    - UI 定义（布局、控件创建）应在 `setup_ui` 方法中完成。
    - 信号和槽的连接应在 `setup_connections` 方法中完成。
    - 业务逻辑应在单独的方法中实现，而不是直接在 UI 事件处理器中。
- **命名约定**:
    - 控件变量名应清晰地反映其类型和功能，例如 `self.start_button`, `self.history_tab`。
- **父子关系**:
    - 创建 `QWidget` 或 `QObject` 时，应尽可能指定父对象，以确保正确的内存管理。

## 3. 数据库 (SQLAlchemy)

- **模型定义**:
    - 模型类应在 `modules/models.py` 中统一定义。
    - 表名应为复数形式，例如 `workpieces`, `holes`。
- **会话管理**:
    - 使用 `DatabaseManager` 类来获取和关闭数据库会话。
    - 避免在应用程序代码中直接创建 `engine` 或 `session`。
    - 使用 `try...finally` 块确保会话在使用后被关闭。

## 4. 文件和目录结构

- **模块化**:
    - 功能代码应按模块组织在 `modules` 目录下。
    - 硬件相关的代码应放在 `hardware` 目录下。
    - 文档应放在 `docs` 目录下。
- **`__init__.py`**:
    - `modules` 和 `hardware` 目录应包含 `__init__.py` 文件，以使其成为 Python 包。

## 5. 版本控制 (Git)

- **提交信息**:
    - 提交信息应清晰、简洁，并描述所做的更改。
- **分支**:
    - 新功能开发应在单独的分支中进行。
    - `main` 分支应保持稳定。

## 6. 文档

- **README.md**:
    - 项目根目录下的 `README.md` 应提供项目的概述、安装说明和使用指南。
- **`docs` 目录**:
    - `docs` 目录用于存放更详细的文档，如设计文档、API 参考等。
