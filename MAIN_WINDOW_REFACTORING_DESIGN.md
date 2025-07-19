# main_window.py 拆解架构设计 v2.0

## 🎯 **核心改进原则**
1. **进一步细化控制器职责**
2. **引入明确的Model层**
3. **规范事件总线使用**
4. **信号机制下沉**
5. **实现真正的单一职责原则**

## 📋 **当前问题分析**
- **文件规模**：4751行代码，过于庞大
- **职责混乱**：UI管理、业务逻辑、数据处理、状态管理混合在一起
- **维护困难**：单一文件承载过多功能
- **测试困难**：难以进行单元测试和模块化测试
- **架构冗余**：现有ApplicationCore和EventBus未被充分利用

## 🔧 **重新设计的架构**

### **现有架构组件分析**
项目已包含以下核心架构组件：
- **ApplicationCore** - 位于 `src/core/application.py`
- **EventBus** - 位于 `src/core/application.py`（第63行开始）
- **DependencyContainer** - 位于 `src/core/dependency_injection.py`
- **业务模型** - 位于 `src/core_business/models/`

### **1. 模型层 (Model Layer) - 基于现有组件优化**

#### **1.1 应用程序数据模型**
```python
# src/models/application_model.py (新建文件，约300-400行)
# 扩展现有的 src/core_business/models/hole_data.py 中的 HoleCollection
class ApplicationModel(QObject):
    """应用程序数据模型 - 单一真实数据源"""
    
    # 数据变化信号
    workpiece_loaded = Signal(str)  # 工件加载
    hole_data_changed = Signal(str, dict)  # 孔位数据变化
    detection_status_changed = Signal(str, str)  # 检测状态变化
    application_state_changed = Signal(str, object)  # 应用状态变化
    
    def __init__(self):
        super().__init__()
        self._current_workpiece = None
        self._hole_collection = None  # 使用现有的 HoleCollection 类
        self._detection_state = DetectionState.IDLE
        self._selected_holes = []
        self._application_config = {}
        self._detection_results = {}
    
    @property
    def current_workpiece(self):
        return self._current_workpiece
    
    @current_workpiece.setter
    def current_workpiece(self, value):
        if self._current_workpiece != value:
            self._current_workpiece = value
            self.workpiece_loaded.emit(value)
    
    def update_hole_data(self, hole_id, data):
        """更新孔位数据"""
        if hole_id in self._hole_collection:
            self._hole_collection[hole_id].update(data)
            self.hole_data_changed.emit(hole_id, data)
    
    def get_detection_summary(self):
        """获取检测摘要"""
        return {
            'total_holes': len(self._hole_collection) if self._hole_collection else 0,
            'detected_holes': len(self._detection_results),
            'detection_rate': self._calculate_detection_rate()
        }
```

#### **1.2 检测状态枚举**
```python
# src/models/detection_state.py (新建文件，约50-100行)
# 或者扩展现有的 src/core_business/models/status_manager.py
class DetectionState(Enum):
    """检测状态枚举"""
    IDLE = "idle"
    LOADING = "loading"
    DETECTING = "detecting"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
```

#### **1.3 事件类型常量**
```python
# src/models/event_types.py (新建文件，约50-100行)
class EventTypes:
    """事件类型常量 - 统一管理所有事件名称"""
    
    # UI导航事件
    NAVIGATE_TO_TAB = "navigate_to_tab"
    NAVIGATE_TO_HOLE = "navigate_to_hole"
    
    # 数据操作事件
    DXF_FILE_LOADED = "dxf_file_loaded"
    HOLE_SELECTED = "hole_selected"
    DETECTION_STARTED = "detection_started"
    DETECTION_COMPLETED = "detection_completed"
    
    # 视图更新事件
    VIEWPORT_CHANGED = "viewport_changed"
    SIDEBAR_UPDATED = "sidebar_updated"
    
    # 系统事件
    APPLICATION_READY = "application_ready"
    SETTINGS_CHANGED = "settings_changed"
```

