"""
Playwright测试配置
"""
import pytest
from playwright.sync_api import sync_playwright
import subprocess
import time
import os
import sys


# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def browser():
    """创建浏览器实例"""
    with sync_playwright() as p:
        # 使用Chromium进行测试
        browser = p.chromium.launch(
            headless=False,  # 设置为False以便观察测试过程
            slow_mo=100  # 减慢操作速度，便于观察
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """为每个测试创建新页面"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN"
    )
    page = context.new_page()
    
    # 注入测试辅助函数
    page.add_init_script("""
        // 将实时图表实例暴露给测试
        window.addEventListener('DOMContentLoaded', () => {
            // 等待应用初始化
            setTimeout(() => {
                const chartElement = document.querySelector('.realtime-chart');
                if (chartElement && chartElement.__vue__) {
                    window.realtimeChart = chartElement.__vue__.$refs.realtimeChart;
                } else if (window.app && window.app.realtimeChart) {
                    window.realtimeChart = window.app.realtimeChart;
                }
            }, 1000);
        });
    """)
    
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="session")
def test_server():
    """启动测试服务器"""
    # 创建一个简单的测试服务器脚本
    server_script = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import time

# 创建测试HTML页面
test_html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RealtimeChart Test</title>
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
    <style>
        body { margin: 20px; font-family: Arial, sans-serif; }
        .realtime-chart { border: 1px solid #ccc; padding: 10px; }
    </style>
</head>
<body>
    <div id="app">
        <div class="realtime-chart" ref="realtimeChart"></div>
    </div>
    
    <script type="module">
        // 模拟实时图表组件
        import('/src/modules/realtime_chart/test_runner.js').then(module => {
            window.app = new Vue({
                el: '#app',
                mounted() {
                    // 创建实时图表实例
                    this.$refs.realtimeChart.__vue__ = {
                        $refs: {
                            realtimeChart: module.createRealtimeChart()
                        }
                    };
                    window.realtimeChart = module.createRealtimeChart();
                }
            });
        });
    </script>
</body>
</html>
'''

with open('test_index.html', 'w', encoding='utf-8') as f:
    f.write(test_html)

# 启动HTTP服务器
def run_server():
    server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

server_thread = Thread(target=run_server, daemon=True)
server_thread.start()

print("Test server started at http://localhost:8000")
time.sleep(2)  # 等待服务器启动
"""
    
    # 写入服务器脚本
    with open('test_server.py', 'w') as f:
        f.write(server_script)
    
    # 启动服务器进程
    server_process = subprocess.Popen(
        [sys.executable, 'test_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务器启动
    time.sleep(3)
    
    yield server_process
    
    # 清理
    server_process.terminate()
    server_process.wait()
    
    # 删除临时文件
    for file in ['test_server.py', 'test_index.html']:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture(autouse=True)
def setup_test_environment(test_server):
    """设置测试环境"""
    # 创建测试运行器
    test_runner = """
// 测试运行器 - 创建实时图表实例用于测试
import { RealtimeChart } from './realtime_chart.js';
import { ChartWidget } from './components/chart_widget.js';
import { DataManager } from './components/data_manager.js';
import { CSVProcessor } from './components/csv_processor.js';
import { AnomalyDetector } from './components/anomaly_detector.js';
import { EndoscopeManager } from './components/endoscope_manager.js';
import { ProcessController } from './components/process_controller.js';

export function createRealtimeChart() {
    // 创建一个模拟的Qt应用环境
    const mockParent = document.querySelector('.realtime-chart');
    
    // 创建并返回实时图表实例
    const chart = new RealtimeChart(mockParent);
    
    // 确保所有组件都已初始化
    chart.chart_widget = chart.chart_widget || new ChartWidget();
    chart.data_manager = chart.data_manager || new DataManager();
    chart.csv_processor = chart.csv_processor || new CSVProcessor();
    chart.anomaly_detector = chart.anomaly_detector || new AnomalyDetector();
    chart.endoscope_manager = chart.endoscope_manager || new EndoscopeManager();
    chart.process_controller = chart.process_controller || new ProcessController();
    
    return chart;
}
"""
    
    # 写入测试运行器
    os.makedirs('src/modules/realtime_chart', exist_ok=True)
    with open('src/modules/realtime_chart/test_runner.js', 'w') as f:
        f.write(test_runner)
    
    yield
    
    # 清理测试运行器
    if os.path.exists('src/modules/realtime_chart/test_runner.js'):
        os.remove('src/modules/realtime_chart/test_runner.js')