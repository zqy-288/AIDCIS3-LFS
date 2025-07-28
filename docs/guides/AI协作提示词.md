# AI协作提示词 - MainWindow重构项目

---

## **阶段一：基础架构搭建与接口定义**

- **阶段说明**: 此阶段是整个项目的基础，创建项目结构、定义核心接口和数据模型，其产出将直接影响后续所有阶段。

---

### **AI 任务 1.1: 架构设计师**

- **核心职责**: 创建完整的项目目录结构，定义所有核心接口和基础类框架

- **最终提示词**:
    
    ```
    你是一名Python架构设计师，专精于PySide6和MVVM模式。请基于以下共享背景信息创建MainWindow重构的基础架构：
    
    共享背景信息位置：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    
    你需要完成：
    1. 创建文档中指定的完整目录结构（src/ui/, src/controllers/等）
    2. 为每个目录创建__init__.py文件
    3. 定义以下核心接口类（只包含方法签名和文档）：
       - IMainViewController (UI层接口)
       - IMainBusinessController (业务层接口)
       - IMainViewModel (数据模型接口)
       - IMainWindowCoordinator (协调器接口)
    4. 创建基础的异常类和工具类
    5. 生成一个architecture_overview.md文件说明整体架构
    
    所有代码必须包含详细的类型注解和文档字符串。接口定义必须与共享背景信息中的规范完全一致。
    ```

### **AI 任务 1.2: 数据模型专家**

- **核心职责**: 设计和实现MainViewModel数据模型及其管理器

- **最终提示词**:
    
    ```
    你是一名数据建模专家，精通Python dataclass和Qt信号机制。请基于以下共享背景信息创建MVVM模式的数据层：
    
    共享背景信息位置：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    
    你需要完成：
    1. 在src/ui/view_models/main_view_model.py中实现MainViewModel dataclass
    2. 包含共享文档中指定的所有状态字段（current_file_path, detection_running等）
    3. 在src/ui/view_models/view_model_manager.py中实现MainViewModelManager类
    4. 实现数据变化通知机制（使用Qt Signal）
    5. 创建view_model_test.py测试文件，验证数据模型的正确性
    
    确保所有字段都有默认值，使用field(default_factory=...)处理可变类型。包含完整的类型注解。
    ```

### **AI 任务 1.3: 测试框架工程师**

- **核心职责**: 搭建测试框架和创建测试模板

- **最终提示词**:
    
    ```
    你是一名测试工程师，专精于Python单元测试和集成测试。请基于以下共享背景信息创建测试框架：
    
    共享背景信息位置：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    
    你需要完成：
    1. 在tests/目录下创建测试结构（unit/, integration/, performance/）
    2. 创建基础测试类BaseTestCase，处理Qt应用初始化
    3. 为每个主要组件创建测试模板：
       - test_main_view_controller.py
       - test_main_business_controller.py
       - test_main_view_model.py
       - test_integration.py
    4. 实现共享文档中指定的基础测试用例
    5. 创建performance_benchmark.py性能基准测试
    
    使用pytest框架，包含fixture定义和mock对象使用示例。
    ```

---

## **阶段二：核心组件实现**

- **阶段说明**: 此阶段的工作将在**阶段一**的成果基础上展开，实现三大核心组件的具体功能。

---

### **AI 任务 2.1: UI层开发工程师**

- **核心职责**: 实现MainViewController及其所有UI组件

- **最终提示词**:
    
    ```
    你是一名PySide6 UI开发专家。请基于以下信息实现MainViewController：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    阶段一产出：查看src/ui/目录下的接口定义和src/ui/view_models/下的数据模型
    
    你需要完成：
    1. 在src/ui/main_view_controller.py中实现MainViewController类
    2. 从原main_window.py（5882行）中提取以下UI方法并重构：
       - create_toolbar() → 实现在components/toolbar_component.py
       - create_left_info_panel() → 实现在components/info_panel_component.py
       - create_center_visualization_panel() → 实现在components/visualization_panel_component.py
       - create_right_operations_panel() → 实现在components/operations_panel_component.py
    3. 实现user_action信号发射机制
    4. 实现update_display()方法，根据ViewModel更新UI
    5. 确保所有用户交互都转换为信号，不包含任何业务逻辑
    
    代码必须遵循共享文档中的命名规范和文档规范。保持UI布局与原版一致。
    ```

### **AI 任务 2.2: 业务逻辑开发工程师**

- **核心职责**: 实现MainBusinessController及其服务层

- **最终提示词**:
    
    ```
    你是一名业务逻辑架构师。请基于以下信息实现MainBusinessController：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    阶段一产出：查看src/controllers/目录下的接口定义
    原始代码：main_window.py中的业务逻辑部分
    
    你需要完成：
    1. 在src/controllers/main_business_controller.py中实现主控制器
    2. 实现handle_user_action()方法，处理所有用户动作
    3. 在services/目录下实现：
       - detection_service.py：处理检测相关业务
       - file_service.py：处理文件和产品管理
       - search_service.py：处理搜索功能
       - status_service.py：处理状态管理
    4. 从原main_window.py提取业务逻辑，重构为服务方法
    5. 实现view_model_changed和message_occurred信号发射
    
    确保与现有的DXFParser、StatusManager等组件正确集成。所有业务逻辑必须与UI完全解耦。
    ```

### **AI 任务 2.3: 集成测试工程师**

