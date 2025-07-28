# 统一缩放控制流程图

## 改进前后对比

### 改进前（两次缩放）
```mermaid
graph TB
    A[数据加载] --> B[load_holes]
    B --> C{disable_auto_fit?}
    C -->|False| D[第一次缩放: fit_to_window_width]
    C -->|True| E[跳过缩放]
    D --> F[隐藏所有孔位]
    E --> F
    F --> G[切换扇形]
    G --> H[第二次缩放: delayed_fit]
    
    style D fill:#FFE0B2,stroke:#FF6F00
    style H fill:#FFE0B2,stroke:#FF6F00
```

### 改进后（统一缩放）
```mermaid
graph TB
    A[数据加载] --> B[load_holes<br/>不执行缩放]
    B --> C[隐藏所有孔位]
    C --> D[延迟200ms]
    D --> E[switch_to_sector]
    E --> F[显示扇形孔位]
    F --> G[_unified_zoom_to_items]
    
    style G fill:#C8E6C9,stroke:#388E3C
```

## _unified_zoom_to_items 函数内部流程

```mermaid
graph TB
    A[_unified_zoom_to_items] --> B{delay_ms > 0?}
    B -->|是| C[QTimer.singleShot延迟执行]
    B -->|否| D[立即执行do_zoom]
    C --> D
    
    D --> E{item_ids是否为None?}
    E -->|是| F[_calculate_visible_bounds<br/>计算所有可见项边界]
    E -->|否| G[_calculate_items_bounds<br/>计算指定项边界]
    
    F --> H{边界有效?}
    G --> H
    
    H -->|是| I[计算扩展边界<br/>margin_factor = 1.1]
    H -->|否| J[结束]
    
    I --> K[expanded_bounds计算<br/>x - width * 0.05<br/>y - height * 0.05<br/>width * 1.1<br/>height * 1.1]
    
    K --> L[fitInView<br/>Qt.KeepAspectRatio]
    
    style A fill:#C8E6C9,stroke:#388E3C
    style D fill:#E1F5FE,stroke:#0288D1
    style I fill:#FFF3E0,stroke:#F57C00
    style L fill:#F3E5F5,stroke:#7B1FA2
```

## 统一缩放函数详解

```python
def _unified_zoom_to_items(self, item_ids: Optional[List[str]] = None, delay_ms: int = 50):
    """
    统一的缩放方法
    
    参数：
    - item_ids: 指定要显示的项目ID列表
              None = 计算所有可见项
              List[str] = 只计算指定ID的项
    - delay_ms: 延迟执行时间
              > 0 = 使用QTimer延迟执行
              = 0 = 立即执行
    
    内部流程：
    1. 判断是否延迟执行
    2. 计算边界（根据item_ids参数选择计算方式）
    3. 添加10%边距（margin_factor = 1.1）
    4. 执行fitInView保持宽高比
    """
```

## 主要改进点

### 1. 消除重复缩放
- **之前**：数据加载时可能缩放一次，切换扇形时又缩放一次
- **现在**：只在需要显示内容时执行一次缩放

### 2. 参数统一管理
| 参数 | 值 | 说明 |
|------|-----|------|
| delay_ms | 50 | 统一的延迟时间 |
| margin_factor | 1.1 | 统一的边距系数 |
| max_auto_scale | 1.5 | 最大自动缩放（在graphics_view中设置） |

### 3. 使用场景

