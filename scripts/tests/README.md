# AIDCIS3 测试套件

本目录包含AIDCIS3项目的完整测试套件，包括单元测试、集成测试、端到端测试和性能测试。

## 测试文件说明

### 单元测试

1. **test_unit_sector_display.py** - 扇形显示组件单元测试
   - 测试扇形图形项创建和属性
   - 测试进度更新功能
   - 测试文本标签大小（3pt字体）
   - 测试场景设置和视图缩放（0.6倍）
   - 测试整体统计标签更新

2. **test_unit_dxf_rotation.py** - DXF旋转功能单元测试
   - 测试90度逆时针旋转计算
   - 测试带偏移的旋转
   - 测试扇形区域分配算法
   - 测试Qt角度转换
   - 测试边界情况处理

### 集成测试

3. **test_integration_simulation.py** - 模拟进度功能集成测试
   - 测试模拟初始化和停止
   - 测试孔位状态更新
   - 测试扇形管理器信号连接
   - 测试跨扇形更新
   - 测试UI组件同步更新

### 端到端测试

4. **test_e2e_complete_workflow.py** - 完整工作流程端到端测试
   - 测试从DXF加载到模拟的完整流程
   - 测试UI响应性（缩放、平移等）
   - 测试错误处理
   - 测试数据持久性
   - 测试用户交互（搜索、过滤、检测控制）

### 性能测试

5. **test_performance_optimization.py** - 性能优化测试
   - 测试内存优化（无工具提示）
   - 测试大量孔位渲染性能（5000个孔位）
   - 测试扇形分配性能（10000个孔位）
   - 测试UI响应性（快速切换）
   - 测试不同参数对性能的影响

## 运行测试

### 运行所有测试

```bash
python scripts/tests/run_all_tests.py
```

### 运行单个测试文件

```bash
# 单元测试
python scripts/tests/test_unit_sector_display.py
python scripts/tests/test_unit_dxf_rotation.py

# 集成测试
python scripts/tests/test_integration_simulation.py

# 端到端测试
python scripts/tests/test_e2e_complete_workflow.py

# 性能测试
python scripts/tests/test_performance_optimization.py
```

### 运行特定测试用例

```bash
# 使用unittest的测试发现功能
python -m unittest scripts.tests.test_unit_sector_display.TestSectorGraphicsItem.test_sector_creation

# 或者使用pytest（如果已安装）
pytest scripts/tests/test_unit_sector_display.py::TestSectorGraphicsItem::test_sector_creation
```

## 测试覆盖的功能

1. **扇形显示优化**
   - ✓ 半径减小到10px
   - ✓ 字体减小到3pt
   - ✓ 缩放比例0.6
   - ✓ 紧凑的边距设置

2. **DXF旋转功能**
   - ✓ 90度逆时针预旋转
   - ✓ 旋转后的扇形分配
   - ✓ 严格的区域对应关系

3. **性能优化**
   - ✓ 移除鼠标悬停工具提示
   - ✓ 减少内存使用
   - ✓ 提高渲染性能

4. **数据同步**
   - ✓ 模拟进度同步到扇形管理器
   - ✓ 状态统计实时更新
   - ✓ 多面板数据一致性

5. **UI布局**
   - ✓ 大扇形显示移到左上角
   - ✓ 移除不必要的叠加层

## 测试环境要求

- Python 3.8+
- PySide6
- psutil（用于性能测试）
- memory_profiler（可选，用于内存分析）

## 测试最佳实践

1. **运行测试前**
   - 确保项目依赖已安装
   - 关闭其他占用资源的程序（特别是运行性能测试时）
   - 确保有足够的内存（建议至少4GB）

2. **调试失败的测试**
   - 查看详细的错误信息
   - 使用 `-v` 参数增加输出详细度
   - 单独运行失败的测试用例

3. **性能测试注意事项**
   - 性能测试结果可能因系统而异
   - 基准值是参考性的，不是绝对标准
   - 在相同环境下比较不同版本的性能

## 持续集成

这些测试可以集成到CI/CD流程中：

```yaml
# 示例 GitHub Actions 配置
- name: Run Tests
  run: |
    python scripts/tests/run_all_tests.py
```

## 贡献指南

添加新测试时，请遵循以下规范：

1. 使用描述性的测试方法名
2. 每个测试方法只测试一个功能点
3. 使用setUp和tearDown正确管理资源
4. 添加适当的文档字符串
5. 确保测试独立可运行

## 问题反馈

如果发现测试问题，请：

1. 记录完整的错误信息
2. 说明运行环境（OS、Python版本等）
3. 提供重现步骤
4. 在项目Issues中报告