### **2. 细化后的控制器层**

#### **2.1 主检测协调器**
```python
# src/controllers/main_detection_coordinator.py (新建文件，约200-300行)
class MainDetectionCoordinator:
    """主检测协调器 - 仅负责协调各子控制器"""
    
    def __init__(self, parent, model: ApplicationModel, event_bus: EventBus):
        self.parent = parent
        self.model = model
        self.event_bus = event_bus  # 使用现有的 EventBus (src/core/application.py)
        
        # 创建子控制器
        self.dxf_controller = DXFViewController(parent, model, event_bus)
        self.sidebar_controller = SidebarController(parent, model, event_bus)
        self.viewport_controller = ViewportController(parent, model, event_bus)
        self.detection_controller = DetectionController(parent, model, event_bus)
        
        self.setup_coordination()
    
    def setup_coordination(self):
        """设置控制器间的协调逻辑"""
        # 订阅关键事件，协调各子控制器
        self.event_bus.subscribe(EventTypes.DXF_FILE_LOADED, self.on_dxf_loaded)
        self.event_bus.subscribe(EventTypes.HOLE_SELECTED, self.on_hole_selected)
        self.event_bus.subscribe(EventTypes.DETECTION_STARTED, self.on_detection_started)
    
    def on_dxf_loaded(self, event_data):
        """DXF文件加载后的协调逻辑"""
        # 协调各子控制器响应DXF加载
        pass
    
    def on_hole_selected(self, event_data):
        """孔位选择后的协调逻辑"""
        # 协调视图更新和侧边栏更新
        pass
```

#### **2.2 DXF视图控制器**
```python
# src/controllers/dxf_view_controller.py (新建文件，约250-350行)
class DXFViewController:
    """DXF视图控制器 - 专门处理DXF文件解析和显示"""
    
    # 局部信号 - 不依赖MainWindow
    dxf_loaded = Signal(str, object)
    parsing_progress = Signal(int)
    parsing_error = Signal(str)
    
    def __init__(self, parent, model: ApplicationModel, event_bus: EventBus):
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        self.dxf_parser = DXFParser()  # 使用现有的 src/core_business/dxf_parser.py
        
        # 连接模型信号
        self.model.workpiece_loaded.connect(self.on_workpiece_loaded)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置DXF相关UI组件"""
        # 文件加载工具栏
        # DXF预览区域
        # 解析进度显示
        pass
    
    def load_dxf_file(self, file_path):
        """加载DXF文件"""
        try:
            # 解析DXF文件
            hole_collection = self.dxf_parser.parse_file(file_path)
            
            # 更新模型
            self.model.hole_collection = hole_collection
            self.model.current_workpiece = self.extract_workpiece_id(file_path)
            
            # 发布事件
            self.event_bus.publish(EventTypes.DXF_FILE_LOADED, {
                'file_path': file_path,
                'hole_collection': hole_collection
            })
            
            # 发出局部信号
            self.dxf_loaded.emit(file_path, hole_collection)
            
        except Exception as e:
            self.parsing_error.emit(str(e))
    
    def update_dxf_display(self):
        """更新DXF显示"""
        # 根据模型数据更新显示
        pass
```

#### **2.3 侧边栏控制器**
```python
# src/controllers/sidebar_controller.py (新建文件，约200-300行)
class SidebarController:
    """侧边栏控制器 - 管理侧边栏交互逻辑"""
    
    # 局部信号
    hole_info_requested = Signal(str)
    status_filter_changed = Signal(list)
    
    def __init__(self, parent, model: ApplicationModel, event_bus: EventBus):
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        
        # 订阅相关事件
        self.event_bus.subscribe(EventTypes.HOLE_SELECTED, self.update_hole_info)
        self.event_bus.subscribe(EventTypes.DETECTION_COMPLETED, self.update_statistics)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置侧边栏UI"""
        # 文件信息面板
        # 状态统计面板
        # 孔位信息面板
        # 过滤器面板
        pass
    
    def update_hole_info(self, event_data):
        """更新孔位信息显示"""
        hole_id = event_data.get('hole_id')
        hole_data = self.model.get_hole_data(hole_id)
        # 更新显示
        pass
    
    def update_statistics(self, event_data):
        """更新统计信息"""
        summary = self.model.get_detection_summary()
        # 更新统计显示
        pass
```

