#!/usr/bin/env python3
"""
增强颜色刷新机制 - 确保蓝色覆盖能正确清除
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def enhance_hole_item_refresh():
    """增强 HoleGraphicsItem 的刷新机制"""
    
    hole_item_path = project_root / "src/core_business/graphics/hole_item.py"
    
    with open(hole_item_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 clear_color_override 方法
    if "def clear_color_override(self):" in content:
        # 增强刷新逻辑
        old_method = """    def clear_color_override(self):
        \"\"\"清除颜色覆盖\"\"\"
        if self._color_override is not None:
            self._color_override = None
            self.update_appearance()"""
            
        new_method = """    def clear_color_override(self):
        \"\"\"清除颜色覆盖\"\"\"
        if self._color_override is not None:
            self._color_override = None
            self.update_appearance()
            # 增强刷新 - 确保颜色更新立即生效
            self.prepareGeometryChange()  # 通知Qt几何可能改变
            self.update()  # 强制重绘
            if self.scene():
                # 更新场景中的特定区域
                self.scene().update(self.sceneBoundingRect())"""
        
        if old_method in content:
            content = content.replace(old_method, new_method)
            print("✅ 增强了 clear_color_override 方法")
        else:
            print("⚠️ clear_color_override 方法格式不匹配，请手动检查")
    
    # 同样处理 set_color_override
    if "def set_color_override(self, color_override):" in content:
        old_set = """    def set_color_override(self, color_override):
        \"\"\"设置颜色覆盖（用于蓝色检测中状态）\"\"\"
        if self._color_override != color_override:
            self._color_override = color_override
            self.update_appearance()"""
            
        new_set = """    def set_color_override(self, color_override):
        \"\"\"设置颜色覆盖（用于蓝色检测中状态）\"\"\"
        if self._color_override != color_override:
            self._color_override = color_override
            self.update_appearance()
            # 增强刷新
            self.prepareGeometryChange()
            self.update()"""
        
        if old_set in content:
            content = content.replace(old_set, new_set)
            print("✅ 增强了 set_color_override 方法")
    
    # 保存修改
    with open(hole_item_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ HoleGraphicsItem 刷新机制增强完成")


def enhance_graphics_view_refresh():
    """增强 OptimizedGraphicsView 的刷新机制"""
    
    view_path = project_root / "src/core_business/graphics/graphics_view.py"
    
    with open(view_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 update_hole_status 方法
    method_start = content.find("def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):")
    if method_start != -1:
        # 找到方法结束位置
        method_end = content.find("\n    def ", method_start + 1)
        if method_end == -1:
            method_end = len(content)
        
        method_content = content[method_start:method_end]
        
        # 检查是否已经有 processEvents
        if "QApplication.processEvents()" not in method_content:
            # 在方法末尾添加事件处理
            insert_pos = method_end - 1
            while insert_pos > method_start and content[insert_pos] in [' ', '\n']:
                insert_pos -= 1
            
            addition = """
            # 确保UI事件得到处理
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()"""
            
            content = content[:insert_pos+1] + addition + content[insert_pos+1:]
            print("✅ 增强了 update_hole_status 方法的事件处理")
    
    # 保存修改
    with open(view_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ OptimizedGraphicsView 刷新机制增强完成")


def main():
    """主函数"""
    print("=== 增强颜色刷新机制 ===\n")
    
    # 增强 HoleGraphicsItem
    enhance_hole_item_refresh()
    
    # 增强 OptimizedGraphicsView
    enhance_graphics_view_refresh()
    
    print("\n=== 增强完成 ===")
    print("\n注意事项：")
    print("1. 修改已应用到源文件")
    print("2. 请重新运行主程序测试效果")
    print("3. 如果问题仍然存在，可能需要检查模拟控制器的定时器精度")


if __name__ == "__main__":
    main()