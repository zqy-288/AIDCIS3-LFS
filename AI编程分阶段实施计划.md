# 🚀 AIDCIS3-LFS 主检测视图功能恢复 - AI编程分阶段实施计划

## 📋 计划概述

本计划基于《主检测视图功能差距分析报告》，将功能恢复工作分为4个可并行开发的阶段。每个阶段都有独立的AI编程提示词，确保多个AI助手可以同时工作而不产生冲突。

### **阶段划分原则**
1. **独立性**: 每个阶段的功能相对独立，减少依赖
2. **并行性**: 不同阶段可以同时开发
3. **集成性**: 预定义清晰的接口规范
4. **测试性**: 每个阶段都有独立的测试验证

---

## 📊 阶段概览

| 阶段 | 名称 | 核心功能 | 预计工时 | 依赖关系 |
|------|------|---------|---------|---------|
| **阶段1** | UI布局增强 | 工具栏、面板布局、基础组件 | 2-3天 | 无 |
| **阶段2** | 核心可视化 | 全景预览、动态扇形显示 | 3-4天 | 阶段1的布局框架 |
| **阶段3** | 业务逻辑 | 产品管理、批次管理、进度跟踪 | 3-4天 | 阶段1的UI组件 |
| **阶段4** | 高级功能 | 模拟系统、导航功能、性能优化 | 2-3天 | 阶段2和3 |

---

## 🎯 阶段1：UI布局增强

### **目标**
恢复源版本的完整UI布局结构，包括顶部工具栏和增强的三栏布局。

### **AI编程提示词 - 阶段1**

```markdown
## 任务：UI布局增强实现

### 背景
当前AIDCIS3-LFS项目的主检测视图缺少完整的UI布局。需要在保持现有模块化架构的基础上，恢复源版本的布局结构。

### 具体需求

1. **添加顶部工具栏** (创建新文件: src/modules/ui_components/toolbar.py)
   - 产品型号选择按钮 (140x45px，字体11pt)
   - 搜索框和搜索按钮（搜索框220px宽，35px高）
   - 视图过滤下拉框（全部孔位/待检孔位/合格孔位/异常孔位）
   - 使用QHBoxLayout布局，高度限制70px
   
2. **增强左侧面板** (修改文件: src/modules/main_detection_view.py)
   - 调整宽度从300px到380px
   - 添加批次进度组件位置（QGroupBox预留）
   - 添加时间跟踪标签（检测时间、预计用时）
   - 添加完成率和合格率标签
   - 在文件信息组添加文件大小和加载时间标签
   - 预留全景预览位置（360x420px的QWidget占位符）
   - 预留扇形统计位置（QLabel占位符，最小高度120px）

3. **增强中间面板** (修改文件: src/modules/main_detection_view.py)
   - 添加层级化视图控制框架（QFrame，60px高）
   - 创建宏观/微观视图切换按钮（使用emoji图标）
   - 添加方向统一按钮
   - 添加视图状态指示器标签
   - 保留现有WorkpieceDiagram的位置

4. **增强右侧面板** (修改文件: src/modules/main_detection_view.py)
   - 添加模拟功能组（QGroupBox预留）
   - 添加导航功能组（实时监控、历史数据按钮）
   - 添加文件操作组（加载DXF、导出数据按钮）
   - 扩展视图控制按钮到6个

### 技术要求

1. **代码结构**
   ```python
   # toolbar.py 结构
   class MainToolbar(QWidget):
       # 信号定义
       product_selected = Signal(str)
       search_requested = Signal(str)
       filter_changed = Signal(str)
       
       def __init__(self):
           # 初始化UI组件
           
       def setup_ui(self):
           # 创建工具栏布局
   ```

2. **集成点**
   - MainDetectionView需要添加toolbar属性
   - 在setup_ui()开始处集成工具栏
   - 使用信号槽机制连接工具栏事件

3. **样式要求**
   - 使用现有主题系统的样式类
   - 按钮使用setProperty("class", "ActionButton")
   - 保持与现有UI风格一致

### 测试验证

1. **布局测试**
   - 工具栏高度不超过70px
   - 左侧面板宽度正确为380px
   - 所有预留位置显示占位符

2. **功能测试**
   - 工具栏按钮点击信号正确发出
   - 视图切换按钮状态互斥
   - 搜索框回车触发搜索信号

### 输出交付物

1. src/modules/ui_components/toolbar.py - 新建工具栏组件
2. src/modules/main_detection_view.py - 修改后的主视图
3. 截图展示增强后的UI布局

### 错误处理

- 所有新增组件需要try-except包装
- 缺失依赖时显示友好的占位符
- 记录详细日志到logger
```

