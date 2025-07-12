# AIDCIS3 测试计划

> **版本**: v1.0  
> **创建时间**: 2025-01-13  
> **适用版本**: AIDCIS3-LFS v3.0  

## 测试概述

本测试计划涵盖AIDCIS3系统的核心功能改进，包括：
- 产品管理功能增强（删除逻辑、DXF导入整合）
- 数据架构重构（路径管理、检测批次）
- UI界面优化（区域划分进度显示）

## 测试策略

### 测试金字塔

```
       /\
      /  \     系统测试 (E2E)
     /____\    - 完整用户流程
    /      \   
   /        \  集成测试
  /__________\ - 模块间交互
 /            \
/______________\ 单元测试
                 - 独立组件
```

### 测试原则

1. **优先级驱动**: 核心功能优先测试
2. **风险导向**: 重点测试高风险变更
3. **自动化优先**: 回归测试全自动化
4. **持续反馈**: 快速发现和修复问题

## 单元测试方案

### 1. 数据路径管理器测试 (DataPathManager)

**测试文件**: `tests/unit/test_data_path_manager.py`

**测试用例**:
- 路径生成正确性
- 目录结构创建
- 文件信息查询
- 数据迁移功能
- 路径验证

**示例用例**:
```python
def test_get_product_path():
    """测试产品路径生成"""
    manager = DataPathManager()
    path = manager.get_product_path("TP-001")
    assert path.endswith("Data/Products/TP-001")

def test_create_product_structure():
    """测试产品目录结构创建"""
    manager = DataPathManager()
    paths = manager.create_product_structure("TP-001")
    assert "product_dir" in paths
    assert "dxf_dir" in paths
    assert os.path.exists(paths["product_dir"])
```

### 2. 检测批次管理器测试 (InspectionBatchManager)

**测试文件**: `tests/unit/test_inspection_batch_manager.py`

**测试用例**:
- 批次创建和查询
- 状态更新
- 进度计算
- 文件生成
- 批次删除

### 3. 产品管理功能测试 (ProductManagement)

**测试文件**: `tests/unit/test_product_management_enhanced.py`

**测试用例**:
- 删除功能（仅数据库、包含文件）
- DXF导入整合
- 文件收集逻辑
- 权限验证

### 4. 扇形区域管理测试 (SectorManager)

**测试文件**: `tests/unit/test_sector_manager_updated.py`

**测试用例**:
- 区域划分算法
- 进度统计
- 动态扇形数量
- 颜色分配

## 集成测试方案

### 1. 产品-批次-路径集成测试

**测试文件**: `tests/integration/test_product_batch_integration.py`

**测试场景**:
- 创建产品 → 创建检测批次 → 验证目录结构
- 删除产品 → 验证批次处理 → 验证文件清理
- DXF导入 → 自动创建产品 → 验证路径关联

### 2. UI-数据模型集成测试

**测试文件**: `tests/integration/test_ui_data_integration.py`

**测试场景**:
- DXF导入界面 → 填充表单 → 保存产品
- 删除确认对话框 → 文件清单显示 → 执行删除
- 区域划分进度 → 数据更新 → 界面刷新

### 3. 数据迁移集成测试

**测试文件**: `tests/integration/test_data_migration.py`

**测试场景**:
- 遗留数据识别
- 新格式转换
- 数据完整性验证
- 兼容性检查

## 系统测试方案

### 1. 完整用户流程测试

**测试文件**: `tests/system/test_complete_user_workflow.py`

**场景1: 新产品创建流程**
```
用户操作: 产品型号选择 → 产品信息维护 → 从DXF导入 → 保存产品
验证点: 
- 产品数据库记录
- 目录结构创建
- DXF文件复制
- 产品信息文件生成
```

**场景2: 检测流程**
```
用户操作: 选择产品 → 开始检测 → 检测进度更新 → 完成检测
验证点:
- 检测批次创建
- 孔位目录生成
- 进度统计更新
- 汇总报告生成
```

