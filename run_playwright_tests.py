#!/usr/bin/env python3
"""
Playwright测试运行器
用于测试重构后的实时图表模块
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """检查必要的依赖"""
    try:
        import playwright
        print("✅ Playwright已安装")
    except ImportError:
        print("❌ Playwright未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "pytest-playwright"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright安装完成")
        
    try:
        import pytest
        print("✅ Pytest已安装")
    except ImportError:
        print("❌ Pytest未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-html"])
        print("✅ Pytest安装完成")


def create_test_app():
    """创建测试应用程序"""
    test_app = '''#!/usr/bin/env python3
"""
实时图表模块测试应用
用于Playwright E2E测试
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
from src.modules.realtime_chart_p2 import RealtimeChart
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class TestAPIHandler(BaseHTTPRequestHandler):
    """测试API处理器"""
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # 处理测试命令
        if self.path == '/api/execute':
            result = window.execute_test_command(data['command'], data.get('args', {}))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RealtimeChart Test Application")
        self.setGeometry(100, 100, 1600, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建实时图表实例
        self.realtime_chart = RealtimeChart()
        layout.addWidget(self.realtime_chart)
        
        # 设置全局访问
        global window
        window = self
        
        # 启动测试API服务器
        self.start_test_server()
        
    def start_test_server(self):
        """启动测试API服务器"""
        def run_server():
            server = HTTPServer(('localhost', 8888), TestAPIHandler)
            server.serve_forever()
            
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print("测试API服务器已启动: http://localhost:8888")
        
    def execute_test_command(self, command: str, args: dict) -> dict:
        """执行测试命令"""
        try:
            if command == 'get_status':
                return {
                    'success': True,
                    'data': {
                        'chart_visible': self.realtime_chart.isVisible(),
                        'data_loaded': self.realtime_chart.is_data_loaded,
                        'current_hole': self.realtime_chart.current_hole_id
                    }
                }
            elif command == 'load_test_data':
                # 创建测试数据
                test_depths = list(range(0, 100, 10))
                test_diameters = [17.6 + i * 0.01 for i in range(10)]
                
                # 使用新的组件API
                self.realtime_chart.data_manager.add_data_batch(test_depths, test_diameters)
                self.realtime_chart.chart_widget.update_data(test_depths, test_diameters)
                
                return {'success': True, 'message': 'Test data loaded'}
                
            elif command == 'set_standard_diameter':
                diameter = args.get('diameter', 17.6)
                tolerance = args.get('tolerance', 0.2)
                self.realtime_chart.set_standard_diameter(diameter, tolerance)
                return {'success': True}
                
            elif command == 'start_monitoring':
                self.realtime_chart.start_monitoring()
                return {'success': True}
                
            elif command == 'stop_monitoring':
                self.realtime_chart.stop_monitoring()
                return {'success': True}
                
            elif command == 'clear_data':
                self.realtime_chart.clear_data()
                return {'success': True}
                
            elif command == 'get_component_status':
                return {
                    'success': True,
                    'components': {
                        'chart_widget': hasattr(self.realtime_chart, 'chart_widget'),
                        'data_manager': hasattr(self.realtime_chart, 'data_manager'),
                        'csv_processor': hasattr(self.realtime_chart, 'csv_processor'),
                        'anomaly_detector': hasattr(self.realtime_chart, 'anomaly_detector'),
                        'endoscope_manager': hasattr(self.realtime_chart, 'endoscope_manager'),
                        'process_controller': hasattr(self.realtime_chart, 'process_controller')
                    }
                }
                
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
'''
    
    # 写入测试应用
    with open('test_app.py', 'w', encoding='utf-8') as f:
        f.write(test_app)
    print("✅ 测试应用创建完成")


def run_tests():
    """运行Playwright测试"""
    print("\n🧪 开始运行Playwright测试...\n")
    
    # 创建测试报告目录
    os.makedirs('test_reports', exist_ok=True)
    
    # 运行测试
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/e2e/",
        "-v",
        "--html=test_reports/playwright_report.html",
        "--self-contained-html",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("\n" + "="*50)
    print("测试输出:")
    print("="*50)
    print(result.stdout)
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr)
        
    return result.returncode == 0


def main():
    """主函数"""
    print("🚀 Playwright测试运行器")
    print("="*50)
    
    # 检查依赖
    check_dependencies()
    
    # 创建测试应用
    create_test_app()
    
    # 运行测试
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过!")
    else:
        print("\n❌ 部分测试失败，请查看详细报告: test_reports/playwright_report.html")
        
    # 清理
    if os.path.exists('test_app.py'):
        os.remove('test_app.py')


if __name__ == '__main__':
    main()