- **核心职责**: 为阶段二的组件编写完整的测试

- **最终提示词**:
    
    ```
    你是一名测试专家。请基于以下信息为核心组件编写测试：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    阶段一测试框架：tests/目录下的测试模板
    阶段二实现：src/ui/和src/controllers/下的具体实现
    
    你需要完成：
    1. 为MainViewController编写完整的单元测试
    2. 为MainBusinessController编写单元测试
    3. 为每个Service编写独立的测试
    4. 编写UI和Business层的集成测试
    5. 创建测试数据fixtures和mock对象
    
    测试覆盖率目标：核心功能100%，总体>80%。使用pytest-cov生成覆盖率报告。
    ```

---

## **阶段三：系统集成与协调器实现**

- **阶段说明**: 此阶段将整合前两个阶段的成果，实现组件间的协调机制，完成系统集成。

---

### **AI 任务 3.1: 系统集成架构师**

- **核心职责**: 实现MainWindowCoordinator和组件集成

- **最终提示词**:
    
    ```
    你是一名系统集成专家。请基于以下信息实现组件协调器：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    阶段一产出：接口定义和数据模型
    阶段二产出：MainViewController和MainBusinessController实现
    
    你需要完成：
    1. 在src/controllers/coordinators/main_window_coordinator.py中实现协调器
    2. 实现组件创建和初始化逻辑
    3. 设置所有组件间的信号连接
    4. 处理组件生命周期管理
    5. 重写简化版的src/main_window.py，保持对外接口兼容
    
    确保三个组件能够无缝协作，数据流向符合MVVM模式。新的main_window.py应少于300行。
    ```

### **AI 任务 3.2: 性能优化工程师**

- **核心职责**: 优化系统性能和资源使用

- **最终提示词**:
    
    ```
    你是一名性能优化专家。请基于以下信息优化系统性能：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    当前实现：所有阶段的代码产出
    性能要求：启动时间<5秒，UI响应<100ms，内存增长<20%
    
    你需要完成：
    1. 使用cProfile分析性能瓶颈
    2. 优化组件初始化顺序和延迟加载
    3. 实现高效的信号传递机制
    4. 优化ViewModel更新策略，减少不必要的UI刷新
    5. 创建performance_report.md，记录优化前后对比
    
    重点关注：大量数据加载时的性能、频繁UI更新的效率、内存泄漏检测。
    ```

### **AI 任务 3.3: 文档工程师**

- **核心职责**: 创建完整的项目文档和迁移指南

- **最终提示词**:
    
    ```
    你是一名技术文档专家。请基于以下信息创建项目文档：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    所有阶段产出：完整的代码实现
    
    你需要完成：
    1. 创建README.md，说明新架构和使用方法
    2. 编写MIGRATION_GUIDE.md，详细说明从旧版迁移步骤
    3. 创建API_REFERENCE.md，记录所有公共接口
    4. 编写ARCHITECTURE.md，解释设计决策和模式
    5. 创建docs/examples/目录，提供使用示例
    
    文档应包含架构图、序列图、类图等可视化内容（使用mermaid语法）。
    ```

---

## **阶段四：验收与部署准备**

- **阶段说明**: 此阶段进行最终的集成测试、问题修复和部署准备工作。

---

### **AI 任务 4.1: QA测试工程师**

- **核心职责**: 执行完整的质量保证测试

- **最终提示词**:
    
    ```
    你是一名QA工程师。请基于以下信息执行全面测试：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    完整实现：所有阶段的代码
    原始功能：main_window.py的所有功能点
    
    你需要完成：
    1. 创建功能对照清单，确保所有原有功能正常
    2. 执行端到端测试，模拟真实用户操作
    3. 进行回归测试，验证重构没有引入新bug
    4. 测试异常情况和边界条件
    5. 创建QA_REPORT.md，详细记录所有测试结果
    
    重点测试：文件加载、检测流程、搜索功能、UI响应、内存使用。发现的问题需提供复现步骤。
    ```

### **AI 任务 4.2: DevOps工程师**

- **核心职责**: 准备部署流程和自动化脚本

- **最终提示词**:
    
    ```
    你是一名DevOps工程师。请基于以下信息准备部署：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    项目结构：重构后的完整代码
    
    你需要完成：
    1. 创建setup.py或pyproject.toml配置文件
    2. 编写CI/CD配置（GitHub Actions或类似）
    3. 创建自动化测试脚本
    4. 准备版本迁移脚本
    5. 编写DEPLOYMENT.md部署指南
    
    包含：依赖管理、环境配置、自动化测试、代码质量检查、打包发布流程。
    ```

### **AI 任务 4.3: 项目经理**

- **核心职责**: 创建项目总结报告和后续规划

- **最终提示词**:
    
    ```
    你是一名项目经理。请基于以下信息创建项目报告：
    
    共享背景信息：/Users/vsiyo/Desktop/AIDCIS3-LFS/SHARED_CONTEXT_FOR_AI_COLLABORATION.md
    所有阶段成果：代码、测试、文档
    技术债务报告：原始的技术债务评估
    
    你需要完成：
    1. 创建PROJECT_SUMMARY.md，总结重构成果
    2. 对比重构前后的代码质量指标
    3. 评估技术债务的解决程度
    4. 识别剩余的改进空间
    5. 制定后续优化路线图
    
    报告应包含：目标达成情况、关键指标对比、经验教训、风险评估、下一步建议。
    ```

---