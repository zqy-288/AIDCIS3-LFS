#!/usr/bin/env python3
"""修复中间视图显示问题的脚本"""

import sys
from pathlib import Path

# 找到要修改的文件
file_path = Path(__file__).parent / "src/pages/main_detection_p1/native_main_detection_view_p1.py"

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并修改 load_hole_collection 方法中的数据加载部分
# 确保在加载数据后立即调用 fit_in_view_with_margin
old_code = """                # 加载数据到中间面板的graphics_view
                if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
                    graphics_view = self.center_panel.graphics_view
                    if hasattr(graphics_view, 'load_holes'):
                        graphics_view.load_holes(self.current_hole_collection)
                        self.logger.info("✅ 中间面板graphics_view数据加载完成")
                    else:
                        self.logger.warning("⚠️ graphics_view没有 load_holes 方法")
                else:
                    self.logger.warning("⚠️ 中间面板没有 graphics_view 属性")"""

new_code = """                # 加载数据到中间面板的graphics_view
                if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
                    graphics_view = self.center_panel.graphics_view
                    if hasattr(graphics_view, 'load_holes'):
                        graphics_view.load_holes(self.current_hole_collection)
                        self.logger.info("✅ 中间面板graphics_view数据加载完成")
                        
                        # 确保数据加载后正确显示
                        if hasattr(graphics_view, 'fit_in_view_with_margin'):
                            graphics_view.fit_in_view_with_margin()
                            self.logger.info("✅ 视图已调整到合适大小")
                    else:
                        self.logger.warning("⚠️ graphics_view没有 load_holes 方法")
                else:
                    self.logger.warning("⚠️ 中间面板没有 graphics_view 属性")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 文件已更新")
else:
    print("❌ 未找到要修改的代码")

print("\n建议重启应用程序以查看效果")