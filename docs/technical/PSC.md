# 共享背景信息 - MainWindow重构项目
## AI协作项目基石文档

### 📋 项目概述

**项目名称**: AIDCIS3-LFS MainWindow架构重构  
**重构目标**: 将5882行的单体MainWindow拆分为高内聚、低耦合的MVVM架构  
**技术债务等级**: 严重 ⚠️  
**紧急程度**: 高优先级，需要在1-2周内完成第一阶段  

### 🏗️ 系统架构现状

#### 当前技术栈
- **UI框架**: PySide6 (Qt6)
- **编程语言**: Python 3.8+
- **架构模式**: 单体架构 (问题所在)
- **项目结构**: 
  ```
  src/
  ├── main_window.py (5882行 - 待拆分)
  ├── core_business/
  ├── modules/
  ├── ui/ (目标新建)
  └── controllers/ (目标新建)
  ```

#### 核心问题分析
1. **MainWindow类职责过多** (违反SRP)
   - UI布局管理 (40%代码)
   - 业务逻辑协调 (30%代码) 
   - 事件处理 (20%代码)
   - 系统集成 (10%代码)

2. **全局状态滥用**
   - SharedDataManager被10+模块直接依赖
   - 缺乏清晰的数据流向

3. **依赖关系混乱**
   - UI层直接导入business层
   - 最深依赖链达13层

### 🎯 重构目标架构 (MVVM模式)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  View Layer     │    │  ViewModel Layer │    │ Controller Layer│
│                 │    │                  │    │                 │
│ MainViewController │◄──│ MainViewModel    │◄──│MainBusinessCtrl │
│ (UI 纯展示)      │    │ (数据状态)        │    │ (业务逻辑)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
    用户交互事件              ViewModel变化              业务服务调用
```

### 📊 任务分工方案

#### AI-1 负责: MainViewController (UI层)
**文件**: `src/ui/main_view_controller.py`  
**代码量**: ~1800行  
**职责范围**:
- 创建所有UI组件 (工具栏、面板、选项卡)
- 处理用户交互事件 (点击、输入、选择)
- 根据ViewModel更新UI显示
- 管理UI状态 (加载、禁用、样式)

**关键接口**:
```python
class MainViewController(QMainWindow):
    # 输出信号 (发送给Coordinator)
    user_action = Signal(str, dict)  # 用户动作
    
    # 输入方法 (从ViewModel接收)
    def update_display(self, view_model: MainViewModel)
    def show_message(self, message: str, level: str)
    def set_loading_state(self, loading: bool)
```

#### AI-2 负责: MainBusinessController (业务层)
**文件**: `src/controllers/main_business_controller.py`  
**代码量**: ~2000行  
**职责范围**:
- 处理所有业务逻辑 (检测、文件处理、搜索)
- 协调各种服务 (DetectionService, FileService等)
- 管理业务状态变化
- 与数据服务层交互

**关键接口**:
```python
class MainBusinessController(QObject):
    # 输出信号 (发送给ViewModel)
    view_model_changed = Signal(object)
    message_occurred = Signal(str, str)
    
    # 输入方法 (从Coordinator接收)
    def handle_user_action(self, action: str, params: dict)
```

#### AI-3 负责: MainViewModel + Coordinator (数据绑定层)
**文件**: `src/ui/view_models/main_view_model.py`, `src/controllers/coordinators/main_window_coordinator.py`  
**代码量**: ~1000行  
**职责范围**:
- 定义数据模型和状态管理
- 协调View和Controller通信
- 管理组件生命周期
- 实现数据绑定机制

**关键接口**:
```python
@dataclass
class MainViewModel:
    # 所有UI状态数据
    current_file_path: Optional[str]
    detection_running: bool
    current_hole_id: Optional[str]
    # ...更多状态字段

class MainWindowCoordinator(QObject):
    # 组装和协调所有组件
    def __init__(self):
        self.view_controller = MainViewController()
        self.business_controller = MainBusinessController()
        self.view_model_manager = MainViewModelManager()
```

### 🔗 组件通信协议

#### 数据流向
```
User Input → MainViewController → MainWindowCoordinator 
    ↓
MainBusinessController → Business Services → Data Layer
    ↓
MainViewModel Update → MainViewController → UI Update
```

#### 信号定义规范
```python
# 用户动作信号格式
user_action = Signal(str, dict)
# 示例: ("load_file", {"file_path": "/path/to/file.dxf"})
# 示例: ("select_hole", {"hole_id": "C001R001"})
# 示例: ("start_detection", {"mode": "auto"})

# ViewModel变化信号格式  
view_model_changed = Signal(object)  # MainViewModel实例

# 消息信号格式
message_occurred = Signal(str, str)  # (message, level)
# level: "info", "warning", "error", "success"
```

### 📁 强制文件结构约定

**所有AI必须遵循此结构创建文件**:

```
src/
├── ui/
│   ├── __init__.py
│   ├── main_view_controller.py           # AI-1创建
│   ├── components/                       # AI-1创建
│   │   ├── __init__.py
│   │   ├── toolbar_component.py
│   │   ├── info_panel_component.py
│   │   ├── visualization_panel_component.py
│   │   └── operations_panel_component.py
│   └── view_models/                      # AI-3创建
│       ├── __init__.py
│       ├── main_view_model.py
│       └── view_model_manager.py
│
├── controllers/                          # AI-2创建
│   ├── __init__.py
│   ├── main_business_controller.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── detection_service.py
│   │   ├── file_service.py
│   │   └── search_service.py
│   └── coordinators/                     # AI-3创建
│       ├── __init__.py
│       └── main_window_coordinator.py
│
└── main_window.py                        # AI-3重写(简化版)
```

### 🔍 现有代码分析 (供参考)

#### 原MainWindow关键组件
```python
# 当前需要保持兼容的核心组件
self.dxf_parser = DXFParser()
self.status_manager = StatusManager() 
self.data_service = get_data_service()
self.shared_data_manager = SharedDataManager()