**场景3: 产品删除流程**
```
用户操作: 选择产品 → 删除 → 选择删除方式 → 确认删除
验证点:
- 文件清单正确
- 选择性删除执行
- 数据库记录清理
- 孤立文件检查
```

### 2. 性能测试

**测试文件**: `tests/system/test_performance.py`

**测试场景**:
- 大量产品加载性能
- 批量文件操作性能
- 目录遍历性能
- 数据库查询性能

### 3. 稳定性测试

**测试文件**: `tests/system/test_stability.py`

**测试场景**:
- 长时间运行稳定性
- 内存泄漏检测
- 文件句柄管理
- 异常恢复能力

## 测试数据管理

### 测试数据准备

**目录结构**:
```
tests/
├── fixtures/
│   ├── sample_products.json
│   ├── sample_dxf/
│   │   ├── simple.dxf
│   │   ├── complex.dxf
│   │   └── invalid.dxf
│   └── legacy_data/
│       ├── H00001/
│       └── H00002/
├── mock_data/
│   ├── mock_database.py
│   └── mock_file_system.py
└── utilities/
    ├── test_helpers.py
    └── data_generators.py
```

### 测试环境隔离

- 每个测试使用独立的临时目录
- 数据库使用内存SQLite
- 自动清理测试数据
- Mock外部依赖

## 测试执行策略

### 持续集成 (CI)

**触发条件**:
- 每次代码提交
- Pull Request创建
- 定时任务（每日）

**执行顺序**:
1. 静态代码检查
2. 单元测试 (快速反馈)
3. 集成测试
4. 系统测试
5. 性能测试

### 本地开发测试

**快速测试**:
```bash
# 运行单元测试
python -m pytest tests/unit/ -v

# 运行特定模块测试
python -m pytest tests/unit/test_data_path_manager.py -v

# 运行覆盖率测试
python -m pytest tests/unit/ --cov=src --cov-report=html
```

**完整测试**:
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行集成测试
python -m pytest tests/integration/ -v

# 运行系统测试
python -m pytest tests/system/ -v --slow
```

## 测试质量指标

### 覆盖率目标

- **单元测试覆盖率**: ≥ 90%
- **集成测试覆盖率**: ≥ 80%
- **整体覆盖率**: ≥ 85%

### 性能指标

- **单元测试执行时间**: < 2分钟
- **集成测试执行时间**: < 5分钟
- **系统测试执行时间**: < 15分钟

### 质量门禁

- 所有测试必须通过
- 覆盖率不能降低
- 性能不能明显退化
- 静态检查无严重问题

## 风险识别与缓解

### 主要风险

1. **数据迁移风险**
   - 缓解: 充分的兼容性测试
   - 回滚: 保留原数据副本

2. **文件操作风险**
   - 缓解: 原子操作和事务处理
   - 监控: 文件完整性检查

3. **UI变更风险**
   - 缓解: 渐进式UI测试
   - 验证: 用户接受度测试

### 测试失败处理

1. **快速定位**: 详细的错误日志
2. **自动重试**: 网络和I/O相关测试
3. **降级策略**: 非关键功能可选退化
4. **监控告警**: 自动通知相关人员

## 测试工具和框架

### 主要工具

- **pytest**: 测试框架
- **pytest-cov**: 覆盖率分析
- **pytest-mock**: Mock和Stub
- **pytest-qt**: Qt界面测试
- **pytest-benchmark**: 性能基准测试

### 辅助工具

- **factory-boy**: 测试数据生成
- **freezegun**: 时间Mock
- **responses**: HTTP请求Mock
- **memory-profiler**: 内存使用分析

## 结果报告

### 测试报告格式

- **HTML报告**: 详细的测试结果和覆盖率
- **JUnit XML**: CI系统集成
- **JSON报告**: 自动化分析
- **趋势分析**: 历史对比

### 关键指标监控

- 测试通过率趋势
- 覆盖率变化
- 执行时间趋势
- 缺陷密度分析

---

**维护者**: AIDCIS3测试团队  
**更新频率**: 每个迭代  
**下次更新**: 根据测试执行结果