---

## 🎨 阶段2：核心可视化组件

### **目标**
实现全景预览和动态扇形显示两个核心可视化组件。

### **AI编程提示词 - 阶段2**

```markdown
## 任务：核心可视化组件实现

### 背景
需要恢复AIDCIS3-LFS的两个核心可视化组件：全景预览和动态扇形显示。这些组件是用户导航和检测区域管理的核心。

### 具体需求

1. **全景预览组件** (创建文件: src/modules/ui_components/panorama_widget.py)
   - 尺寸：360x420px固定大小
   - 显示完整工件的缩略图
   - 扇形区域高亮显示
   - 点击扇形触发sector_clicked信号
   - 当前选中扇形用蓝色边框标记
   
2. **动态扇形显示组件** (创建文件: src/modules/ui_components/dynamic_sector_widget.py)
   - 替换现有的WorkpieceDiagram
   - 支持扇形区域划分（8个扇形）
   - 每个扇形独立的检测状态
   - 支持缩放和平移
   - 扇形点击交互
   
3. **扇形管理适配器** (创建文件: src/modules/sector_manager_adapter.py)
   - 管理扇形状态和数据
   - 扇形进度计算
   - 扇形统计信息生成
   - 与可视化组件的数据绑定

### 技术实现要点

1. **全景预览实现**
   ```python
   class CompletePanoramaWidget(QWidget):
       sector_clicked = Signal(int)  # 扇形ID
       
       def __init__(self):
           self.sectors = {}  # 扇形数据
           self.selected_sector = None
           
       def paintEvent(self, event):
           # 绘制工件轮廓
           # 绘制扇形分割线
           # 高亮选中扇形
           
       def mousePressEvent(self, event):
           # 检测点击的扇形
           # 发出sector_clicked信号
   ```

2. **动态扇形显示实现**
   ```python
   class DynamicSectorDisplayWidget(QWidget):
       sector_changed = Signal(int)
       hole_clicked = Signal(str)
       
       def __init__(self):
           self.graphics_view = QGraphicsView()
           self.graphics_scene = QGraphicsScene()
           self.sector_items = {}  # 扇形图形项
           
       def load_workpiece_data(self, hole_collection):
           # 加载孔位数据
           # 创建扇形划分
           # 渲染孔位和扇形
   ```

3. **扇形管理器接口**
   ```python
   class SectorManagerAdapter:
       sector_progress_updated = Signal(int, float)
       overall_progress_updated = Signal(float)
       
       def get_sector_statistics(self, sector_id):
           # 返回扇形统计信息
           
       def update_hole_status(self, hole_id, status):
           # 更新孔位状态并重算扇形进度
   ```

### 依赖和接口

1. **依赖阶段1的布局**
   - 全景预览放置在左侧面板预留位置
   - 动态扇形替换中间面板的WorkpieceDiagram

2. **数据接口**
   - 使用现有的HoleCollection数据结构
   - 扇形ID使用0-7的整数
   - 状态使用HoleStatus枚举

3. **信号接口**
   - sector_clicked(int) - 扇形点击
   - sector_changed(int) - 扇形切换
   - hole_clicked(str) - 孔位点击

### 测试验证

1. **视觉测试**
   - 全景预览正确显示8个扇形
   - 扇形颜色反映检测进度
   - 选中扇形有明显标记

2. **交互测试**
   - 点击扇形正确触发信号
   - 缩放平移功能正常
   - 扇形统计信息准确

### 输出交付物

1. src/modules/ui_components/panorama_widget.py
2. src/modules/ui_components/dynamic_sector_widget.py
3. src/modules/sector_manager_adapter.py
4. 测试脚本展示组件功能
```

---

## 💼 阶段3：业务逻辑增强

### **目标**
实现产品管理、批次管理和增强的进度跟踪系统。

### **AI编程提示词 - 阶段3**

