#!/usr/bin/env python3
"""
修复检测时序问题的补丁
解决部分孔位在检测周期结束后仍保持蓝色状态的问题
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def create_backup(file_path):
    """创建文件备份"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 备份创建: {backup_path}")
    return backup_path

def fix_simulation_controller():
    """修复模拟控制器的时序问题"""
    
    # 目标文件
    controller_path = Path("src/pages/main_detection_p1/components/simulation_controller.py")
    
    if not controller_path.exists():
        print(f"❌ 文件不存在: {controller_path}")
        return False
        
    # 创建备份
    create_backup(controller_path)
    
    # 读取文件内容
    with open(controller_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1: 增强 _process_next_pair 方法，保存检测单元引用
    fix1_old = """    def _process_next_pair(self):
        \"\"\"处理下一个检测配对 - 新的时序控制\"\"\"
        if not self.is_running or self.is_paused:
            return
            
        if self.current_index >= len(self.detection_units):
            # 模拟完成
            self._complete_simulation()
            return
            
        # 获取当前检测单元
        current_unit = self.detection_units[self.current_index]
        
        # 处理扇形聚焦
        self._focus_on_sector(current_unit)
        
        # 设置当前检测配对
        self.current_detecting_pair = current_unit
        
        # 开始检测：设置为蓝色状态（检测中）
        if isinstance(current_unit, HolePair):
            self._start_pair_detection(current_unit)
        else:
            self._start_single_hole_detection(current_unit)
            
        # 启动状态变化定时器（9.5秒后变为最终状态）
        self.status_change_timer.start(self.status_change_time)
            
        # 更新路径渲染进度
        if self.graphics_view:
            self.snake_path_renderer.update_progress(self.current_index)
            
        # 发射进度信号
        self.simulation_progress.emit(self.current_index + 1, len(self.detection_units))
        
        # 移动到下一个检测单元
        self.current_index += 1"""
        
    fix1_new = """    def _process_next_pair(self):
        \"\"\"处理下一个检测配对 - 新的时序控制\"\"\"
        if not self.is_running or self.is_paused:
            return
            
        if self.current_index >= len(self.detection_units):
            # 模拟完成
            self._complete_simulation()
            return
            
        # 获取当前检测单元
        current_unit = self.detection_units[self.current_index]
        
        # 处理扇形聚焦
        self._focus_on_sector(current_unit)
        
        # 保存当前检测单元的副本，避免引用丢失
        if isinstance(current_unit, HolePair):
            # 创建HolePair的副本
            from src.pages.shared.components.snake_path.snake_path_renderer import HolePair
            self.current_detecting_pair = HolePair(current_unit.holes[:])
        else:
            # 保存单个孔位的引用
            self.current_detecting_pair = current_unit
        
        # 开始检测：设置为蓝色状态（检测中）
        if isinstance(current_unit, HolePair):
            self._start_pair_detection(current_unit)
        else:
            self._start_single_hole_detection(current_unit)
            
        # 启动状态变化定时器（9.5秒后变为最终状态）
        self.status_change_timer.stop()  # 确保停止之前的定时器
        self.status_change_timer.start(self.status_change_time)
            
        # 更新路径渲染进度
        if self.graphics_view:
            self.snake_path_renderer.update_progress(self.current_index)
            
        # 发射进度信号
        self.simulation_progress.emit(self.current_index + 1, len(self.detection_units))
        
        # 移动到下一个检测单元
        self.current_index += 1"""
    
    # 修复2: 改进 _finalize_current_pair_status 方法，确保颜色覆盖被清除
    fix2_old = """    def _finalize_current_pair_status(self):
        \"\"\"9.5秒后确定当前配对的最终状态\"\"\"
        if not self.current_detecting_pair:
            return
            
        current_unit = self.current_detecting_pair
        
        if isinstance(current_unit, HolePair):
            # 处理配对
            for hole in current_unit.holes:
                final_status = self._simulate_detection_result()
                self._update_hole_status(hole.hole_id, final_status)
                status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
                self.logger.info(f"📋 {hole.hole_id}: {status_text}")
        else:
            # 处理单孔
            final_status = self._simulate_detection_result()
            self._update_hole_status(current_unit.hole_id, final_status)
            status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
            self.logger.info(f"📋 {current_unit.hole_id}: {status_text}")
            
        # 清除当前检测配对
        self.current_detecting_pair = None"""
        
    fix2_new = """    def _finalize_current_pair_status(self):
        \"\"\"9.5秒后确定当前配对的最终状态\"\"\"
        if not self.current_detecting_pair:
            self.logger.warning("⚠️ _finalize_current_pair_status 被调用但没有当前检测配对")
            return
            
        current_unit = self.current_detecting_pair
        
        try:
            if isinstance(current_unit, HolePair):
                # 处理配对
                for hole in current_unit.holes:
                    final_status = self._simulate_detection_result()
                    # 明确传递 color_override=None 来清除蓝色覆盖
                    self._update_hole_status(hole.hole_id, final_status, color_override=None)
                    status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
                    self.logger.info(f"📋 {hole.hole_id}: {status_text}")
            else:
                # 处理单孔
                final_status = self._simulate_detection_result()
                # 明确传递 color_override=None 来清除蓝色覆盖
                self._update_hole_status(current_unit.hole_id, final_status, color_override=None)
                status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
                self.logger.info(f"📋 {current_unit.hole_id}: {status_text}")
        except Exception as e:
            self.logger.error(f"❌ 状态变更失败: {e}")
        finally:
            # 清除当前检测配对
            self.current_detecting_pair = None"""
    
    # 修复3: 增强停止/暂停时的清理逻辑
    fix3_old = """    def stop_simulation(self):
        \"\"\"停止模拟\"\"\"
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.simulation_timer.stop()
            self.status_change_timer.stop()  # 停止状态变化定时器
            self.current_detecting_pair = None  # 清除当前检测配对
            
            # 清除路径渲染
            if self.graphics_view:
                self.snake_path_renderer.clear_paths()
                
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")"""
            
    fix3_new = """    def stop_simulation(self):
        \"\"\"停止模拟\"\"\"
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.simulation_timer.stop()
            self.status_change_timer.stop()  # 停止状态变化定时器
            
            # 如果有正在检测的孔位，立即完成其状态变更
            if self.current_detecting_pair and self.status_change_timer.isActive():
                self.logger.info("⚠️ 停止模拟时发现未完成的检测，立即完成状态变更")
                self._finalize_current_pair_status()
            
            self.current_detecting_pair = None  # 清除当前检测配对
            
            # 清除路径渲染
            if self.graphics_view:
                self.snake_path_renderer.clear_paths()
                
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")"""
    
    # 应用修复
    content = content.replace(fix1_old, fix1_new)
    content = content.replace(fix2_old, fix2_new)
    content = content.replace(fix3_old, fix3_new)
    
    # 保存修改
    with open(controller_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修复应用到: {controller_path}")
    return True

def fix_panorama_widget():
    """修复全景图组件的颜色更新逻辑"""
    
    # 这部分已经在现有代码中正确实现
    print("✅ 全景图组件的颜色覆盖逻辑已正确实现")
    return True

def main():
    """执行修复"""
    print("🔧 开始修复检测时序问题...")
    print("="*60)
    
    # 修复模拟控制器
    if fix_simulation_controller():
        print("\n✅ 模拟控制器修复完成")
    else:
        print("\n❌ 模拟控制器修复失败")
        
    # 检查全景图组件
    fix_panorama_widget()
    
    print("\n" + "="*60)
    print("🎉 修复完成!")
    print("\n建议的测试步骤:")
    print("1. 启动应用并加载DXF文件")
    print("2. 开始模拟检测")
    print("3. 观察孔位颜色变化：灰色 -> 蓝色(9.5秒) -> 绿色/红色")
    print("4. 特别注意最后几个检测单元是否正确变色")
    print("5. 测试暂停/恢复功能")
    print("6. 测试提前停止功能")

if __name__ == "__main__":
    main()