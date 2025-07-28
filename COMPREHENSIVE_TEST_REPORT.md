# 🎯 AIDCIS3-LFS 综合测试报告

## 📋 执行摘要

**测试时间**: 2025-07-26 01:40:50  
**总执行时间**: 3.69 秒  
**测试成功率**: 75.0%

## 📊 统计概览

| 指标 | 数量 |
|------|------|
| 总测试数 | 8 |
| 通过测试 | 6 ✅ |
| 失败测试 | 2 ❌ |
| 跳过测试 | 0 ⏭️ |

## 🧪 测试套件详情

### ✅ 零容忍核心测试

- **状态**: 通过
- **执行时间**: 0.74 秒
- **测试数量**: 0
- **通过数量**: 0
- **失败数量**: 0

**错误信息**:
```
2025-07-26 01:40:47,228 - INFO - 🚀 开始零容忍测试套件 (修复版)...
2025-07-26 01:40:47,229 - INFO - 🧪 执行测试: 主窗口创建测试 (优化版)
qt.qpa.fonts: Populating font family aliases took 73 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
2025-07-26 01:40:47,708 - INFO - 配置文件加载成功: config/config.json
2025-07-26 01:40:47,724 - INFO - 配置管理器初始化成功: ConfigManager
2025-07-26 01:40:47,724 - INFO - ApplicationCore initialized
2025-07-26 01:40:47,724 - INFO - ErrorRecoveryManager initial...
```

### ❌ UI自动化测试

- **状态**: 失败
- **执行时间**: 2.95 秒
- **测试数量**: 8
- **通过数量**: 6
- **失败数量**: 2

**错误信息**:
```
/Users/vsiyo/Library/Python/3.9/lib/python/site-packages/pytest_asyncio/plugin.py:208: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop ...
```

## ❌ 测试结论

**测试失败过多** (75.0%)，系统未达到质量标准，需要重大修复。