#### **2.4 视口控制器**
```python
# src/controllers/viewport_controller.py (新建文件，约300-400行)
class ViewportController:
    """视口控制器 - 管理主视图区域的显示和交互"""
    
    # 局部信号
    hole_clicked = Signal(str)
    viewport_changed = Signal(dict)
    zoom_changed = Signal(float)
    
    def __init__(self, parent, model: ApplicationModel, event_bus: EventBus):
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        self.graphics_view = OptimizedGraphicsView()  # 使用现有的 src/core_business/graphics/graphics_view.py
        
        # 订阅相关事件
        self.event_bus.subscribe(EventTypes.DXF_FILE_LOADED, self.load_viewport_data)
        self.event_bus.subscribe(EventTypes.HOLE_SELECTED, self.highlight_hole)
        
        self.setup_ui()
        self.setup_interactions()
    
    def setup_ui(self):
        """设置视口UI"""
        # 图形视图区域
        # 缩放控制
        # 视图工具栏
        pass
    
    def setup_interactions(self):
        """设置交互逻辑"""
        # 鼠标点击事件
        # 缩放事件
        # 平移事件
        pass
    
    def load_viewport_data(self, event_data):
        """加载视口数据"""
        hole_collection = event_data.get('hole_collection')
        self.graphics_view.load_holes(hole_collection)
        # 发布视口变化事件
        self.event_bus.publish(EventTypes.VIEWPORT_CHANGED, {
            'action': 'data_loaded',
            'hole_count': len(hole_collection)
        })
    
    def highlight_hole(self, event_data):
        """高亮显示孔位"""
        hole_id = event_data.get('hole_id')
        # 高亮逻辑
        pass
```

#### **2.5 检测控制器**
```python
# src/controllers/detection_controller.py (新建文件，约250-350行)
class DetectionController:
    """检测控制器 - 管理检测流程"""
    
    # 局部信号
    detection_started = Signal()
    detection_paused = Signal()
    detection_completed = Signal(dict)
    detection_progress = Signal(int, str)
    
    def __init__(self, parent, model: ApplicationModel, event_bus: EventBus):
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        self.detection_timer = QTimer()
        
        # 连接模型信号
        self.model.detection_status_changed.connect(self.on_detection_status_changed)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置检测控制UI"""
        # 检测控制面板
        # 进度显示
        # 状态指示器
        pass
    
    def start_detection(self):
        """启动检测"""
        self.model.detection_state = DetectionState.DETECTING
        self.detection_started.emit()
        
        # 发布检测启动事件
        self.event_bus.publish(EventTypes.DETECTION_STARTED, {
            'timestamp': datetime.now(),
            'hole_count': len(self.model.hole_collection)
        })
        
        # 启动检测逻辑
        self.detection_timer.start(100)  # 100ms间隔
    
    def pause_detection(self):
        """暂停检测"""
        self.model.detection_state = DetectionState.PAUSED
        self.detection_paused.emit()
        self.detection_timer.stop()
    
    def complete_detection(self):
        """完成检测"""
        self.model.detection_state = DetectionState.COMPLETED
        
        # 收集检测结果
        results = self.model.get_detection_summary()
        
        self.detection_completed.emit(results)
        
        # 发布检测完成事件
        self.event_bus.publish(EventTypes.DETECTION_COMPLETED, results)
```

