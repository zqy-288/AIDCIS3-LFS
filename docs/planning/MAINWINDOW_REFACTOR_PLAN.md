# MainWindow 重构方案
## 基于技术债务评估报告的紧急修复计划

### 📋 重构目标
- 将5882行的MainWindow拆分为3个核心组件
- 实现高内聚、低耦合的架构
- 符合SOLID原则和MVVM模式
- 减少技术债务，提升代码可维护性

### 🎯 拆分策略

#### 1. MainViewController (UI层) - 约1800行
**职责**: 纯UI管理，不包含业务逻辑

```python
class MainViewController(QMainWindow):
    """主视图控制器 - 专注UI展示和用户交互"""
    
    # 只发出事件，不处理业务逻辑
    user_action = Signal(str, dict)  # 用户动作信号
    
    def setup_ui(self):
        """设置UI布局"""
        
    def create_toolbar(self) -> QWidget:
        """创建工具栏"""
        
    def create_left_info_panel(self) -> QWidget:
        """创建左侧信息面板"""
        
    def create_center_visualization_panel(self) -> QWidget:
        """创建中央可视化面板"""
        
    def create_right_operations_panel(self) -> QWidget:
        """创建右侧操作面板"""
        
    def update_display(self, view_model: MainViewModel):
        """根据ViewModel更新UI显示"""
        
    def show_message(self, message: str, level: str):
        """显示消息"""
        
    def set_loading_state(self, loading: bool):
        """设置加载状态"""
```

#### 2. MainBusinessController (业务层) - 约2000行
**职责**: 业务逻辑协调，不直接操作UI

```python
class MainBusinessController(QObject):
    """主业务控制器 - 协调各种业务逻辑"""
    
    # 业务状态变化信号
    view_model_changed = Signal(object)  # ViewModel变化
    message_occurred = Signal(str, str)  # 消息和级别
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.detection_service = DetectionService()
        self.file_service = FileService()
        self.search_service = SearchService()
        
    def handle_user_action(self, action: str, params: dict):
        """处理用户动作"""
        
    def start_detection(self, params: dict):
        """开始检测流程"""
        
    def load_dxf_file(self, file_path: str):
        """加载DXF文件"""
        
    def select_hole(self, hole_id: str):
        """选择孔位"""
        
    def switch_sector(self, sector: SectorQuadrant):
        """切换扇形"""
        
    def perform_search(self, query: str):
        """执行搜索"""
        
    def export_report(self, params: dict):
        """导出报告"""
```

#### 3. MainViewModel (数据绑定层) - 约800行
**职责**: 数据状态管理和绑定

```python
@dataclass
class MainViewModel:
    """主视图模型 - 管理UI状态数据"""
    
    # 文件信息
    current_file_path: Optional[str] = None
    file_info: Dict[str, Any] = field(default_factory=dict)
    
    # 检测状态
    detection_running: bool = False
    detection_progress: float = 0.0
    current_hole_id: Optional[str] = None
    
    # 显示状态
    current_sector: Optional[SectorQuadrant] = None
    view_mode: str = "macro"  # macro/micro
    
    # 数据状态
    hole_collection: Optional[HoleCollection] = None
    status_summary: Dict[str, int] = field(default_factory=dict)
    
    # 搜索状态
    search_query: str = ""
    search_results: List[str] = field(default_factory=list)
    
    # UI状态
    loading: bool = False
    message: str = ""
    message_level: str = "info"  # info/warning/error


class MainViewModelManager(QObject):
    """ViewModel管理器"""
    
    view_model_changed = Signal(object)
    
    def __init__(self):
        self._view_model = MainViewModel()
        
    @property
    def view_model(self) -> MainViewModel:
        return self._view_model
        
    def update_file_info(self, file_path: str, info: dict):
        """更新文件信息"""
        self._view_model.current_file_path = file_path
        self._view_model.file_info = info
        self.view_model_changed.emit(self._view_model)
        
    def update_detection_status(self, running: bool, progress: float):
        """更新检测状态"""
        self._view_model.detection_running = running
        self._view_model.detection_progress = progress
        self.view_model_changed.emit(self._view_model)
        
    def update_hole_collection(self, collection: HoleCollection):
        """更新孔位集合"""
        self._view_model.hole_collection = collection
        self.view_model_changed.emit(self._view_model)
```