```markdown
## 任务：业务逻辑功能实现

### 背景
需要实现AIDCIS3-LFS的核心业务逻辑功能，包括产品管理、批次管理和进度跟踪。

### 具体需求

1. **产品管理系统** (创建文件: src/modules/product_manager.py)
   - 产品型号数据结构（名称、DXF路径、孔位配置）
   - 产品选择对话框
   - 产品配置加载逻辑
   - 与主界面的集成接口

2. **批次管理系统** (创建文件: src/modules/batch_manager.py)
   - 批次数据结构（批次ID、孔位列表、进度）
   - 批次创建和管理
   - 批次进度跟踪
   - 批次切换逻辑

3. **进度跟踪增强** (修改文件: src/modules/main_detection_view.py)
   - 检测时间计时器
   - 预计剩余时间计算
   - 完成率实时更新
   - 合格率统计计算
   - 批次进度显示

4. **时间管理器** (创建文件: src/modules/time_tracker.py)
   - 检测开始/结束时间记录
   - 平均检测速度计算
   - 剩余时间估算算法

### 技术实现要点

1. **产品管理实现**
   ```python
   class ProductManager:
       def __init__(self):
           self.products = self.load_products()
           
       def load_products(self):
           # 从配置文件加载产品列表
           
       def get_product_dxf_path(self, product_name):
           # 返回产品的DXF文件路径
           
   class ProductSelectionDialog(QDialog):
       product_selected = Signal(str)
       
       def __init__(self, product_manager):
           # 创建产品选择界面
   ```

2. **批次管理实现**
   ```python
   class BatchManager:
       batch_started = Signal(str)
       batch_completed = Signal(str)
       batch_progress_updated = Signal(str, float)
       
       def create_batch(self, holes, batch_size=10):
           # 创建检测批次
           
       def update_batch_progress(self, batch_id, completed_count):
           # 更新批次进度
   ```

3. **进度跟踪实现**
   ```python
   class ProgressTracker:
       def __init__(self):
           self.start_time = None
           self.completed_count = 0
           self.total_count = 0
           
       def calculate_completion_rate(self):
           # 计算完成率
           
       def calculate_qualification_rate(self, qualified_count):
           # 计算合格率
           
       def estimate_remaining_time(self):
           # 估算剩余时间
   ```

### 集成要求

1. **与UI组件集成**
   - 产品选择按钮连接ProductSelectionDialog
   - 批次进度更新左侧面板显示
   - 时间信息实时更新标签

2. **与现有系统集成**
   - 使用EventBus发布批次事件
   - 通过DependencyContainer注入服务
   - 保持与现有信号槽的兼容

3. **数据持久化**
   - 产品配置保存在config/products.json
   - 批次历史记录保存
   - 进度数据定期保存

### 测试验证

1. **功能测试**
   - 产品选择后自动加载DXF
   - 批次创建正确分组孔位
   - 进度计算准确无误

2. **性能测试**
   - 大批量孔位处理流畅
   - 进度更新不阻塞UI
   - 内存使用合理

### 输出交付物

1. src/modules/product_manager.py
2. src/modules/batch_manager.py
3. src/modules/time_tracker.py
4. config/products.json 示例配置
5. 集成测试脚本
```

---

## 🚀 阶段4：高级功能与优化

### **目标**
实现模拟系统、导航功能和整体性能优化。

### **AI编程提示词 - 阶段4**