### **3. 简化后的主窗口**
```python
# src/main_window.py (重构后，约150-200行)
class MainWindow(QMainWindow):
    """主窗口 - 仅负责窗口管理和顶层协调"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化核心组件
        self.model = ApplicationModel()
        self.event_bus = EventBus()  # 使用现有的 src/core/application.py 中的 EventBus
        self.state_manager = UIStateManager()
        
        # 初始化选项卡管理器
        self.tab_manager = TabManager(self, self.model, self.event_bus)
        
        # 初始化各控制器
        self.main_detection_coordinator = MainDetectionCoordinator(
            self, self.model, self.event_bus
        )
        self.realtime_controller = RealtimeController(
            self, self.model, self.event_bus
        )
        self.history_controller = HistoryController(
            self, self.model, self.event_bus
        )
        self.report_controller = ReportController(
            self, self.model, self.event_bus
        )
        
        self.setup_ui()
        self.setup_global_connections()
        self.setup_event_subscriptions()
    
    def setup_ui(self):
        """设置基础UI"""
        # 菜单栏
        # 工具栏
        # 状态栏
        # 选项卡容器
        pass
    
    def setup_global_connections(self):
        """设置全局连接 - 仅保留必要的顶层连接"""
        # 连接各控制器的关键信号
        self.main_detection_coordinator.dxf_controller.dxf_loaded.connect(
            self.on_dxf_loaded
        )
        # 其他顶层连接
        pass
    
    def setup_event_subscriptions(self):
        """设置事件订阅 - 仅订阅需要窗口级别处理的事件"""
        self.event_bus.subscribe(EventTypes.APPLICATION_READY, self.on_app_ready)
        self.event_bus.subscribe(EventTypes.NAVIGATE_TO_TAB, self.on_navigate_to_tab)
    
    def on_dxf_loaded(self, file_path, hole_collection):
        """DXF加载完成处理"""
        # 更新窗口标题
        self.setWindowTitle(f"AIDCIS3-LFS - {os.path.basename(file_path)}")
        
        # 更新状态栏
        self.statusBar().showMessage(f"已加载 {len(hole_collection)} 个孔位")
    
    def on_navigate_to_tab(self, event_data):
        """处理选项卡导航"""
        tab_name = event_data.get('tab_name')
        self.tab_manager.switch_tab(tab_name)
```

### **4. 事件总线使用规范**
```python
# 使用现有的 src/core/application.py 中的 EventBus 类
# 位置：src/core/application.py 第63行开始
class EventBus(QObject):
    """事件总线 - 基于现有实现优化"""
    
    # 现有实现已包含基本的事件发布/订阅功能
    # 建议在现有基础上添加以下功能：
    
    def __init__(self):
        super().__init__()
        self.listeners = {}
        self.event_history = []  # 用于调试
        self.max_history = 100
    
    def subscribe(self, event_type: str, callback: callable, priority: int = 0):
        """订阅事件 - 支持优先级"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append((callback, priority))
        # 按优先级排序
        self.listeners[event_type].sort(key=lambda x: x[1], reverse=True)
    
    def publish(self, event_type: str, data: dict = None, source: str = None):
        """发布事件 - 记录来源"""
        if event_type not in EventTypes.__dict__.values():
            raise ValueError(f"未定义的事件类型: {event_type}")
        
        # 记录事件历史
        self.event_history.append({
            'type': event_type,
            'data': data,
            'source': source,
            'timestamp': datetime.now()
        })
        
        # 保持历史记录大小
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # 通知监听者
        if event_type in self.listeners:
            for callback, priority in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"事件处理异常: {event_type}, {e}")
    
    def get_event_history(self):
        """获取事件历史 - 用于调试"""
        return self.event_history.copy()
```