#### 4. 协调器 (Coordinator) - 约200行
**职责**: 组件间通信协调

```python
class MainWindowCoordinator(QObject):
    """主窗口协调器 - 协调各个组件"""
    
    def __init__(self):
        self.view_controller = MainViewController()
        self.business_controller = MainBusinessController()
        self.view_model_manager = MainViewModelManager()
        
        self._setup_connections()
        
    def _setup_connections(self):
        """设置组件间连接"""
        # 用户动作 -> 业务处理
        self.view_controller.user_action.connect(
            self.business_controller.handle_user_action
        )
        
        # 业务结果 -> ViewModel更新
        self.business_controller.view_model_changed.connect(
            self.view_model_manager.set_view_model
        )
        
        # ViewModel变化 -> UI更新
        self.view_model_manager.view_model_changed.connect(
            self.view_controller.update_display
        )
        
        # 消息处理
        self.business_controller.message_occurred.connect(
            self.view_controller.show_message
        )
        
    def show(self):
        """显示主窗口"""
        self.view_controller.show()
```

### 📁 文件组织结构

```
src/
├── ui/
│   ├── __init__.py
│   ├── main_view_controller.py      # UI控制器
│   ├── ui_components/               # UI组件
│   │   ├── toolbar_widget.py
│   │   ├── info_panel_widget.py
│   │   ├── visualization_panel_widget.py
│   │   └── operations_panel_widget.py
│   └── view_models/
│       ├── __init__.py
│       ├── main_view_model.py       # 视图模型
│       └── view_model_manager.py    # ViewModel管理器
│
├── controllers/
│   ├── __init__.py
│   ├── main_business_controller.py  # 业务控制器
│   ├── services/                    # 业务服务
│   │   ├── detection_service.py
│   │   ├── file_service.py
│   │   └── search_service.py
│   └── coordinators/
│       ├── __init__.py
│       └── main_window_coordinator.py  # 主协调器
│
└── main_window.py                   # 简化的入口文件
```

### 🔄 渐进式迁移计划

#### 阶段1: 准备工作 (1-2天)
1. 创建新的文件结构
2. 定义接口和数据模型
3. 创建基础的ViewModel

#### 阶段2: UI层拆分 (3-4天)
1. 提取UI创建方法到MainViewController
2. 实现ViewModel绑定机制
3. 测试UI显示功能

#### 阶段3: 业务层拆分 (4-5天)
1. 提取业务逻辑到MainBusinessController
2. 重构事件处理机制
3. 实现服务层解耦

#### 阶段4: 集成测试 (2-3天)
1. 集成各个组件
2. 验证功能完整性
3. 性能优化

#### 阶段5: 清理优化 (1-2天)
1. 删除旧代码
2. 优化组件通信
3. 添加文档

### 🎯 预期收益

#### 代码质量提升
- MainWindow代码量从5882行减少到200行 (减少96.6%)
- 单个类职责单一，符合SOLID原则
- 组件间依赖清晰，易于测试

#### 开发效率提升
- UI修改不影响业务逻辑
- 业务逻辑修改不影响UI
- 新功能开发更加灵活

#### 维护成本降低
- 问题定位更精确
- 代码修改风险更小
- 测试覆盖更全面

### ⚠️ 风险控制

1. **兼容性风险**: 保持现有公共接口不变
2. **性能风险**: 通过基准测试验证性能
3. **稳定性风险**: 分阶段迁移，每个阶段充分测试
4. **学习成本**: 提供详细的迁移文档和示例

### 📊 成功指标

- [ ] MainWindow代码行数 < 300行
- [ ] 组件间依赖深度 < 3层  
- [ ] 单元测试覆盖率 > 60%
- [ ] 功能回归测试通过率 = 100%
- [ ] 新功能开发时间减少 > 30%

---

**下一步**: 开始实施阶段1的准备工作，创建基础架构和接口定义。