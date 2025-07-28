# Playwright E2E测试框架

本目录包含实时图表模块的端到端测试框架设计。

## 测试覆盖范围

### 1. 主测试套件 (test_realtime_chart.py)
- **图表初始化测试**: 验证所有UI组件正确加载
- **CSV数据加载测试**: 测试CSV文件读取和数据显示
- **异常检测测试**: 验证异常点的检测和显示
- **图表交互测试**: 测试缩放、平移、点击等交互功能
- **进程控制测试**: 测试外部进程的启动和停止
- **数据导出测试**: 验证数据导出功能
- **实时更新测试**: 测试数据的实时更新
- **清除数据测试**: 验证数据清除功能
- **内窥镜管理测试**: 测试孔位和探头管理
- **组件隔离性测试**: 验证各组件的独立性

### 2. 组件测试套件 (test_realtime_chart_components.py)
- **ChartWidget测试**: 图表渲染、公差线、导出功能
- **DataManager测试**: 数据缓冲、批量添加、统计计算
- **AnomalyDetector测试**: 公差检测、统计检测方法
- **CSVProcessor测试**: CSV监控、数据解析
- **ProcessController测试**: 进程生命周期、进程监控
- **EndoscopeManager测试**: 孔位管理、探头切换、自动切换

## 运行测试

### 安装依赖
```bash
pip install pytest playwright
playwright install chromium
```

### 运行所有测试
```bash
pytest tests/e2e/
```

### 运行特定测试
```bash
# 运行主测试套件
pytest tests/e2e/test_realtime_chart.py

# 运行组件测试
pytest tests/e2e/test_realtime_chart_components.py

# 运行特定测试用例
pytest tests/e2e/test_realtime_chart.py::TestRealtimeChart::test_csv_data_loading
```

### 测试配置选项
```bash
# 无头模式运行（后台运行）
pytest tests/e2e/ --headed=false

# 慢速模式（便于观察）
pytest tests/e2e/ --slowmo=500

# 生成测试报告
pytest tests/e2e/ --html=report.html
```

## 测试架构设计

### 1. 页面对象模式
虽然当前实现直接操作元素，但可以扩展为页面对象模式：

```python
class RealtimeChartPage:
    def __init__(self, page):
        self.page = page
        
    def start_monitoring(self):
        self.page.click("button:has-text('开始监测')")
        
    def load_csv(self, file_path):
        self.page.evaluate(f"window.realtimeChart.set_csv_file('{file_path}')")
```

### 2. 测试数据管理
- 使用fixture创建和清理测试数据
- CSV文件自动生成和删除
- 测试隔离，避免相互影响

### 3. 断言策略
- 使用Playwright的expect API进行可靠的异步断言
- 结合JavaScript评估进行深度状态验证
- 超时配置确保测试稳定性

## 扩展建议

### 1. 性能测试
```python
def test_large_dataset_performance(page):
    # 创建大数据集
    create_test_csv("large_data.csv", 10000)
    
    # 测量加载时间
    start_time = time.time()
    page.evaluate("window.realtimeChart.set_csv_file('large_data.csv')")
    load_time = time.time() - start_time
    
    assert load_time < 5.0  # 应在5秒内完成
```

### 2. 视觉回归测试
```python
def test_chart_visual_regression(page):
    # 加载标准数据
    load_standard_data(page)
    
    # 截图对比
    page.screenshot(path="chart_actual.png")
    # 使用图像对比工具验证
```

### 3. 并发测试
```python
def test_concurrent_operations(page):
    # 同时进行多个操作
    Promise.all([
        page.evaluate("window.realtimeChart.start_monitoring()"),
        page.evaluate("window.realtimeChart.process_controller.start_process('test')"),
        page.evaluate("window.realtimeChart.endoscope_manager.start_auto_switch()")
    ])
```

## 最佳实践

1. **测试独立性**: 每个测试应该独立运行，不依赖其他测试
2. **清理策略**: 使用fixture确保测试后清理
3. **等待策略**: 使用适当的等待条件，避免固定延时
4. **错误处理**: 捕获并记录详细的错误信息
5. **可维护性**: 保持测试代码简洁，使用描述性命名

## 调试技巧

1. **截图调试**:
```python
page.screenshot(path="debug.png")
```

2. **暂停执行**:
```python
page.pause()  # 会打开Playwright Inspector
```

3. **控制台日志**:
```python
page.on("console", lambda msg: print(f"Console: {msg.text}"))
```

4. **网络监控**:
```python
page.on("request", lambda req: print(f"Request: {req.url}"))
```