```markdown
## 任务：高级功能实现与系统优化

### 背景
完成基础功能后，需要实现高级功能并进行整体优化，提升用户体验。

### 具体需求

1. **模拟系统** (创建文件: src/modules/simulation_system.py)
   - 检测进度模拟
   - 随机故障模拟
   - 批次完成模拟
   - 可配置的模拟参数

2. **导航功能** (修改文件: src/modules/main_detection_view.py)
   - 快速跳转到实时监控
   - 快速跳转到历史数据
   - 带参数的页面切换
   - 返回按钮逻辑

3. **文件操作增强** (创建文件: src/modules/file_operations.py)
   - DXF文件拖放支持
   - 批量文件导入
   - 检测结果导出
   - 报告生成接口

4. **性能优化** (多文件修改)
   - 大数据量渲染优化
   - 内存使用优化
   - 更新频率优化
   - 异步操作实现

### 技术实现要点

1. **模拟系统实现**
   ```python
   class SimulationSystem:
       simulation_started = Signal()
       simulation_stopped = Signal()
       progress_updated = Signal(float)
       
       def __init__(self):
           self.timer = QTimer()
           self.simulation_speed = 1.0
           
       def start_simulation(self, total_holes):
           # 开始模拟检测过程
           
       def simulate_detection_step(self):
           # 模拟单步检测
           # 随机生成检测结果
   ```

2. **导航系统实现**
   ```python
   class NavigationManager:
       def navigate_to_realtime(self, hole_id=None):
           # 切换到实时监控页面
           # 传递hole_id参数
           
       def navigate_to_history(self, batch_id=None):
           # 切换到历史数据页面
           # 传递batch_id参数
   ```

3. **性能优化策略**
   ```python
   # 使用QGraphicsScene的层级优化
   class OptimizedGraphicsScene(QGraphicsScene):
       def __init__(self):
           self.enable_lod = True  # Level of Detail
           self.cache_mode = True
           
   # 使用工作线程处理耗时操作
   class DataProcessingThread(QThread):
       def run(self):
           # 异步处理数据
   ```

### 集成和优化要求

1. **系统集成**
   - 所有新功能通过信号槽集成
   - 保持模块间的松耦合
   - 统一的错误处理机制

2. **性能目标**
   - 支持10000+孔位流畅显示
   - 界面响应时间<100ms
   - 内存占用<500MB

3. **用户体验优化**
   - 添加操作进度提示
   - 优化动画过渡效果
   - 改进错误提示信息

### 测试验证

1. **功能测试**
   - 模拟系统各项参数可调
   - 导航跳转带参数正确
   - 文件操作支持多种格式

2. **性能测试**
   - 使用大数据集测试渲染
   - 监控内存使用情况
   - 测试响应时间

3. **集成测试**
   - 所有模块协同工作
   - 无内存泄漏
   - 错误处理完善

### 输出交付物

1. src/modules/simulation_system.py
2. src/modules/file_operations.py
3. 性能优化后的各组件
4. 完整集成测试报告
5. 用户操作手册
```

---

## 🔧 集成规范

### **接口定义**

```python
# 统一的组件接口
class IDetectionComponent:
    """所有检测组件的基础接口"""
    
    def initialize(self):
        """初始化组件"""
        pass
        
    def cleanup(self):
        """清理资源"""
        pass
        
    def get_status(self):
        """获取组件状态"""
        pass
```

### **信号规范**

```python
# 统一的信号命名规范
# 格式: <动作>_<对象>
hole_clicked = Signal(str)  # 孔位ID
sector_selected = Signal(int)  # 扇形ID
batch_completed = Signal(str)  # 批次ID
progress_updated = Signal(float)  # 进度百分比
```

### **数据格式**

```python
# 统一的数据交换格式
{
    "hole_data": {
        "id": "H001",
        "position": {"x": 100, "y": 200},
        "status": "pending",
        "sector": 3
    },
    "batch_data": {
        "id": "BATCH_001",
        "holes": ["H001", "H002"],
        "progress": 0.5
    }
}
```

---

## 📝 实施注意事项

### **并行开发指南**

1. **代码隔离**
   - 每个阶段在独立的分支开发
   - 避免修改其他阶段的核心文件
   - 通过接口而非直接调用通信

2. **测试先行**
   - 先编写单元测试
   - 使用模拟数据开发
   - 确保接口稳定后再集成

3. **文档同步**
   - 每个组件都要有docstring
   - 更新接口变更到文档
   - 记录已知问题和限制

### **风险管理**

1. **技术风险**
   - Qt版本兼容性问题
   - 性能瓶颈风险
   - 第三方库依赖

2. **缓解措施**
   - 使用虚拟环境隔离
   - 定期性能测试
   - 最小化外部依赖

---

## 🎯 预期成果

### **功能恢复度**
- 阶段1完成: 60% UI结构恢复
- 阶段2完成: 80% 可视化功能恢复
- 阶段3完成: 90% 业务功能恢复
- 阶段4完成: 100% 完整功能+优化

### **质量目标**
- 代码覆盖率 > 80%
- 响应时间 < 100ms
- 零关键bug

### **交付时间表**
- 总工期: 10-14天
- 每日进度汇报
- 每阶段演示验收

---

*计划制定时间: 2025-07-19*  
*基于: 主检测视图功能差距分析报告*  
*目标: 100%功能恢复+架构优化*