# AIDCIS2 组件整合清单

**项目**: 将AIDCIS2组件整合到现有上位机软件项目中  
**目标**: 替换现有的MainDetectionView，提供更强大的一级界面功能  
**创建时间**: 2025-07-07  

## 整合概述

本清单将AIDCIS2组件整合工作分解为最小可开发单元（Smallest Development Unit），确保每个单元都是独立、可测试、可验证的工作项。

### 整合策略
- **替换策略**: 用AIDCIS2的MainWindow替换现有的MainDetectionView
- **保留策略**: 保留现有的RealtimeChart、HistoryViewer、AnnotationTool等二级和三级界面
- **集成策略**: 通过信号槽机制实现新旧组件间的通信

## 第一阶段：环境准备与依赖管理

### SDU-001: 依赖项分析与合并
**描述**: 分析两个项目的依赖差异，制定合并策略
**具体任务**:
- [ ] 对比主项目requirements.txt与AIDCIS2/requirements.txt
- [ ] 识别版本冲突（PySide6: 6.5.0+ vs 6.9.1, numpy: 1.24.0+ vs 2.0.2）
- [ ] 制定依赖升级计划
- [ ] 更新主项目requirements.txt

### SDU-002: 新依赖项安装
**描述**: 安装AIDCIS2特有的依赖包
**具体任务**:
- [ ] 添加ezdxf==1.4.2到主项目依赖
- [ ] 添加pytest==8.4.1和pytest-qt==4.5.0（用于测试）
- [ ] 验证所有依赖包兼容性

### SDU-003: 目录结构调整
**描述**: 为AIDCIS2组件创建合适的目录结构
**具体任务**:
- [ ] 在主项目根目录创建aidcis2/目录
- [ ] 复制AIDCIS2/src/目录内容到aidcis2/
- [ ] 调整Python路径配置以支持新模块导入

## 第二阶段：核心组件移植

### SDU-004: DXF解析器集成
**描述**: 将AIDCIS2的DXF解析功能集成到主项目
**具体任务**:
- [ ] 复制src/dxf_parser.py到aidcis2/dxf_parser.py
- [ ] 修改导入路径以适应主项目结构
- [ ] 在main.py中添加DXF解析器的导入

### SDU-005: 数据模型整合
**描述**: 整合AIDCIS2的孔位数据模型与现有数据库模型
**具体任务**:
- [ ] 复制src/models/hole_data.py到aidcis2/models/
- [ ] 复制src/models/status_manager.py到aidcis2/models/
- [ ] 分析HoleData与现有Hole模型的兼容性
- [ ] 创建数据转换适配器

### SDU-006: 图形组件移植
**描述**: 移植AIDCIS2的优化图形视图组件
**具体任务**:
- [ ] 复制src/graphics/目录到aidcis2/graphics/
- [ ] 修改OptimizedGraphicsView的导入依赖
- [ ] 调整HoleGraphicsItem的渲染逻辑

### SDU-007: 搜索引擎集成
**描述**: 集成AIDCIS2的搜索功能
**具体任务**:
- [ ] 复制src/search/目录到aidcis2/search/
- [ ] 修改SearchEngine的导入路径
- [ ] 集成搜索功能到主界面

## 第三阶段：主界面替换

### SDU-008: 新主界面组件准备
**描述**: 准备AIDCIS2的主界面组件用于替换
**具体任务**:
- [ ] 复制src/ui/main_window.py到aidcis2/ui/main_window.py
- [ ] 重命名类名为AIDCIS2MainWindow避免冲突
- [ ] 移除AIDCIS2特有的硬件通信组件

### SDU-009: UI组件移植
**描述**: 移植AIDCIS2的UI组件
**具体任务**:
- [ ] 复制src/ui/目录下所有组件到aidcis2/ui/
- [ ] 修改所有UI组件的导入路径
- [ ] 调整组件尺寸以适应主项目布局

### SDU-010: 主窗口导入路径修改
**描述**: 修改main_window.py中的导入语句
**具体任务**:
- [ ] 将`from modules.main_detection_view import MainDetectionView`替换为`from aidcis2.ui.main_window import AIDCIS2MainWindow`
- [ ] 更新变量名：`self.main_detection_tab = AIDCIS2MainWindow()`
- [ ] 修改选项卡标题为"主检测视图 (AIDCIS2)"

## 第四阶段：信号槽连接

### SDU-011: 导航信号适配
**描述**: 适配AIDCIS2主界面的导航信号到现有系统
**具体任务**:
- [ ] 在AIDCIS2MainWindow中添加navigate_to_realtime信号
- [ ] 在AIDCIS2MainWindow中添加navigate_to_history信号
- [ ] 修改孔位点击事件以发射正确的导航信号