```python
# 场景1：切换扇形时（正常流程）
def switch_to_sector(self, sector):
    # 获取扇形孔位ID
    sector_hole_ids = self.sector_distributor.get_sector_data(sector).hole_ids
    # 设置可见性
    for hole_id, hole_item in self.graphics_view.hole_items.items():
        hole_item.setVisible(hole_id in sector_hole_ids)
    # 统一缩放到扇形内容
    self._unified_zoom_to_items(list(sector_hole_ids), delay_ms=50)

# 场景2：显示所有可见项（全景模式）
def show_all_visible_items(self):
    # 不指定item_ids，自动计算所有可见项
    self._unified_zoom_to_items(None, delay_ms=50)

# 场景3：立即缩放（响应用户操作）
def zoom_to_selection(self, selected_ids):
    # 立即执行，不延迟
    self._unified_zoom_to_items(selected_ids, delay_ms=0)

# 场景4：数据更新后的自适应
def on_data_updated(self):
    # 使用较长延迟，等待UI完全更新
    self._unified_zoom_to_items(None, delay_ms=100)
```

### 4. 关键时间节点

| 时间点 | 操作 | 说明 |
|--------|------|------|
| 0ms | load_holes | 加载数据，不缩放 |
| 0ms | 隐藏所有孔位 | 防止显示混乱 |
| 200ms | switch_to_sector | 自动切换到扇形1 |
| 200ms | 设置孔位可见性 | 只显示扇形1的孔位 |
| 250ms | _unified_zoom_to_items | 延迟50ms执行缩放 |
| 250ms | fitInView | 实际执行缩放操作 |

## 性能优势

1. **减少计算次数**
   - 从可能的2次缩放减少到1次
   - 避免了不必要的视图变换

2. **更好的用户体验**
   - 消除了"先变大后适应"的视觉跳变
   - 统一的延迟时间提供一致的体验

3. **代码维护性**
   - 所有缩放参数集中管理
   - 易于调整和优化

## 完整调用时序图

```mermaid
sequenceDiagram
    participant User
    participant Display as DynamicSectorDisplay
    participant View as GraphicsView
    participant Zoom as _unified_zoom_to_items
    
    rect rgb(230, 240, 255)
        Note over User,View: 数据加载阶段
        User->>Display: 加载数据
        Display->>View: load_holes()
        Note over View: disable_auto_fit=True<br/>不执行缩放
        Display->>Display: 隐藏所有孔位
    end
    
    rect rgb(230, 255, 230)
        Note over User,View: 扇形切换阶段（延迟200ms后）
        Display->>Display: switch_to_sector(SECTOR_1)
        Display->>Display: 设置孔位可见性
        Display->>Zoom: _unified_zoom_to_items(sector_hole_ids, 50ms)
    end
    
    rect rgb(255, 240, 230)
        Note over User,View: 缩放执行阶段（延迟50ms后）
        Zoom->>Zoom: do_zoom()执行
        Zoom->>Zoom: 计算指定孔位边界
        Zoom->>Zoom: 添加10%边距
        Zoom->>View: fitInView(expanded_bounds, KeepAspectRatio)
        Note over View: 执行唯一的缩放操作
    end
```

## 数据流向图

```mermaid
graph LR
    A[HoleCollection] --> B[load_holes]
    B --> C[创建hole_items]
    C --> D[setVisible False]
    
    D --> E[switch_to_sector]
    E --> F[获取扇形孔位ID]
    F --> G[设置可见性]
    
    G --> H[_unified_zoom_to_items]
    H --> I[_calculate_items_bounds]
    I --> J[计算场景边界]
    J --> K[扩展边界+10%]
    K --> L[fitInView]
    
    style A fill:#E8F4FD,stroke:#1976D2
    style H fill:#C8E6C9,stroke:#388E3C
    style L fill:#F3E5F5,stroke:#7B1FA2
```

## 建议的进一步优化

1. **可配置的缩放参数**
```python
class ZoomConfig:
    delay_ms: int = 50
    margin_factor: float = 1.1
    max_scale: float = 1.5
    animation_enabled: bool = False
```

2. **缩放策略模式**
```python
class ZoomStrategy:
    def calculate_bounds(self, items): pass
    def apply_margin(self, bounds): pass
    def execute_zoom(self, view, bounds): pass
```

3. **缩放历史记录**
- 记录缩放操作历史
- 支持撤销/重做功能