#!/usr/bin/env python3
"""
修复蓝色到绿色/红色的渲染延迟问题
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def analyze_rendering_issue():
    """分析渲染延迟问题"""
    print("=== 分析蓝色到绿色/红色的渲染延迟问题 ===\n")
    
    # 检查关键文件
    files_to_check = [
        "src/pages/main_detection_p1/components/simulation_controller.py",
        "src/core_business/graphics/hole_item.py",
        "src/core_business/graphics/graphics_view.py"
    ]
    
    issues = []
    
    # 1. 检查simulation_controller
    sim_path = project_root / files_to_check[0]
    with open(sim_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "QApplication.processEvents" in content:
        print("✅ simulation_controller 已包含 processEvents 调用")
    else:
        issues.append("simulation_controller 缺少强制事件处理")
        
    # 2. 检查hole_item的update_appearance
    hole_item_path = project_root / files_to_check[1]
    with open(hole_item_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "view.viewport().update(" in content:
        print("✅ hole_item 包含视口强制更新")
    else:
        issues.append("hole_item 可能需要更强的刷新机制")
        
    return issues


def create_enhanced_refresh_solution():
    """创建增强的刷新解决方案"""
    
    solution_code = '''
def _finalize_current_pair_status_enhanced(self):
    """增强版：9.5秒后确定当前孔位的最终状态，确保颜色立即更新"""
    self.logger.info(f"🔄 开始更新检测单元的最终状态")
    if not self.current_detecting_pair:
        self.logger.warning("⚠️ 没有当前检测配对，跳过状态更新")
        return
        
    current_unit = self.current_detecting_pair
    
    # 处理HolePair检测的最终状态
    self.logger.info(f"🎯 处理配对单元，包含 {len(current_unit.holes)} 个孔位")
    
    # 收集需要更新的孔位
    holes_to_update = []
    for hole in current_unit.holes:
        final_status = self._simulate_detection_result()
        holes_to_update.append((hole.hole_id, final_status))
        
    # 批量更新，减少重绘次数
    for hole_id, final_status in holes_to_update:
        self.logger.info(f"📋 更新孔位 {hole_id}: 清除蓝色，设置最终状态 {final_status.value}")
        self._update_hole_status(hole_id, final_status, color_override=None)
        status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
        self.logger.info(f"📋 配对检测 {hole_id}: {status_text}")
    
    # 清除当前检测配对
    self.current_detecting_pair = None
    
    # 强制刷新所有视图 - 多层保证
    self._force_complete_refresh()
    
def _force_complete_refresh(self):
    """强制完整刷新，确保颜色更新立即可见"""
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication
    
    # 1. 先处理所有挂起的事件
    QApplication.processEvents(QEventLoop.AllEvents, 50)  # 最多处理50ms
    
    # 2. 强制刷新图形视图
    if self.graphics_view:
        # 强制重绘
        self.graphics_view.viewport().repaint()
        # 更新场景
        if hasattr(self.graphics_view, 'scene'):
            scene = self.graphics_view.scene
            if callable(scene):
                scene = scene()
            if scene:
                scene.update()
                # 让场景有时间处理更新
                QApplication.processEvents(QEventLoop.AllEvents, 10)
    
    # 3. 强制刷新全景图
    if self.panorama_widget:
        self.panorama_widget.repaint()
        if hasattr(self.panorama_widget, 'panorama_view'):
            self.panorama_widget.panorama_view.viewport().repaint()
    
    # 4. 最后再处理一次事件，确保所有更新都被执行
    QApplication.processEvents(QEventLoop.AllEvents, 10)
'''
    
    print("\n=== 增强的刷新解决方案 ===")
    print(solution_code)
    
    # 保存解决方案
    with open(project_root / "enhanced_refresh_solution.py", 'w', encoding='utf-8') as f:
        f.write(solution_code)
    
    print("\n✅ 解决方案已保存到 enhanced_refresh_solution.py")


def suggest_immediate_fixes():
    """建议立即可用的修复"""
    print("\n=== 立即可用的修复建议 ===\n")
    
    print("1. 在 _finalize_current_pair_status 方法末尾添加更强的刷新:")
    print("""
    # 在清除当前检测配对后添加
    self.current_detecting_pair = None
    
    # 强制刷新中间视图
    if self.graphics_view:
        self.graphics_view.viewport().repaint()  # 使用 repaint 而不是 update
        
    # 强制刷新全景图
    if self.panorama_widget:
        self.panorama_widget.repaint()
        
    # 给UI一点时间来处理重绘
    from PySide6.QtCore import QTimer
    QTimer.singleShot(10, lambda: None)  # 10ms延迟
""")
    
    print("\n2. 在 hole_item.py 的 clear_color_override 方法中增强刷新:")
    print("""
    def clear_color_override(self):
        \"\"\"清除颜色覆盖\"\"\"
        if self._color_override is not None:
            self._color_override = None
            self.update_appearance()
            # 强制场景更新这个项
            if self.scene():
                self.scene().update(self.sceneBoundingRect())
            # 更新提示框文本
            self.setToolTip(self._create_tooltip())
""")
    
    print("\n3. 考虑降低更新频率，让UI有更多时间处理渲染:")
    print("   - 将检测间隔从10秒增加到11-12秒")
    print("   - 或在状态更新之间添加小延迟")


def main():
    """主函数"""
    # 分析问题
    issues = analyze_rendering_issue()
    
    if issues:
        print(f"\n发现 {len(issues)} 个潜在问题:")
        for issue in issues:
            print(f"  - {issue}")
    
    # 创建解决方案
    create_enhanced_refresh_solution()
    
    # 建议立即修复
    suggest_immediate_fixes()
    
    print("\n=== 总结 ===")
    print("蓝色没有及时变成绿色/红色的原因：")
    print("1. Qt的事件循环可能被阻塞或延迟")
    print("2. 视图更新使用了 update() 而不是 repaint()")
    print("3. 场景和视口的更新可能没有立即执行")
    print("\n建议使用 repaint() 和 processEvents() 的组合来强制立即更新。")


if __name__ == "__main__":
    main()