# 当前UI组件结构
create_toolbar() → 工具栏
create_left_info_panel() → 左侧信息面板
create_center_visualization_panel() → 中央可视化
create_right_operations_panel() → 右侧操作

# 关键业务方法
on_product_selected() → 产品选择
load_dxf_from_product() → DXF加载
start_detection() → 开始检测
perform_search() → 搜索功能
```

#### 重要依赖关系
```python
# 这些导入关系必须在重构中保持
from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from src.modules.realtime_chart import RealtimeChart
from src.modules.unified_history_viewer import UnifiedHistoryViewer
```

### ⚠️ 关键约束条件

#### 兼容性要求
1. **外部接口保持不变**: main_window.py的公共方法签名不能改变
2. **信号保持兼容**: 现有的Signal定义必须保留
3. **组件引用保持**: 其他模块对MainWindow的引用不能破坏

#### 技术约束
1. **必须使用PySide6**: 不能更换UI框架
2. **保持现有依赖**: 不能移除现有的核心依赖包
3. **渐进式迁移**: 必须支持分阶段部署和回滚

#### 性能要求
1. **启动时间**: 不能超过当前启动时间的110%
2. **内存使用**: 不能超过当前内存使用的120%  
3. **响应性**: UI响应时间不能劣化

### 🧪 测试验证标准

#### 功能测试 (每个AI都要验证)
```python
# 必须通过的基础测试
def test_basic_functionality():
    # 1. UI能正常显示
    # 2. 文件加载功能正常
    # 3. 检测流程能启动
    # 4. 搜索功能正常
    # 5. 扇形切换正常
```

#### 集成测试 (AI-3负责)
```python
def test_component_integration():
    # 1. 组件间通信正常
    # 2. 数据流向正确
    # 3. 状态同步准确
    # 4. 错误处理完善
```

#### 性能测试
```python
def test_performance():
    # 1. 启动时间 < 5秒
    # 2. UI响应 < 100ms
    # 3. 内存使用稳定
    # 4. 无内存泄漏
```

### 📝 代码规范要求

#### 文档规范
```python
"""
模块文档必须包含:
1. 模块职责说明
2. 主要类和方法介绍  
3. 使用示例
4. 注意事项
"""

class ExampleClass:
    """
    类文档必须包含:
    1. 类的用途和职责
    2. 初始化参数说明
    3. 主要方法概述
    4. 使用示例
    """
    
    def example_method(self, param1: str, param2: int) -> bool:
        """
        方法文档必须包含:
        
        Args:
            param1: 参数1说明
            param2: 参数2说明
            
        Returns:
            返回值说明
            
        Raises:
            可能的异常说明
        """
```

#### 命名规范
- **类名**: PascalCase (MainViewController)
- **方法名**: snake_case (handle_user_action)
- **常量**: UPPER_SNAKE_CASE (DEFAULT_TIMEOUT)
- **私有方法**: _private_method
- **信号**: camelCase (userAction, viewModelChanged)

#### 类型注解要求
```python
# 必须使用类型注解
from typing import Optional, Dict, List, Any

def process_data(
    input_data: Dict[str, Any],
    config: Optional[Dict[str, str]] = None
) -> List[HoleData]:
    """必须有类型注解的方法示例"""
```

### 🚀 实施顺序

#### 阶段1: 基础架构 (第1-2天)
1. **AI-3**: 创建目录结构和基础接口定义
2. **AI-1**: 创建UI组件基础框架
3. **AI-2**: 创建业务服务基础框架

#### 阶段2: 核心功能 (第3-7天)
1. **AI-1**: 实现UI组件和事件处理
2. **AI-2**: 实现业务逻辑和服务层
3. **AI-3**: 实现ViewModel和数据绑定

#### 阶段3: 集成测试 (第8-10天)
1. **AI-3**: 组装所有组件并测试
2. **All**: 修复集成问题
3. **AI-3**: 性能优化和文档

### 📋 每日检查清单

#### AI-1 (UI层) 日检查
- [ ] UI组件正确渲染
- [ ] 用户交互事件正确发出
- [ ] ViewModel数据正确绑定到UI
- [ ] 样式和布局符合原始设计

#### AI-2 (业务层) 日检查  
- [ ] 业务逻辑处理正确
- [ ] 服务层接口调用正常
- [ ] 异常处理完善
- [ ] 状态变化正确通知

#### AI-3 (协调层) 日检查
- [ ] 组件间通信正常
- [ ] 数据流向正确
- [ ] 性能指标达标
- [ ] 整体功能完整

### 🆘 应急预案

#### 如果遇到问题
1. **接口不匹配**: 参考本文档的接口定义部分
2. **依赖冲突**: 检查现有代码分析部分
3. **性能问题**: 参考性能要求部分的约束
4. **功能缺失**: 检查任务分工部分的职责范围

#### 回滚策略
- 保持原始main_window.py作为备份
- 每个阶段完成后创建检查点
- 遇到严重问题时可以分阶段回滚

---

**重要提醒**: 这是一个协作项目，每个AI负责不同的层，但最终必须能无缝集成。请严格按照本文档的接口定义和约束条件进行开发。

**成功标志**: 当三个AI的代码能够完美集成，MainWindow从5882行减少到200行以内，同时保持所有原有功能正常工作。