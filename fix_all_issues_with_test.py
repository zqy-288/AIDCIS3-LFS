#!/usr/bin/env python3
"""
修复所有问题并包含测试功能
"""

import re
import subprocess
import sys
import time

def fix_sector_view_autoscale():
    """修复扇形视图的自适应缩放"""
    print("🔧 修复扇形视图自适应...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除固定大小限制，使用自适应
    content = re.sub(
        r'self\.graphics_view\.setMinimumSize\(\d+, \d+\)',
        '# self.graphics_view.setMinimumSize(600, 600)  # 使用自适应',
        content
    )
    content = re.sub(
        r'self\.graphics_view\.setMaximumSize\(\d+, \d+\)',
        '# self.graphics_view.setMaximumSize(800, 800)  # 使用自适应',
        content
    )
    
    # 2. 确保在 setup_ui 中设置正确的大小策略
    if "setSizePolicy" not in content:
        pattern = r'(self\.graphics_view = OptimizedGraphicsView\(\))'
        replacement = r'''\1
        # 设置大小策略为扩展
        from PySide6.QtWidgets import QSizePolicy
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)'''
        
        content = re.sub(pattern, replacement, content)
    
    # 3. 在 setup_ui 的布局部分确保主视图占据大部分空间
    if "setStretchFactor" not in content:
        # 在 main_layout.addWidget(main_splitter) 后添加
        pattern = r'(main_layout\.addWidget\(main_splitter\))'
        replacement = r'''\1
        # 设置伸展因子，让主视图占据更多空间
        main_splitter.setStretchFactor(0, 3)  # 左侧（包含扇形视图）
        main_splitter.setStretchFactor(1, 1)  # 右侧'''
        
        content = re.sub(pattern, replacement, content)
    
    # 4. 确保数据加载后自动适配
    pattern = r'(self\.graphics_view\.load_holes\(sector_collection\).*?)(if hasattr\(self, \'graphics_view\'\) and self\.graphics_view:)'
    replacement = r'''\1
                    # 延迟自适应以确保布局完成
                    from PySide6.QtCore import QTimer
                    def auto_fit():
                        if hasattr(self.graphics_view, 'fit_to_window_width'):
                            self.graphics_view.fit_to_window_width()
                            print("✅ [扇形视图] 自适应完成")
                    QTimer.singleShot(200, auto_fit)
                    
                \2'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 扇形视图自适应修复完成")

def fix_mini_panorama_size_and_center():
    """修复小型全景图的大小和居中"""
    print("\n🔧 修复小型全景图...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 在 _create_mini_panorama 中设置合适的大小
    pattern = r'(mini_panorama = QGraphicsView\(\))'
    replacement = r'''\1
        # 设置小型全景图的固定大小
        mini_panorama.setFixedSize(200, 200)
        mini_panorama.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")'''
    
    content = re.sub(pattern, replacement, content)
    
    # 2. 在 _setup_mini_panorama 中确保正确缩放和居中
    if "# 计算适合的缩放" not in content:
        pattern = r'(self\.mini_panorama\.fitInView\(scene_rect, Qt\.KeepAspectRatio\))'
        replacement = r'''# 计算适合的缩放
        view_rect = self.mini_panorama.viewport().rect()
        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()
        scale = min(scale_x, scale_y) * 0.9  # 留10%边距
        
        # 重置变换并应用缩放
        self.mini_panorama.resetTransform()
        self.mini_panorama.scale(scale, scale)
        
        # 居中显示
        self.mini_panorama.centerOn(scene_rect.center())'''
        
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 小型全景图修复完成")

def fix_rendering_colors():
    """修复渲染颜色问题"""
    print("\n🔧 修复渲染颜色...")
    
    # 1. 修复 hole_item.py
    filepath = "src/aidcis2/graphics/hole_item.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保颜色映射正确
    if "STATUS_COLORS = {" in content:
        # 确保使用明亮的颜色
        pattern = r'STATUS_COLORS = \{[^}]+\}'
        replacement = '''STATUS_COLORS = {
        HoleStatus.NOT_DETECTED: QColor(200, 200, 200),      # 灰色
        HoleStatus.PENDING: QColor(200, 200, 200),          # 灰色
        HoleStatus.DETECTING: QColor(100, 150, 255),        # 蓝色
        HoleStatus.QUALIFIED: QColor(50, 200, 50),          # 绿色
        HoleStatus.UNQUALIFIED: QColor(255, 50, 50),        # 红色
        HoleStatus.UNCERTAIN: QColor(255, 200, 50),         # 黄色
        HoleStatus.ERROR: QColor(255, 100, 100),            # 浅红色
        HoleStatus.REAL_DATA: QColor(100, 255, 100)         # 亮绿色
    }'''
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 确保更新时重新设置画刷
    pattern = r'(def update_status\(self, status: HoleStatus\):.*?)(self\.update\(\))'
    replacement = r'''\1# 确保颜色更新
        self.setPen(QPen(Qt.NoPen))  # 无边框
        self.setOpacity(1.0)  # 完全不透明
        \2'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 渲染颜色修复完成")

def ensure_method_exists():
    """确保 update_mini_panorama_hole_status 方法存在并正确实现"""
    print("\n🔧 确保方法存在...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除可能存在的旧实现
    content = re.sub(
        r'\n\s*def update_mini_panorama_hole_status.*?(?=\n\s*def|\n\s*class|\Z)',
        '',
        content,
        flags=re.DOTALL
    )
    
    # 添加正确的实现
    method_code = '''

    def update_mini_panorama_hole_status(self, hole_id: str, status, color=None):
        """更新小型全景图中的孔位状态"""
        try:
            if hasattr(self, 'mini_panorama_items') and hole_id in self.mini_panorama_items:
                item = self.mini_panorama_items[hole_id]
                if color:
                    from PySide6.QtGui import QBrush
                    item.setBrush(QBrush(color))
                item.update()
                
                # 更新场景
                if hasattr(self, 'mini_panorama') and self.mini_panorama:
                    self.mini_panorama.viewport().update()
                    
                print(f"✅ [小型全景图] 更新孔位 {hole_id} 状态")
            else:
                # 不打印警告，避免日志过多
                pass
        except Exception as e:
            print(f"⚠️ [小型全景图] 更新失败: {e}")'''
    
    # 在类的末尾添加
    content = content.rstrip() + method_code + "\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 方法添加完成")

def fix_overall_layout():
    """修复整体布局比例"""
    print("\n🔧 修复整体布局...")
    
    filepath = "src/main_window.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在创建主分割器后设置比例
    if "main_splitter.setSizes" not in content:
        pattern = r'(main_splitter\.addWidget\(sidebar_container\))'
        replacement = r'''\1
        
        # 设置初始大小比例（侧边栏:主内容 = 1:4）
        main_splitter.setSizes([300, 1200])'''
        
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 整体布局修复完成")

def verify_syntax():
    """验证所有文件的语法"""
    print("\n🔍 验证语法...")
    
    files = [
        "src/main_window.py",
        "src/aidcis2/graphics/dynamic_sector_view.py",
        "src/aidcis2/graphics/hole_item.py",
        "src/aidcis2/graphics/graphics_view.py"
    ]
    
    all_good = True
    for filepath in files:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', filepath],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath}")
            print(result.stderr)
            all_good = False
    
    return all_good

def test_window_display():
    """测试窗口是否能正常显示"""
    print("\n🧪 测试窗口显示...")
    
    test_script = '''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import subprocess

# 启动实际程序
process = subprocess.Popen([sys.executable, 'run_project.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.STDOUT,
                          text=True)

# 等待并收集输出
import time
start_time = time.time()
success_indicators = {
    "startup": False,
    "window_shown": False,
    "data_loaded": False,
    "no_errors": True
}

print("等待程序启动...")
while time.time() - start_time < 20:
    line = process.stdout.readline()
    if line:
        line = line.strip()
        if "启动完成" in line:
            success_indicators["startup"] = True
            print("✅ 程序启动成功")
        elif "显示主窗口" in line or "系统启动成功" in line:
            success_indicators["window_shown"] = True
            print("✅ 窗口显示成功")
        elif "DXF解析成功" in line:
            success_indicators["data_loaded"] = True
            print("✅ 数据加载成功")
        elif "Error" in line or "Exception" in line:
            success_indicators["no_errors"] = False
            print(f"❌ 错误: {line}")

# 终止进程
process.terminate()

# 显示结果
print("\\n测试结果:")
all_pass = all(success_indicators.values())
for key, value in success_indicators.items():
    status = "✅" if value else "❌"
    print(f"{status} {key}")

if all_pass:
    print("\\n✅ 所有测试通过！窗口可以正常显示")
else:
    print("\\n❌ 有测试失败，请检查问题")
'''
    
    # 写入测试脚本
    with open('test_display.py', 'w') as f:
        f.write(test_script)
    
    # 运行测试
    result = subprocess.run([sys.executable, 'test_display.py'], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("错误输出:", result.stderr)
    
    # 清理
    os.remove('test_display.py')
    
    return "所有测试通过" in result.stdout

def main():
    print("=" * 60)
    print("修复所有问题并测试")
    print("=" * 60)
    
    # 执行所有修复
    fix_sector_view_autoscale()
    fix_mini_panorama_size_and_center()
    fix_rendering_colors()
    ensure_method_exists()
    fix_overall_layout()
    
    # 验证语法
    if not verify_syntax():
        print("\n❌ 语法验证失败，请检查错误")
        return
    
    # 测试窗口显示
    print("\n" + "=" * 60)
    print("开始测试窗口显示")
    print("=" * 60)
    
    if test_window_display():
        print("\n" + "=" * 60)
        print("✅ 所有修复完成且测试通过！")
        print("\n修复内容总结：")
        print("1. ✅ 扇形视图使用自适应缩放而非固定大小")
        print("2. ✅ 小型全景图限制为200x200并正确居中")
        print("3. ✅ 孔位颜色渲染使用明亮颜色")
        print("4. ✅ 添加了缺失的方法避免错误")
        print("5. ✅ 优化了整体布局比例")
        print("\n现在程序应该能正常显示了！")
    else:
        print("\n⚠️ 测试未完全通过，可能还有问题需要解决")

if __name__ == "__main__":
    import os
    main()