### SDU-012: 信号连接更新
**描述**: 更新main_window.py中的信号连接
**具体任务**:
- [ ] 连接`self.main_detection_tab.navigate_to_realtime.connect(self.navigate_to_realtime)`
- [ ] 连接`self.main_detection_tab.navigate_to_history.connect(self.navigate_to_history)`
- [ ] 测试信号槽连接的正确性

### SDU-013: 数据传递接口
**描述**: 建立AIDCIS2与现有组件间的数据传递接口
**具体任务**:
- [ ] 创建数据适配器类DataAdapter
- [ ] 实现HoleData到现有数据模型的转换
- [ ] 实现孔位状态同步机制

## 第五阶段：配置与日志系统

### SDU-014: 配置管理集成
**描述**: 集成AIDCIS2的配置管理系统
**具体任务**:
- [ ] 复制src/config/目录到aidcis2/config/
- [ ] 修改ConfigManager以适应主项目配置结构
- [ ] 合并配置文件格式

### SDU-015: 日志系统集成
**描述**: 集成AIDCIS2的日志系统
**具体任务**:
- [ ] 复制src/log_system/目录到aidcis2/log_system/
- [ ] 配置日志输出路径
- [ ] 集成到主项目的日志体系

### SDU-016: 性能监控集成
**描述**: 集成AIDCIS2的性能监控功能
**具体任务**:
- [ ] 复制src/performance/目录到aidcis2/performance/
- [ ] 配置性能监控参数
- [ ] 集成到主窗口状态栏

## 第六阶段：功能验证与优化

### SDU-017: DXF文件加载测试
**描述**: 验证DXF文件加载功能
**具体任务**:
- [ ] 测试加载AIDCIS2/data/东重管板.dxf文件
- [ ] 验证孔位数据解析正确性
- [ ] 测试大型DXF文件的加载性能

### SDU-018: 界面响应性测试
**描述**: 测试新界面的响应性和交互功能
**具体任务**:
- [ ] 测试孔位点击响应
- [ ] 测试搜索功能
- [ ] 测试界面缩放和导航

### SDU-019: 导航功能验证
**描述**: 验证从新主界面到二级界面的导航功能
**具体任务**:
- [ ] 测试点击孔位跳转到实时监控
- [ ] 测试点击孔位跳转到历史数据
- [ ] 验证孔位ID正确传递

### SDU-020: 数据同步验证
**描述**: 验证新旧组件间的数据同步
**具体任务**:
- [ ] 测试孔位状态更新同步
- [ ] 测试检测数据在各界面间的一致性
- [ ] 验证数据库操作的正确性

## 第七阶段：清理与优化

### SDU-021: 旧代码清理
**描述**: 清理不再使用的旧代码
**具体任务**:
- [ ] 备份原始modules/main_detection_view.py
- [ ] 移除对旧MainDetectionView的引用
- [ ] 清理未使用的导入语句

### SDU-022: 文档更新
**描述**: 更新项目文档以反映新的架构
**具体任务**:
- [ ] 更新README.md中的项目结构说明
- [ ] 更新架构图以包含AIDCIS2组件
- [ ] 创建AIDCIS2集成使用指南

### SDU-023: 最终验证
**描述**: 进行完整的系统验证
**具体任务**:
- [ ] 执行完整的用户工作流测试
- [ ] 验证所有功能模块正常工作
- [ ] 进行性能基准测试
- [ ] 确认无内存泄漏或资源问题

## 风险评估与缓解策略

### 高风险项目
1. **依赖版本冲突** (SDU-001, SDU-002)
   - 缓解策略：创建虚拟环境进行隔离测试
   
2. **信号槽连接失败** (SDU-011, SDU-012)
   - 缓解策略：创建详细的信号槽测试用例

3. **性能下降** (SDU-017, SDU-018)
   - 缓解策略：建立性能基准，持续监控

### 中风险项目
1. **数据模型不兼容** (SDU-005, SDU-013)
   - 缓解策略：创建适配器模式解决兼容性问题

2. **UI布局问题** (SDU-009, SDU-010)
   - 缓解策略：采用响应式布局设计

## 完成标准

每个SDU的完成标准：
- [ ] 代码实现完成且通过代码审查
- [ ] 相关单元测试通过
- [ ] 集成测试验证功能正确
- [ ] 文档更新完成
- [ ] 无明显性能回归

**总体完成标准**: 所有23个SDU完成，系统能够正常启动并提供完整功能，用户体验与原系统相当或更好。
