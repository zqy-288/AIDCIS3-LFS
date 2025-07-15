#!/usr/bin/env python3
"""
综合修复扇形偏移问题
解决所有可能绕过保护标志的代码路径
"""

import re
from pathlib import Path

def fix_offset_issues():
    """综合修复偏移问题"""
    
    print("🔧 开始综合修复扇形偏移问题")
    print("=" * 60)
    
    # 修复 graphics_view.py 中的问题
    fix_graphics_view_issues()
    
    # 修复 dynamic_sector_view.py 中的问题
    fix_dynamic_sector_view_issues()
    
    print("\n✅ 综合修复完成！")

def fix_graphics_view_issues():
    """修复 graphics_view.py 中的问题"""
    
    print("\n1. 修复 graphics_view.py 中的问题:")
    
    graphics_view_file = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "graphics_view.py"
    
    with open(graphics_view_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 _ensure_perfect_centering 方法，添加 disable_auto_fit 保护
    old_centering_method = re.search(r'def _ensure_perfect_centering\(self, target_center: QPointF\):.*?(?=def|\Z)', content, re.DOTALL)
    if old_centering_method:
        old_method = old_centering_method.group(0)
        
        # 添加 disable_auto_fit 保护
        new_method = old_method.replace(
            'def _ensure_perfect_centering(self, target_center: QPointF):',
            '''def _ensure_perfect_centering(self, target_center: QPointF):
        """确保内容精确居中显示"""
        # 【增强保护】如果禁用了自动适配，则跳过精确居中
        if getattr(self, 'disable_auto_fit', False):
            self.logger.info("跳过精确居中（disable_auto_fit=True）")
            return'''
        )
        
        content = content.replace(old_method, new_method)
        print("  ✅ 已修复 _ensure_perfect_centering 方法，添加 disable_auto_fit 保护")
    
    # 修复 set_macro_view_scale 方法，添加 disable_auto_center 保护
    old_macro_scale = re.search(r'def set_macro_view_scale\(self\):.*?(?=def|\Z)', content, re.DOTALL)
    if old_macro_scale:
        old_method = old_macro_scale.group(0)
        
        # 在方法开头添加保护检查
        new_method = old_method.replace(
            'def set_macro_view_scale(self):',
            '''def set_macro_view_scale(self):
        """设置宏观视图的适当缩放比例"""
        # 【增强保护】如果禁用了自动适配，则跳过宏观视图缩放
        if getattr(self, 'disable_auto_fit', False):
            self.logger.info("跳过 set_macro_view_scale（disable_auto_fit=True）")
            return'''
        )
        
        content = content.replace(old_method, new_method)
        print("  ✅ 已修复 set_macro_view_scale 方法，添加 disable_auto_fit 保护")
    
    # 写入修复后的文件
    with open(graphics_view_file, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_dynamic_sector_view_issues():
    """修复 dynamic_sector_view.py 中的问题"""
    
    print("\n2. 修复 dynamic_sector_view.py 中的问题:")
    
    dynamic_sector_file = Path(__file__).parent / "src" / "aidcis2" / "graphics" / "dynamic_sector_view.py"
    
    with open(dynamic_sector_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 _apply_fill_view_strategy 中的 centerOn 调用
    old_fill_method = re.search(r'def _apply_fill_view_strategy\(self\):.*?(?=def|\Z)', content, re.DOTALL)
    if old_fill_method:
        old_method = old_fill_method.group(0)
        
        # 将 centerOn 调用替换为保护的版本
        new_method = old_method.replace(
            'self.graphics_view.centerOn(visual_center)',
            '''# 【增强保护】只有在未禁用自动居中时才调用 centerOn
        if not getattr(self.graphics_view, 'disable_auto_center', False):
            self.graphics_view.centerOn(visual_center)
            print(f"🎯 [动态扇形] 已将视觉中心对齐到视图中心")
        else:
            print(f"🛡️ [动态扇形] 跳过 centerOn（disable_auto_center=True）")'''
        )
        
        content = content.replace(old_method, new_method)
        print("  ✅ 已修复 _apply_fill_view_strategy 中的 centerOn 调用")
    
    # 添加偏移状态监控方法
    monitoring_method = '''
    def monitor_offset_state(self):
        """监控偏移状态并在必要时恢复"""
        if not self.sector_offset_enabled:
            return
            
        # 检查保护标志是否被意外重置
        if hasattr(self, 'graphics_view'):
            if not getattr(self.graphics_view, 'disable_auto_fit', False):
                self.graphics_view.disable_auto_fit = True
                print("🔧 [监控] 恢复 disable_auto_fit 标志")
                
            if not getattr(self.graphics_view, 'disable_auto_center', False):
                self.graphics_view.disable_auto_center = True
                print("🔧 [监控] 恢复 disable_auto_center 标志")
    
    def force_apply_offset(self):
        """强制应用偏移设置"""
        if not self.sector_offset_enabled or not hasattr(self, 'graphics_view'):
            return
            
        try:
            # 获取视口信息
            viewport_rect = self.graphics_view.viewport().rect()
            if viewport_rect.width() <= 0:
                return
                
            # 计算偏移像素
            offset_pixels = viewport_rect.width() * self.sector_offset_ratio
            
            # 方法1：使用滚动条
            h_bar = self.graphics_view.horizontalScrollBar()
            if h_bar and h_bar.isVisible():
                current_value = h_bar.value()
                center_value = (h_bar.minimum() + h_bar.maximum()) / 2
                target_value = center_value + int(offset_pixels)
                target_value = max(h_bar.minimum(), min(h_bar.maximum(), target_value))
                
                if abs(current_value - target_value) > 5:  # 只有显著差异时才调整
                    h_bar.setValue(target_value)
                    print(f"🎚️ [强制偏移] 滚动条: {current_value} -> {target_value}")
            
            # 方法2：使用变换矩阵
            else:
                transform = self.graphics_view.transform()
                # 计算当前偏移
                current_offset = transform.dx()
                target_offset = offset_pixels
                
                if abs(current_offset - target_offset) > 5:
                    # 重置变换并应用偏移
                    transform.reset()
                    transform.translate(target_offset, 0)
                    self.graphics_view.setTransform(transform)
                    print(f"🔄 [强制偏移] 变换矩阵: dx={target_offset:.1f}")
                    
        except Exception as e:
            print(f"❌ [强制偏移] 失败: {e}")
'''
    
    # 在类的末尾添加监控方法
    class_end = content.rfind('\n\n')
    if class_end != -1:
        content = content[:class_end] + monitoring_method + content[class_end:]
        print("  ✅ 已添加偏移状态监控方法")
    
    # 修改 set_sector_offset_config 方法，添加延时监控
    old_config_method = re.search(r'def set_sector_offset_config\(self, ratio: float = None, enabled: bool = None\):.*?(?=def|\Z)', content, re.DOTALL)
    if old_config_method:
        old_method = old_config_method.group(0)
        
        # 在方法末尾添加延时监控
        new_method = old_method.replace(
            'self.switch_to_sector(self.current_sector)',
            '''self.switch_to_sector(self.current_sector)
            
            # 【增强保护】延时监控偏移状态
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.monitor_offset_state)
            QTimer.singleShot(300, self.monitor_offset_state)
            QTimer.singleShot(500, self.force_apply_offset)'''
        )
        
        content = content.replace(old_method, new_method)
        print("  ✅ 已在 set_sector_offset_config 中添加延时监控")
    
    # 写入修复后的文件
    with open(dynamic_sector_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_offset_issues()
    
    print(f"\n🎯 修复重点:")
    print(f"  1. 修复了 _ensure_perfect_centering 绕过保护标志的问题")
    print(f"  2. 修复了 set_macro_view_scale 缺少保护的问题")
    print(f"  3. 修复了 _apply_fill_view_strategy 中的 centerOn 调用")
    print(f"  4. 添加了偏移状态监控和恢复机制")
    print(f"  5. 添加了强制偏移应用方法")
    
    print(f"\n🔄 下一步测试:")
    print(f"  1. 重启应用程序")
    print(f"  2. 导入DXF文件")
    print(f"  3. 调整扇形偏移设置")
    print(f"  4. 观察控制台日志确认修复效果")