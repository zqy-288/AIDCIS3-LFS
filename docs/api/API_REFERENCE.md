# AIDCIS3-LFS API 参考文档

![API](https://img.shields.io/badge/API-reference-blue)
![MVVM](https://img.shields.io/badge/pattern-MVVM-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

> 📚 **完整的API参考文档** - MVVM架构下的所有公共接口和使用方法

## 📋 文档概述

本文档提供AIDCIS3-LFS系统重构后的完整API参考，包括所有公共接口、类、方法和使用示例。文档按照MVVM架构层次组织，便于开发者快速查找和使用。

## 🏗️ 架构层次

```
┌─────────────────────────────────────────┐
│              Coordinator Layer          │
│           (协调器层)                     │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│                View Layer               │
│              (视图层)                   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│             ViewModel Layer             │
│            (视图模型层)                  │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│             Business Layer              │
│             (业务逻辑层)                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              Service Layer              │
│              (服务层)                   │
└─────────────────────────────────────────┘
```

---

## 🎯 协调器层 API

### MainWindowCoordinator

主窗口协调器，负责协调各个组件之间的交互。

#### 类定义

```python
class MainWindowCoordinator(QObject):
    """主窗口协调器 - 协调各个组件"""
```

#### 构造函数

```python
def __init__(self, data_service: Optional[IDataService] = None) -> None:
    """
    初始化主窗口协调器
    
    Args:
        data_service: 可选的数据服务实例
    """
```

#### 公共方法

##### show()

```python
def show(self) -> None:
    """显示主窗口"""
```

**示例**:
```python
coordinator = MainWindowCoordinator()
coordinator.show()
```

##### hide()

```python
def hide(self) -> None:
    """隐藏主窗口"""
```

##### close()

```python
def close(self) -> None:
    """关闭应用并清理资源"""
```

#### 属性

##### view_controller

```python
@property
def view_controller(self) -> MainViewController:
    """获取视图控制器实例"""
```

##### business_controller

```python
@property
def business_controller(self) -> MainBusinessController:
    """获取业务控制器实例"""
```

#### 使用示例

```python
from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator

# 创建协调器
coordinator = MainWindowCoordinator()

# 显示主窗口
coordinator.show()

# 访问子组件
view = coordinator.view_controller
business = coordinator.business_controller

# 关闭应用
coordinator.close()
```

---

## 🖥️ 视图层 API

### MainViewController

主视图控制器，负责UI的展示和用户交互。

#### 类定义

```python
class MainViewController(QMainWindow):
    """主视图控制器 - 专注UI展示和用户交互"""
```

#### 信号

##### user_action

```python
user_action = Signal(str, dict)
```

**描述**: 用户动作信号，当用户执行操作时发出

**参数**:
- `str`: 动作类型
- `dict`: 动作参数

**示例**:
```python
def on_user_action(action: str, params: dict):
    print(f"用户执行了动作: {action}, 参数: {params}")

view_controller.user_action.connect(on_user_action)
```

#### 公共方法

##### setup_ui()

```python
def setup_ui(self) -> None:
    """设置UI布局"""
```

##### update_display()

```python
def update_display(self, view_model: MainViewModel) -> None:
    """
    根据ViewModel更新UI显示
    
    Args:
        view_model: 主视图模型实例
    """
```

**示例**:
```python
view_model = MainViewModel()
view_model.detection_running = True
view_controller.update_display(view_model)
```

##### show_message()

```python
def show_message(self, message: str, level: str) -> None:
    """
    显示消息
    
    Args:
        message: 消息内容
        level: 消息级别 ('info', 'warning', 'error')
    """
```

**示例**:
```python
view_controller.show_message("检测完成", "info")
view_controller.show_message("文件加载失败", "error")
```

##### set_loading_state()

```python
def set_loading_state(self, loading: bool) -> None:
    """
    设置加载状态
    
    Args:
        loading: 是否处于加载状态
    """
```

#### 组件属性

##### toolbar

```python
@property
def toolbar(self) -> ToolbarComponent:
    """获取工具栏组件"""
```

##### info_panel

```python
@property
def info_panel(self) -> InfoPanelComponent:
    """获取信息面板组件"""
```

##### visualization_panel

```python
@property
def visualization_panel(self) -> VisualizationPanelComponent:
    """获取可视化面板组件"""
```

##### operations_panel

```python
@property
def operations_panel(self) -> OperationsPanelComponent:
    """获取操作面板组件"""
```

### UI组件 API

#### ToolbarComponent

工具栏组件，提供主要操作按钮。

```python
class ToolbarComponent(QToolBar):
    """工具栏组件"""
    
    action_triggered = Signal(str, dict)  # 动作触发信号
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """根据ViewModel更新显示"""
    
    def set_loading(self, loading: bool) -> None:
        """设置加载状态"""
```

**支持的动作**:
- `load_dxf_file`: 加载DXF文件
- `start_detection`: 开始检测
- `stop_detection`: 停止检测
- `switch_view`: 切换视图模式

#### InfoPanelComponent

信息面板组件，显示文件和检测信息。

```python
class InfoPanelComponent(QWidget):
    """信息面板组件"""
    
    action_triggered = Signal(str, dict)
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """更新显示信息"""
    
    def update_file_info(self, file_info: Dict[str, Any]) -> None:
        """更新文件信息"""
    
    def update_status_summary(self, summary: Dict[str, int]) -> None:
        """更新状态摘要"""
```

#### VisualizationPanelComponent

可视化面板组件，显示检测结果和图形。

```python
class VisualizationPanelComponent(QWidget):
    """可视化面板组件"""
    
    action_triggered = Signal(str, dict)
    hole_selected = Signal(str)  # 孔位选择信号
    sector_changed = Signal(str)  # 扇区切换信号
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """更新可视化显示"""
    
    def render_hole_collection(self, hole_collection: Any) -> None:
        """渲染孔位集合"""
    
    def highlight_hole(self, hole_id: str) -> None:
        """高亮指定孔位"""
    
    def switch_sector(self, sector: str) -> None:
        """切换扇区视图"""
```

#### OperationsPanelComponent

操作面板组件，提供检测控制和设置。

```python
class OperationsPanelComponent(QWidget):
    """操作面板组件"""
    
    action_triggered = Signal(str, dict)
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """更新操作面板"""
    
    def update_detection_progress(self, progress: float) -> None:
        """更新检测进度"""
    
    def set_detection_enabled(self, enabled: bool) -> None:
        """设置检测按钮状态"""
```

---

## 📊 视图模型层 API

### MainViewModel

主视图模型，管理UI状态数据。

#### 类定义

```python
@dataclass
class MainViewModel:
    """主视图模型 - 管理UI状态数据"""
```

#### 属性

##### 文件信息

```python
current_file_path: Optional[str] = None  # 当前文件路径
file_info: Dict[str, Any] = field(default_factory=dict)  # 文件信息
```

##### 检测状态

```python
detection_running: bool = False  # 检测是否运行中
detection_progress: float = 0.0  # 检测进度 (0-100)
current_hole_id: Optional[str] = None  # 当前选中孔位ID
```

##### 显示状态

```python
current_sector: Optional[str] = None  # 当前扇区
view_mode: str = "macro"  # 视图模式 ("macro"/"micro")
```

##### 数据状态

```python
hole_collection: Optional[Any] = None  # 孔位集合
status_summary: Dict[str, int] = field(default_factory=dict)  # 状态摘要
```

##### 搜索状态

```python
search_query: str = ""  # 搜索查询
search_results: List[str] = field(default_factory=list)  # 搜索结果
```

##### UI状态

```python
loading: bool = False  # 加载状态
message: str = ""  # 消息内容
message_level: str = "info"  # 消息级别
```

#### 公共方法

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典格式
    
    Returns:
        包含所有状态数据的字典
    """
```

##### from_dict()

```python
def from_dict(self, data: Dict[str, Any]) -> None:
    """
    从字典加载数据
    
    Args:
        data: 状态数据字典
    """
```

#### 使用示例

```python
from src.ui.view_models.main_view_model import MainViewModel

# 创建视图模型
view_model = MainViewModel()

# 设置文件信息
view_model.current_file_path = "/path/to/file.dxf"
view_model.file_info = {"size": 1024, "holes": 100}

# 设置检测状态
view_model.detection_running = True
view_model.detection_progress = 50.0

# 转换为字典
data = view_model.to_dict()

# 从字典恢复
new_model = MainViewModel()
new_model.from_dict(data)
```

### MainViewModelManager

视图模型管理器，负责ViewModel的生命周期管理。

#### 类定义

```python
class MainViewModelManager(QObject):
    """ViewModel管理器"""
```

#### 信号

##### view_model_changed

```python
view_model_changed = Signal(object)
```

**描述**: 当ViewModel发生变化时发出的信号

#### 属性

##### view_model

```python
@property
def view_model(self) -> MainViewModel:
    """获取当前视图模型实例"""
```

#### 公共方法

##### update_file_info()

```python
def update_file_info(self, file_path: str, info: Dict[str, Any]) -> None:
    """
    更新文件信息
    
    Args:
        file_path: 文件路径
        info: 文件信息字典
    """
```

##### update_detection_status()

```python
def update_detection_status(self, running: bool, progress: float) -> None:
    """
    更新检测状态
    
    Args:
        running: 是否运行中
        progress: 检测进度
    """
```

##### update_hole_collection()

```python
def update_hole_collection(self, collection: Any) -> None:
    """
    更新孔位集合
    
    Args:
        collection: 孔位集合对象
    """
```

#### 使用示例

```python
from src.ui.view_models.main_view_model import MainViewModelManager

# 创建管理器
manager = MainViewModelManager()

# 连接信号
def on_view_model_changed(view_model):
    print(f"ViewModel已更新: {view_model.to_dict()}")

manager.view_model_changed.connect(on_view_model_changed)

# 更新状态
manager.update_file_info("/path/to/file.dxf", {"holes": 100})
manager.update_detection_status(True, 25.0)
```

---

## 🏢 业务层 API

### MainBusinessController

主业务控制器，协调各种业务逻辑。

#### 类定义

```python
class MainBusinessController(QObject):
    """主业务控制器 - 协调各种业务逻辑"""
```

#### 信号

##### view_model_changed

```python
view_model_changed = Signal(object)
```

**描述**: ViewModel变化信号

##### message_occurred

```python
message_occurred = Signal(str, str)
```

**描述**: 消息发生信号

**参数**:
- `str`: 消息内容
- `str`: 消息级别 ('info', 'warning', 'error')

#### 构造函数

```python
def __init__(self, data_service: Optional[IDataService] = None) -> None:
    """
    初始化业务控制器
    
    Args:
        data_service: 可选的数据服务实例
    """
```

#### 核心方法

##### handle_user_action()

```python
def handle_user_action(self, action: str, params: Dict[str, Any]) -> None:
    """
    处理用户动作
    
    Args:
        action: 动作类型
        params: 动作参数
    """
```

**支持的动作类型**:
- `load_dxf_file`: 加载DXF文件
- `start_detection`: 开始检测
- `stop_detection`: 停止检测
- `select_hole`: 选择孔位
- `switch_sector`: 切换扇区
- `switch_view`: 切换视图
- `perform_search`: 执行搜索
- `export_report`: 导出报告
- `navigate_hole`: 导航孔位

##### load_dxf_file()

```python
def load_dxf_file(self, params: Dict[str, Any] = None) -> None:
    """
    加载DXF文件
    
    Args:
        params: 可选参数，可包含 'file_path'
    """
```

##### start_detection()

```python
def start_detection(self, params: Dict[str, Any]) -> None:
    """
    开始检测流程
    
    Args:
        params: 检测参数
    """
```

##### stop_detection()

```python
def stop_detection(self, params: Dict[str, Any]) -> None:
    """
    停止检测流程
    
    Args:
        params: 停止参数
    """
```

##### select_hole()

```python
def select_hole(self, params: Dict[str, Any]) -> None:
    """
    选择孔位
    
    Args:
        params: 包含 'hole_id' 的参数字典
    """
```

##### switch_sector()

```python
def switch_sector(self, params: Dict[str, Any]) -> None:
    """
    切换扇形
    
    Args:
        params: 包含 'sector' 的参数字典
    """
```

##### perform_search()

```python
def perform_search(self, params: Dict[str, Any]) -> None:
    """
    执行搜索
    
    Args:
        params: 包含 'query' 的参数字典
    """
```

##### export_report()

```python
def export_report(self, params: Dict[str, Any]) -> None:
    """
    导出报告
    
    Args:
        params: 包含 'type' 和 'file_path' 的参数字典
    """
```

#### 属性

##### view_model_manager

```python
@property
def view_model_manager(self) -> MainViewModelManager:
    """获取视图模型管理器"""
```

##### detection_service

```python
@property
def detection_service(self) -> DetectionService:
    """获取检测服务"""
```

##### file_service

```python
@property
def file_service(self) -> FileService:
    """获取文件服务"""
```

#### 使用示例

```python
from src.controllers.main_business_controller import MainBusinessController

# 创建业务控制器
controller = MainBusinessController()

# 连接信号
def on_message(message, level):
    print(f"[{level.upper()}] {message}")

controller.message_occurred.connect(on_message)

# 处理用户动作
controller.handle_user_action("load_dxf_file", {"file_path": "/path/to/file.dxf"})
controller.handle_user_action("start_detection", {"mode": "auto"})
controller.handle_user_action("select_hole", {"hole_id": "H001"})
```

---

## 🔧 服务层 API

### DetectionService

检测服务，负责检测逻辑的执行。

#### 类定义

```python
class DetectionService(QObject):
    """检测服务"""
```

#### 信号

##### detection_progress

```python
detection_progress = Signal(float)
```

**描述**: 检测进度信号，参数为进度百分比 (0-100)

##### detection_completed

```python
detection_completed = Signal(dict)
```

**描述**: 检测完成信号，参数为检测结果字典

##### detection_error

```python
detection_error = Signal(str)
```

**描述**: 检测错误信号，参数为错误信息

#### 公共方法

##### start_detection()

```python
def start_detection(self, hole_collection: Any, detection_params: Dict[str, Any]) -> None:
    """
    开始检测
    
    Args:
        hole_collection: 孔位集合对象
        detection_params: 检测参数
        
    Raises:
        Exception: 如果检测已在进行中
    """
```

##### stop_detection()

```python
def stop_detection(self) -> None:
    """停止检测"""
```

##### is_running()

```python
def is_running(self) -> bool:
    """
    检查检测是否正在运行
    
    Returns:
        True 如果检测正在运行，否则 False
    """
```

#### 使用示例

```python
from src.controllers.services.detection_service import DetectionService

# 创建检测服务
service = DetectionService()

# 连接信号
def on_progress(progress):
    print(f"检测进度: {progress}%")

def on_completed(results):
    print(f"检测完成: {results}")

def on_error(error):
    print(f"检测错误: {error}")

service.detection_progress.connect(on_progress)
service.detection_completed.connect(on_completed)
service.detection_error.connect(on_error)

# 开始检测
service.start_detection(hole_collection, {"mode": "auto"})

# 检查状态
if service.is_running():
    print("检测正在运行")

# 停止检测
service.stop_detection()
```

### FileService

文件服务，负责文件操作和DXF处理。

#### 类定义

```python
class FileService(QObject):
    """文件服务"""
```

#### 信号

##### file_loaded

```python
file_loaded = Signal(dict)
```

**描述**: 文件加载完成信号

**参数格式**:
```python
{
    'file_path': str,          # 文件路径
    'hole_collection': Any,    # 孔位集合
    'info': Dict[str, Any]     # 文件信息
}
```

##### file_error

```python
file_error = Signal(str)
```

**描述**: 文件操作错误信号

#### 公共方法

##### load_dxf_file()

```python
def load_dxf_file(self, file_path: str) -> None:
    """
    加载DXF文件
    
    Args:
        file_path: DXF文件路径
        
    Emits:
        file_loaded: 加载成功时发出
        file_error: 加载失败时发出
    """
```

##### save_results()

```python
def save_results(self, results: Dict[str, Any], file_path: str) -> bool:
    """
    保存检测结果
    
    Args:
        results: 检测结果数据
        file_path: 保存路径
        
    Returns:
        True 如果保存成功，否则 False
    """
```

##### export_to_pdf()

```python
def export_to_pdf(self, data: Dict[str, Any], file_path: str) -> bool:
    """
    导出PDF报告
    
    Args:
        data: 报告数据
        file_path: PDF文件路径
        
    Returns:
        True 如果导出成功，否则 False
    """
```

##### export_to_excel()

```python
def export_to_excel(self, data: Dict[str, Any], file_path: str) -> bool:
    """
    导出Excel报告
    
    Args:
        data: 报告数据
        file_path: Excel文件路径
        
    Returns:
        True 如果导出成功，否则 False
    """
```

#### 使用示例

```python
from src.controllers.services.file_service import FileService

# 创建文件服务
service = FileService()

# 连接信号
def on_file_loaded(file_data):
    print(f"文件加载成功: {file_data['file_path']}")
    print(f"孔位数量: {len(file_data['hole_collection'])}")

def on_file_error(error):
    print(f"文件操作错误: {error}")

service.file_loaded.connect(on_file_loaded)
service.file_error.connect(on_file_error)

# 加载DXF文件
service.load_dxf_file("/path/to/file.dxf")

# 保存结果
results = {"holes": 100, "passed": 85}
success = service.save_results(results, "/path/to/results.json")

# 导出报告
success = service.export_to_pdf(results, "/path/to/report.pdf")
```

### SearchService

搜索服务，提供数据搜索和过滤功能。

#### 类定义

```python
class SearchService(QObject):
    """搜索服务"""
```

#### 公共方法

##### search()

```python
def search(self, query: str, hole_collection: Any) -> List[str]:
    """
    执行搜索
    
    Args:
        query: 搜索查询字符串
        hole_collection: 要搜索的孔位集合
        
    Returns:
        匹配的孔位ID列表
    """
```

##### search_by_status()

```python
def search_by_status(self, status: str, hole_collection: Any) -> List[str]:
    """
    按状态搜索孔位
    
    Args:
        status: 状态值 ('passed', 'failed', 'warning')
        hole_collection: 孔位集合
        
    Returns:
        匹配状态的孔位ID列表
    """
```

##### search_by_sector()

```python
def search_by_sector(self, sector: str, hole_collection: Any) -> List[str]:
    """
    按扇区搜索孔位
    
    Args:
        sector: 扇区标识
        hole_collection: 孔位集合
        
    Returns:
        指定扇区的孔位ID列表
    """
```

##### filter_holes()

```python
def filter_holes(self, filters: Dict[str, Any], hole_collection: Any) -> List[str]:
    """
    按多个条件过滤孔位
    
    Args:
        filters: 过滤条件字典
        hole_collection: 孔位集合
        
    Returns:
        满足条件的孔位ID列表
    """
```

#### 使用示例

```python
from src.controllers.services.search_service import SearchService

# 创建搜索服务
service = SearchService()

# 基本搜索
results = service.search("H001", hole_collection)
print(f"搜索结果: {results}")

# 按状态搜索
failed_holes = service.search_by_status("failed", hole_collection)
print(f"失败的孔位: {failed_holes}")

# 按扇区搜索
sector_holes = service.search_by_sector("A", hole_collection)
print(f"A扇区孔位: {sector_holes}")

# 多条件过滤
filters = {
    "status": "passed",
    "sector": "A",
    "diameter": {"min": 10, "max": 20}
}
filtered = service.filter_holes(filters, hole_collection)
print(f"过滤结果: {filtered}")
```

### StatusService

状态服务，管理系统和检测状态。

#### 类定义

```python
class StatusService(QObject):
    """状态服务"""
```

#### 信号

##### status_changed

```python
status_changed = Signal(dict)
```

**描述**: 状态变化信号

#### 公共方法

##### update_hole_status()

```python
def update_hole_status(self, hole_id: str, status: str) -> None:
    """
    更新孔位状态
    
    Args:
        hole_id: 孔位ID
        status: 新状态
    """
```

##### get_status_summary()

```python
def get_status_summary(self, hole_collection: Any) -> Dict[str, int]:
    """
    获取状态摘要
    
    Args:
        hole_collection: 孔位集合
        
    Returns:
        状态统计字典
    """
```

##### reset_all_status()

```python
def reset_all_status(self, hole_collection: Any) -> None:
    """
    重置所有状态
    
    Args:
        hole_collection: 孔位集合
    """
```

#### 使用示例

```python
from src.controllers.services.status_service import StatusService

# 创建状态服务
service = StatusService()

# 连接信号
def on_status_changed(status_data):
    print(f"状态已更新: {status_data}")

service.status_changed.connect(on_status_changed)

# 更新孔位状态
service.update_hole_status("H001", "passed")
service.update_hole_status("H002", "failed")

# 获取状态摘要
summary = service.get_status_summary(hole_collection)
print(f"状态摘要: {summary}")
# 输出: {'total': 100, 'passed': 85, 'failed': 10, 'warning': 5}

# 重置所有状态
service.reset_all_status(hole_collection)
```

---

## 🔌 接口定义 API

### IMainViewController

主视图控制器接口。

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class IMainViewController(ABC):
    """主视图控制器接口"""
    
    @abstractmethod
    def setup_ui(self) -> None:
        """设置UI布局"""
        pass
    
    @abstractmethod
    def update_display(self, view_model: 'MainViewModel') -> None:
        """更新UI显示"""
        pass
    
    @abstractmethod
    def show_message(self, message: str, level: str) -> None:
        """显示消息"""
        pass
```

### IMainBusinessController

主业务控制器接口。

```python
class IMainBusinessController(ABC):
    """主业务控制器接口"""
    
    @abstractmethod
    def handle_user_action(self, action: str, params: Dict[str, Any]) -> None:
        """处理用户动作"""
        pass
    
    @abstractmethod
    def start_detection(self, params: Dict[str, Any]) -> None:
        """开始检测流程"""
        pass
```

### IDataService

数据服务接口。

```python
class IDataService(ABC):
    """数据服务接口"""
    
    @abstractmethod
    def load_data(self, file_path: str) -> Any:
        """加载数据"""
        pass
    
    @abstractmethod
    def save_data(self, data: Any, file_path: str) -> bool:
        """保存数据"""
        pass
```

---

## 🛠️ 实用工具 API

### SignalThrottler

信号节流器，用于控制信号发射频率。

```python
class SignalThrottler(QObject):
    """信号节流器"""
    
    throttled_signal = Signal(object)
    
    def __init__(self, delay_ms: int = 100):
        """
        初始化节流器
        
        Args:
            delay_ms: 延迟毫秒数
        """
    
    def emit_throttled(self, value: Any) -> None:
        """
        发射节流信号
        
        Args:
            value: 要发射的值
        """
```

#### 使用示例

```python
from src.utils.mvvm_utils import SignalThrottler

# 创建节流器
throttler = SignalThrottler(200)  # 200ms延迟

# 连接信号
def on_throttled_signal(value):
    print(f"节流信号: {value}")

throttler.throttled_signal.connect(on_throttled_signal)

# 快速连续发射信号（只有最后一个会被处理）
for i in range(10):
    throttler.emit_throttled(i)
```

### TypeValidator

类型验证器，提供数据类型验证功能。

```python
class TypeValidator:
    """类型验证器"""
    
    @staticmethod
    def validate_hole_id(hole_id: str) -> bool:
        """
        验证孔位ID格式
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            True 如果格式正确
        """
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        验证文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            True 如果路径有效
        """
```

---

## 🚨 异常处理 API

### 自定义异常

#### MainWindowError

```python
class MainWindowError(Exception):
    """MainWindow相关错误的基类"""
    pass
```

#### ViewControllerError

```python
class ViewControllerError(MainWindowError):
    """视图控制器错误"""
    pass
```

#### BusinessControllerError

```python
class BusinessControllerError(MainWindowError):
    """业务控制器错误"""
    pass
```

#### DetectionError

```python
class DetectionError(BusinessControllerError):
    """检测相关错误"""
    pass
```

#### FileServiceError

```python
class FileServiceError(BusinessControllerError):
    """文件服务错误"""
    pass
```

### 错误处理示例

```python
from src.exceptions.main_exceptions import DetectionError, FileServiceError

try:
    # 执行检测操作
    detection_service.start_detection(hole_collection, params)
except DetectionError as e:
    print(f"检测错误: {e}")
    # 处理检测错误
except FileServiceError as e:
    print(f"文件错误: {e}")
    # 处理文件错误
except Exception as e:
    print(f"未知错误: {e}")
    # 处理其他错误
```

---

## 📝 完整使用示例

### 基本应用启动

```python
#!/usr/bin/env python3
"""
AIDCIS3-LFS 基本使用示例
"""

import sys
import logging
from PySide6.QtWidgets import QApplication

from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    
    # 创建主协调器
    coordinator = MainWindowCoordinator()
    
    # 连接信号（可选）
    def on_message(message, level):
        print(f"[{level.upper()}] {message}")
    
    coordinator.business_controller.message_occurred.connect(on_message)
    
    # 显示主窗口
    coordinator.show()
    
    # 运行应用
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### 自定义业务逻辑

```python
"""
自定义业务逻辑示例
"""

from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
from src.controllers.services.detection_service import DetectionService

class CustomDetectionService(DetectionService):
    """自定义检测服务"""
    
    def start_detection(self, hole_collection, detection_params):
        # 自定义检测逻辑
        print("开始自定义检测...")
        super().start_detection(hole_collection, detection_params)

# 使用自定义服务
coordinator = MainWindowCoordinator()
custom_service = CustomDetectionService()

# 替换默认服务
coordinator.business_controller.detection_service = custom_service
```

### 扩展UI组件

```python
"""
扩展UI组件示例
"""

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Signal

class CustomOperationsPanel(QWidget):
    """自定义操作面板"""
    
    action_triggered = Signal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加自定义按钮
        self.custom_button = QPushButton("自定义操作")
        self.custom_button.clicked.connect(self.on_custom_action)
        layout.addWidget(self.custom_button)
    
    def on_custom_action(self):
        self.action_triggered.emit("custom_action", {})
    
    def update_from_view_model(self, view_model):
        # 根据ViewModel更新UI
        pass

# 在主视图控制器中使用
coordinator = MainWindowCoordinator()
view_controller = coordinator.view_controller

# 替换操作面板
custom_panel = CustomOperationsPanel()
custom_panel.action_triggered.connect(
    coordinator.business_controller.handle_user_action
)

# 在UI中替换组件（需要在具体实现中完成）
```

---

## 📊 性能优化建议

### 信号连接优化

```python
# 使用Qt.QueuedConnection确保线程安全
signal.connect(slot, Qt.QueuedConnection)

# 使用信号节流避免频繁更新
throttler = SignalThrottler(100)  # 100ms节流
throttler.throttled_signal.connect(update_ui)
```

### 内存管理

```python
# 正确清理资源
def cleanup(self):
    if self.detection_worker:
        self.detection_worker.stop()
        self.detection_worker.wait()
        self.detection_worker = None
```

### 大数据处理

```python
# 使用分页处理大量数据
def load_large_dataset(self, file_path, page_size=1000):
    for chunk in self.load_chunks(file_path, page_size):
        self.process_chunk(chunk)
        QApplication.processEvents()  # 保持UI响应
```

---

## ❓ 常见问题解答

### Q: 如何添加新的用户动作？

A: 在MainBusinessController中添加新的处理方法，并在handle_user_action中注册：

```python
def handle_user_action(self, action: str, params: Dict[str, Any]):
    action_handlers = {
        'existing_action': self.existing_method,
        'new_action': self.new_method,  # 添加新动作
    }
    # ...
```

### Q: 如何扩展ViewModel？

A: 可以继承MainViewModel或创建新的ViewModel类：

```python
@dataclass
class ExtendedViewModel(MainViewModel):
    custom_field: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)
```

### Q: 如何处理异步操作？

A: 使用QThread或信号机制：

```python
class AsyncOperation(QThread):
    result_ready = Signal(object)
    
    def run(self):
        result = self.perform_operation()
        self.result_ready.emit(result)
```

---

## 📚 相关文档

- [README.md](README.md) - 项目概述和快速开始
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计文档
- [docs/examples/](docs/examples/) - 使用示例

---

**📞 技术支持**: 如有API使用问题，请查阅相关文档或提交Issue

**🔄 版本**: v2.0.0 API参考

**📅 最后更新**: 2025-07-25