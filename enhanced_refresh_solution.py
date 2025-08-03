
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
