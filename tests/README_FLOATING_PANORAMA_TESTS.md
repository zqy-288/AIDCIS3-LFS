# 浮动全景图修改功能测试套件

## 快速开始

### 运行所有测试
```bash
cd /Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS
python tests/run_floating_panorama_tests.py
```

### 运行特定类别
```bash
# 只运行单元测试
python tests/run_floating_panorama_tests.py --category unit

# 只运行集成测试
python tests/run_floating_panorama_tests.py --category integration

# 只运行系统测试
python tests/run_floating_panorama_tests.py --category system
```

### 生成详细报告
```bash
python tests/run_floating_panorama_tests.py --category all --verbose --report
```

## 测试内容

### 🎨 浮动窗口样式测试
- 验证绿色边框已移除
- 验证半透明背景设置正确
- 验证标题"全局预览视图"显示
- 验证窗口尺寸调整（220x240）

### 🔄 数据同步测试
- 验证与主窗口信号连接
- 验证与左边栏全景图数据同步
- 验证状态更新一致性

### 📐 扇形区域调整测试
- 验证中心点向右下偏移（5%）
- 验证半径缩小（1.1→0.9）
- 验证小型和主全景图同步调整

### 📁 JSON并发读写测试
- 验证原子写入操作
- 验证文件读取重试机制
- 验证并发安全性
- 验证故障恢复能力

## 测试结果解读

### 成功示例
```
单元测试: ✅ 通过 (12/12 测试)
集成测试: ✅ 通过 (8/8 测试)
系统测试: ✅ 通过 (6/6 测试)

🎉 所有测试都通过了！浮动全景图修改功能验证成功。
```

### 失败排查
如果测试失败，检查：

1. **环境依赖**
   ```bash
   pip install PySide6 pytest
   ```

2. **图形环境**
   ```bash
   export QT_QPA_PLATFORM=offscreen
   ```

3. **文件权限**
   ```bash
   ls -la tests/
   chmod +x tests/run_floating_panorama_tests.py
   ```

## 测试文件说明

| 文件 | 类型 | 描述 |
|-----|------|------|
| `test_floating_panorama_modifications.py` | 单元测试 | 组件独立功能测试 |
| `test_json_concurrent_io.py` | 单元测试 | JSON文件并发安全测试 |
| `test_floating_panorama_integration.py` | 集成测试 | 组件间集成测试 |
| `test_floating_panorama_system.py` | 系统测试 | 端到端工作流程测试 |
| `run_floating_panorama_tests.py` | 运行器 | 测试执行和报告生成 |

## 性能基准

- 单元测试总耗时: < 30秒
- 集成测试总耗时: < 60秒  
- 系统测试总耗时: < 120秒
- 并发操作吞吐量: > 10操作/秒
- JSON读写重试成功率: > 95%

## 集成到CI/CD

### GitHub Actions
```yaml
# 添加到 .github/workflows/test.yml
- name: Run floating panorama tests
  run: |
    python tests/run_floating_panorama_tests.py --category all --report
```

### 本地开发
```bash
# 开发前运行测试
python tests/run_floating_panorama_tests.py --category unit

# 提交前运行完整测试
python tests/run_floating_panorama_tests.py --category all
```

## 测试报告

测试运行后会在 `tests/test_reports/` 生成详细报告：
```
floating_panorama_test_report_20250113_143022.txt
```

报告包含：
- 测试执行摘要
- 性能指标
- 失败详情
- 修复建议

## 维护说明

### 添加新测试
1. 在相应目录创建测试文件
2. 继承 `unittest.TestCase`
3. 更新 `run_floating_panorama_tests.py` 的模块列表

### 更新性能基准
1. 运行性能测试获得新基准
2. 更新测试中的性能断言
3. 更新文档中的性能指标

### 测试环境隔离
每个测试都使用独立的临时目录，确保测试间不相互影响。