## 📊 **优化后的文件结构**
```
# 拆解后的文件结构（基于现有架构）
src/main_window.py (150-200行，从4751行大幅精简)
src/ui/tab_manager.py (150-200行，新建)

# 模型层（扩展现有业务模型）
src/models/application_model.py (300-400行，新建)
src/models/detection_state.py (50-100行，新建或扩展现有status_manager.py)
src/models/event_types.py (50-100行，新建)

# 控制器层（新建）
src/controllers/main_detection_coordinator.py (200-300行)
src/controllers/dxf_view_controller.py (250-350行)
src/controllers/sidebar_controller.py (200-300行)
src/controllers/viewport_controller.py (300-400行)
src/controllers/detection_controller.py (250-350行)
src/controllers/realtime_controller.py (300-400行)
src/controllers/history_controller.py (250-350行)
src/controllers/report_controller.py (200-300行)

# 核心组件（使用现有架构）
src/core/application.py (包含ApplicationCore和EventBus，已存在)
src/core/dependency_injection.py (已存在)
src/managers/ui_state_manager.py (150-200行，新建)

# 现有业务组件（保持不变）
src/core_business/models/ (已存在，HoleData, HoleCollection等)
src/core_business/graphics/ (已存在，OptimizedGraphicsView等)
src/core_business/dxf_parser.py (已存在)
src/modules/ (已存在，各种功能模块)
```

## 🎯 **关键改进点**

1. **彻底拆分MainDetectionController**：拆分为4个专门的子控制器
2. **引入ApplicationModel**：统一管理数据状态，实现Single Source of Truth
3. **利用现有架构**：充分使用现有的ApplicationCore和EventBus
4. **规范事件总线**：基于现有EventBus实现，统一事件类型管理
5. **信号下沉**：每个控制器管理自己的信号，减少MainWindow的中心化
6. **职责明确**：每个类都有明确的单一职责
7. **可测试性**：每个组件都可以独立测试
8. **渐进式重构**：基于现有组件，避免大规模重写

## 🔧 **实施建议**

### **渐进式重构策略**
1. **第一阶段**：在MainWindow中集成现有ApplicationCore和EventBus
2. **第二阶段**：创建ApplicationModel，统一数据管理
3. **第三阶段**：创建控制器层，逐步提取业务逻辑
4. **第四阶段**：完成UI层分离，实现完整的MVC架构

### **依赖注入（Dependency Injection）的轻度自动化**
- **现状**：项目已有`src/core/dependency_injection.py`，包含完整的DI容器
- **建议**：利用现有的DI容器，通过装饰器和容器注册管理依赖
- **未来展望**：基于现有实现，进一步优化依赖管理

### **异步操作的处理**
- **潜在瓶颈**：DXF文件解析、检测逻辑等耗时操作可能阻塞UI线程
- **建议**：将耗时操作放到独立的工作线程（QThread）中执行
- **实现方式**：通过信号-槽机制，Worker可以安全地通知主线程更新UI

### **测试策略的具体化**
- **模型测试**：独立测试ApplicationModel，验证信号发射
- **控制器测试**：使用模拟对象（Mocking）测试控制器逻辑
- **集成测试**：验证关键控制器和模型的协同工作

## 🎯 **预期效果**
1. **代码可维护性**：从4751行拆分为多个150-400行的模块
2. **测试便利性**：每个控制器可以独立测试
3. **功能完整性**：所有原有功能保持不变
4. **界面一致性**：UI布局和交互逻辑完全一致
5. **扩展性**：新功能可以通过添加新控制器实现
6. **架构一致性**：充分利用现有ApplicationCore架构
7. **重构风险降低**：渐进式重构，避免大规模重写风险

这种设计确保了在保持UI和功能完全一致的前提下，实现了真正的模块化和可维护性。

---

**创建时间**: 2025-01-18  
**版本**: v2.1  
**状态**: 设计已更新，基于现有架构优化  
**更新内容**: 修正架构组件引用，整合现有ApplicationCore和EventBus