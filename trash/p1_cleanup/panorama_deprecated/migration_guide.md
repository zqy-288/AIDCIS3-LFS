# 全景图组件迁移指南

## 一、迁移概述

将原有的 `CompletePanoramaWidget` 迁移到新的组件架构，实现高内聚低耦合的设计。

## 二、主要变化

### 1. 组件拆分
- **原来**：所有功能在一个类中
- **现在**：拆分为8个独立组件，每个组件单一职责

### 2. 依赖管理
- **原来**：直接创建和管理所有依赖
- **现在**：使用依赖注入容器统一管理

### 3. 通信方式
- **原来**：组件间直接调用
- **现在**：通过事件总线解耦通信

## 三、代码迁移示例

### 1. 创建全景图组件

**原代码**：
```python
# 在 main_window.py 中
self.sidebar_panorama = CompletePanoramaWidget()
self.sidebar_panorama.setFixedSize(350, 350)
```

**新代码**：
```python
from src.core_business.graphics.panorama import PanoramaDIContainer

# 在 main_window.py 中
self.panorama_container = PanoramaDIContainer()
self.sidebar_panorama = self.panorama_container.create_panorama_widget()
self.sidebar_panorama.setFixedSize(350, 350)
```

### 2. 加载数据

**原代码**：
```python
self.sidebar_panorama.load_hole_collection(hole_collection)
```

**新代码**：
```python
# 相同的接口，内部实现已优化
self.sidebar_panorama.load_hole_collection(hole_collection)
```

### 3. 更新孔位状态

**原代码**：
```python
self.sidebar_panorama.update_hole_status(hole_id, status)
```

**新代码**：
```python
# 相同的接口，但现在支持批量优化
self.sidebar_panorama.update_hole_status(hole_id, status)
```

### 4. 扇区高亮

**原代码**：
```python
self.sidebar_panorama.highlight_sector(SectorQuadrant.FIRST)
self.sidebar_panorama.clear_sector_highlight()
```

**新代码**：
```python
# 接口保持不变
self.sidebar_panorama.highlight_sector(SectorQuadrant.FIRST)
self.sidebar_panorama.clear_sector_highlight()
```

### 5. 事件处理

**原代码**：
```python
self.sidebar_panorama.sector_clicked.connect(self.on_sector_clicked)
```

**新代码**：
```python
# 信号连接方式不变
self.sidebar_panorama.sector_clicked.connect(self.on_sector_clicked)

# 也可以通过事件总线订阅
event_bus = self.panorama_container.get_event_bus()
event_bus.subscribe(PanoramaEvent.SECTOR_CLICKED, self.on_sector_event)
```

## 四、高级用法

### 1. 自定义组件

可以替换默认组件实现：

```python
from src.core_business.graphics.panorama import IPanoramaRenderer

class CustomRenderer(IPanoramaRenderer):
    def render_holes(self, holes, scene, hole_size):
        # 自定义渲染逻辑
        pass
```

### 2. 扩展事件

添加自定义事件：

```python
# 扩展事件类型
class CustomPanoramaEvent(Enum):
    CUSTOM_ACTION = "custom_action"

# 发布事件
event_bus.publish(CustomPanoramaEvent.CUSTOM_ACTION, data)
```

### 3. 单元测试

每个组件可独立测试：

```python
def test_geometry_calculator():
    calculator = PanoramaGeometryCalculator()
    holes = create_test_holes()
    center = calculator.calculate_center(holes)
    assert center.x() == expected_x
    assert center.y() == expected_y
```

## 五、性能优化

### 1. 批量更新
新架构自动批量处理状态更新，减少重绘次数。

### 2. 事件去抖
高亮操作自动去抖，避免频繁更新。

### 3. 内存管理
通过依赖注入容器统一管理生命周期。

## 六、注意事项

1. **保持接口兼容**：公共API保持不变，确保平滑迁移
2. **逐步迁移**：可以先使用适配器模式，逐步替换
3. **测试覆盖**：迁移前后进行充分的回归测试
4. **性能监控**：监控迁移后的性能指标

## 七、迁移检查清单

- [ ] 替换 CompletePanoramaWidget 导入
- [ ] 使用 DI 容器创建组件
- [ ] 更新事件处理代码
- [ ] 移除直接依赖
- [ ] 添加单元测试
- [ ] 性能测试
- [ ] 集成测试
- [ ] 文档更新