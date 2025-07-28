# PanoramaController 重构方案（修正版）

## 🔍 当前问题分析

`PanoramaController` 当前承担了过多职责，需要合理拆分，但**测试功能不应该独立成服务**。

## ✅ **正确的重构方案**

### 1. **PanoramaSyncService** - 状态同步服务
负责所有全景图的状态同步工作：

```python
class PanoramaSyncService:
    """全景图状态同步服务"""
    
    def __init__(self, event_bus: PanoramaEventBus):
        self.event_bus = event_bus
        self.sync_counter = 0
        self.error_count = 0
        
    def sync_hole_status(self, hole_id: str, status: HoleStatus):
        """同步孔位状态到所有全景图"""
        self.event_bus.publish(PanoramaEvent.HOLE_STATUS_CHANGED, {
            'hole_id': hole_id,
            'status': status
        })
        
    def sync_sector_highlight(self, sector: SectorQuadrant):
        """同步扇区高亮到所有全景图"""
        self.event_bus.publish(PanoramaEvent.SECTOR_HIGHLIGHTED, sector)
        
    def clear_highlights(self):
        """清除所有高亮"""
        self.event_bus.publish(PanoramaEvent.HIGHLIGHT_CLEARED)
```

### 2. **PanoramaEventHandler** - 事件处理器
处理全景图的交互事件：

```python
class PanoramaEventHandler:
    """全景图事件处理器"""
    
    sector_clicked = Signal(SectorQuadrant)
    
    def __init__(self, event_bus: PanoramaEventBus):
        self.event_bus = event_bus
        # 订阅全景图点击事件
        self.event_bus.subscribe(PanoramaEvent.SECTOR_CLICKED, self._on_sector_clicked)
        
    def _on_sector_clicked(self, event_data):
        """处理扇区点击事件"""
        sector = event_data.data
        self.sector_clicked.emit(sector)
```

### 3. **简化的PanoramaController** - 协调器
只负责协调和对外接口：

```python
class PanoramaController(QObject):
    """全景图协调控制器 - 简化版"""
    
    sector_clicked = Signal(SectorQuadrant)
    log_message = Signal(str)
    
    def __init__(self, panorama_container: PanoramaDIContainer, parent=None):
        super().__init__(parent)
        
        # 使用新的全景图包
        self.container = panorama_container
        self.event_bus = panorama_container.get_event_bus()
        
        # 创建专门的服务
        self.sync_service = PanoramaSyncService(self.event_bus)
        self.event_handler = PanoramaEventHandler(self.event_bus)
        
        # 连接信号
        self.event_handler.sector_clicked.connect(self.sector_clicked.emit)
        
    def sync_hole_status(self, hole_id: str, status: HoleStatus):
        """对外接口：同步孔位状态"""
        self.sync_service.sync_hole_status(hole_id, status)
        
    def highlight_sector(self, sector: SectorQuadrant):
        """对外接口：高亮扇区"""
        self.sync_service.sync_sector_highlight(sector)
        
    def clear_highlight(self):
        """对外接口：清除高亮"""
        self.sync_service.clear_highlights()
```

## 🧪 **测试功能的正确处理方式**

### ❌ **错误方式**：独立的测试服务
```python
# 不要这样做
class PanoramaTestService:
    def test_panorama_highlights(self):
        pass
```

### ✅ **正确方式**：几种更好的选择

#### 方案1：集成到主组件的调试接口
```python
class PanoramaController:
    def debug_panorama_system(self):
        """调试接口 - 仅在开发环境使用"""
        if not DEBUG_MODE:
            return
            
        # 获取所有全景图实例
        panorama_widgets = self.container.get_all_widgets()
        for widget in panorama_widgets:
            self._debug_widget_state(widget)
```

#### 方案2：开发工具类（推荐）
```python
class PanoramaDeveloperTools:
    """全景图开发工具 - 独立的开发辅助类"""
    
    def __init__(self, panorama_container: PanoramaDIContainer):
        self.container = panorama_container
        
    def diagnose_system(self):
        """诊断全景图系统状态"""
        # 检查数据模型
        data_model = self.container.get_data_model()
        print(f"数据模型状态: {len(data_model.get_holes())} 个孔位")
        
        # 检查事件总线
        event_bus = self.container.get_event_bus()
        print(f"事件总线状态: 正常")
        
    def test_all_highlights(self):
        """测试所有扇区高亮"""
        for sector in SectorQuadrant:
            print(f"测试高亮: {sector.value}")
            # 通过事件总线发送测试事件
            self.container.get_event_bus().publish(
                PanoramaEvent.SECTOR_HIGHLIGHTED, sector
            )
```

#### 方案3：单元测试（最佳实践）
```python
# 在 test_panorama_controller.py 中
class TestPanoramaController(unittest.TestCase):
    def setUp(self):
        self.container = PanoramaDIContainer()
        self.controller = PanoramaController(self.container)
        
    def test_highlight_functionality(self):
        """测试高亮功能"""
        # 创建测试数据
        test_holes = self._create_test_holes()
        self.container.get_data_model().load_holes(test_holes)
        
        # 测试高亮
        self.controller.highlight_sector(SectorQuadrant.FIRST)
        
        # 验证结果
        # ...
```

## 🎯 **推荐的最终方案**

### 主要组件：
1. **PanoramaSyncService** - 专门处理同步
2. **PanoramaEventHandler** - 专门处理事件
3. **简化的PanoramaController** - 只做协调

### 测试功能：
1. **开发环境**: 使用 `PanoramaDeveloperTools` 类
2. **生产环境**: 移除所有调试代码
3. **测试环境**: 使用标准的单元测试

### 在main_window.py中的使用：
```python
class MainWindow:
    def __init__(self):
        # 使用新的全景图包
        self.panorama_container = PanoramaDIContainer()
        self.sidebar_panorama = self.panorama_container.create_panorama_widget()
        
        # 使用重构后的控制器
        self.panorama_controller = PanoramaController(self.panorama_container)
        
        # 开发环境下可以使用调试工具
        if DEBUG_MODE:
            self.dev_tools = PanoramaDeveloperTools(self.panorama_container)
    
    def setup_shortcuts(self):
        # 开发快捷键
        if DEBUG_MODE:
            debug_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
            debug_shortcut.activated.connect(self.dev_tools.diagnose_system)
```

## 📈 **重构后的优势**

1. **职责清晰**: 每个类只负责一个明确的职责
2. **低耦合**: 通过事件总线通信，而不是直接依赖
3. **易测试**: 每个组件都可以独立测试
4. **易维护**: 调试代码分离，生产代码更清洁
5. **易扩展**: 可以轻松添加新的同步目标或事件类型

## 🚀 **实施步骤**

1. **第一步**: 创建 `PanoramaSyncService`
2. **第二步**: 创建 `PanoramaEventHandler` 
3. **第三步**: 重构 `PanoramaController` 为协调器
4. **第四步**: 创建 `PanoramaDeveloperTools`（可选）
5. **第五步**: 更新 `main_window.py` 使用新控制器
6. **第六步**: 移除旧的 `PanoramaController`

这样的重构方案更加合理，避免了测试功能独立成服务的设计问题。