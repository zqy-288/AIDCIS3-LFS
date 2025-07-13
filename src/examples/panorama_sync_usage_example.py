"""
全景图同步系统使用示例
演示如何在主应用中集成和使用基于数据库驱动的全景图更新系统
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aidcis2.data_management.panorama_sync_manager import PanoramaSyncManager, StatusUpdateBuffer
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleStatus
from modules.models import DatabaseManager


class PanoramaSyncIntegrationExample:
    """全景图同步系统集成示例"""
    
    def __init__(self):
        # 1. 初始化数据库管理器
        self.db_manager = DatabaseManager("sqlite:///example_detection_system.db")
        self.db_manager.create_tables()
        print("✅ 数据库管理器初始化完成")
        
        # 2. 创建全景图组件
        self.panorama_widget = CompletePanoramaWidget()
        print("✅ 全景图组件创建完成")
        
        # 3. 创建同步管理器
        self.sync_manager = PanoramaSyncManager(self.db_manager, self.panorama_widget)
        print("✅ 同步管理器创建完成")
        
        # 4. 设置全景图组件的同步管理器
        self.panorama_widget.set_panorama_sync_manager(self.sync_manager)
        print("✅ 全景图与同步管理器关联完成")
        
        # 5. 创建状态更新缓冲区（可选，用于批量处理）
        self.status_buffer = StatusUpdateBuffer(
            self.db_manager, 
            buffer_size=20,      # 20个更新后刷新
            flush_interval=2.0   # 或2秒后刷新
        )
        print("✅ 状态更新缓冲区创建完成")
        
        # 创建一些示例数据
        self._create_example_data()
    
    def _create_example_data(self):
        """创建示例数据"""
        print("\\n📊 创建示例数据...")
        
        # 创建示例工件（如果不存在）
        session = self.db_manager.get_session()
        try:
            from modules.models import Workpiece, Hole
            
            # 检查是否已有数据
            existing_workpiece = session.query(Workpiece).filter_by(workpiece_id="EXAMPLE-001").first()
            if existing_workpiece:
                print("   示例数据已存在，跳过创建")
                return
            
            # 创建工件
            workpiece = Workpiece(
                workpiece_id="EXAMPLE-001",
                name="示例管板工件",
                type="tube_plate",
                hole_count=25
            )
            session.add(workpiece)
            session.flush()
            
            # 创建25个孔位
            for i in range(25):
                hole = Hole(
                    hole_id=f"H{i+1:03d}",
                    workpiece_id=workpiece.id,
                    position_x=(i % 5) * 50.0,
                    position_y=(i // 5) * 50.0,
                    target_diameter=25.0,
                    tolerance=0.1,
                    status='pending'
                )
                session.add(hole)
            
            session.commit()
            print(f"   创建了工件 {workpiece.workpiece_id} 和 25 个孔位")
            
        except Exception as e:
            session.rollback()
            print(f"   ❌ 创建示例数据失败: {e}")
        finally:
            self.db_manager.close_session(session)
    
    def start_sync_system(self):
        """启动同步系统"""
        print("\\n🚀 启动全景图同步系统...")
        
        # 启动自动同步，间隔1秒
        self.sync_manager.start_sync(interval_ms=1000)
        
        # 启用全景图的数据库同步模式
        self.panorama_widget.enable_db_sync(True)
        
        print("   ✅ 自动同步已启动 (1秒间隔)")
        print("   ✅ 全景图数据库同步模式已启用")
        
        # 连接同步完成信号（可选）
        self.sync_manager.sync_completed.connect(self._on_sync_completed)
        self.sync_manager.sync_error.connect(self._on_sync_error)
        print("   ✅ 同步信号已连接")
    
    def _on_sync_completed(self, update_count):
        """同步完成回调"""
        print(f"   📊 同步完成: {update_count} 个更新")
    
    def _on_sync_error(self, error_message):
        """同步错误回调"""
        print(f"   ❌ 同步错误: {error_message}")
    
    def simulate_detection_process(self):
        """模拟检测过程"""
        print("\\n🔍 模拟检测过程...")
        
        # 模拟检测25个孔位
        hole_ids = [f"H{i+1:03d}" for i in range(25)]
        
        for i, hole_id in enumerate(hole_ids):
            # 模拟检测延迟
            time.sleep(0.5)
            
            # 随机生成检测结果
            import random
            statuses = ['qualified', 'defective', 'blind']
            weights = [0.8, 0.15, 0.05]  # 80%合格，15%缺陷，5%盲孔
            status = random.choices(statuses, weights=weights)[0]
            
            # 方法1：直接更新到数据库（推荐）
            success = self.db_manager.update_hole_status(
                hole_id=hole_id,
                new_status=status,
                update_source="simulated_detection",
                operator_id="demo_system",
                batch_id=f"demo_batch_{int(time.time())}"
            )
            
            if success:
                print(f"   🔍 检测完成: {hole_id} -> {status}")
            else:
                print(f"   ❌ 检测更新失败: {hole_id}")
            
            # 每5个孔位显示一次同步状态
            if (i + 1) % 5 == 0:
                self._show_sync_status()
        
        print("   ✅ 模拟检测完成")
    
    def simulate_detection_with_buffer(self):
        """使用缓冲区模拟检测过程"""
        print("\\n🔍 使用缓冲区模拟检测过程...")
        
        hole_ids = [f"H{i+1:03d}" for i in range(25)]
        
        for i, hole_id in enumerate(hole_ids):
            time.sleep(0.2)  # 更快的检测
            
            import random
            status = random.choice(['qualified', 'defective', 'processing'])
            
            # 方法2：使用缓冲区（适合高频更新）
            self.status_buffer.add_update(
                hole_id=hole_id,
                new_status=status,
                update_source="buffered_detection",
                operator_id="demo_system",
                batch_id=f"buffered_batch_{int(time.time())}"
            )
            
            print(f"   🔍 缓冲区检测: {hole_id} -> {status}")
            
            if (i + 1) % 8 == 0:
                print("   💾 触发缓冲区刷新...")
        
        # 确保所有缓冲的更新都被处理
        self.status_buffer.flush()
        print("   ✅ 缓冲区检测完成")
    
    def _show_sync_status(self):
        """显示同步状态"""
        stats = self.sync_manager.get_sync_stats()
        db_stats = stats.get('db_stats', {})
        
        print(f"   📊 同步状态: 待同步 {db_stats.get('pending_updates', 0)}, "
              f"已同步 {db_stats.get('synced_updates', 0)}, "
              f"同步率 {db_stats.get('sync_rate', 0):.1f}%")
    
    def demonstrate_manual_operations(self):
        """演示手动操作"""
        print("\\n🔧 演示手动操作...")
        
        # 手动更新几个孔位
        manual_updates = [
            ("H001", "defective", "手动复检发现缺陷"),
            ("H002", "qualified", "手动复检确认合格"),
            ("H003", "blind", "手动标记为盲孔")
        ]
        
        for hole_id, status, reason in manual_updates:
            success = self.db_manager.update_hole_status(
                hole_id=hole_id,
                new_status=status,
                update_source="manual_inspection",
                operator_id="operator_001"
            )
            
            if success:
                print(f"   ✋ 手动更新: {hole_id} -> {status} ({reason})")
        
        # 强制立即同步
        print("   ⚡ 强制立即同步...")
        self.sync_manager.force_sync()
        
        # 显示最终状态
        time.sleep(1)  # 等待同步完成
        self._show_sync_status()
    
    def demonstrate_batch_operations(self):
        """演示批量操作"""
        print("\\n📦 演示批量操作...")
        
        # 批量更新多个孔位（直接调用全景图方法）
        batch_updates = {
            "H020": HoleStatus.QUALIFIED,
            "H021": HoleStatus.DEFECTIVE, 
            "H022": HoleStatus.BLIND,
            "H023": HoleStatus.PROCESSING,
            "H024": HoleStatus.QUALIFIED
        }
        
        print(f"   📦 批量更新 {len(batch_updates)} 个孔位...")
        
        # 方法3：直接调用全景图批量更新（跳过数据库）
        self.panorama_widget.batch_update_hole_status(batch_updates)
        
        print("   ✅ 批量更新完成（直接全景图）")
    
    def show_final_statistics(self):
        """显示最终统计信息"""
        print("\\n📊 最终统计信息...")
        
        # 同步管理器统计
        sync_stats = self.sync_manager.get_sync_stats()
        print("\\n同步管理器统计:")
        print(f"   总同步次数: {sync_stats['total_synced']}")
        print(f"   同步错误次数: {sync_stats['sync_errors']}")
        print(f"   上次同步时间: {sync_stats['last_sync_time']}")
        print(f"   自动同步状态: {'启用' if sync_stats['auto_sync_enabled'] else '禁用'}")
        
        # 数据库统计
        db_stats = sync_stats.get('db_stats', {})
        if db_stats:
            print("\\n数据库统计:")
            print(f"   总更新记录: {db_stats['total_updates']}")
            print(f"   待同步记录: {db_stats['pending_updates']}")
            print(f"   已同步记录: {db_stats['synced_updates']}")
            print(f"   同步完成率: {db_stats['sync_rate']:.1f}%")
        
        # 全景图组件统计
        if hasattr(self.panorama_widget, 'get_update_status'):
            panorama_status = self.panorama_widget.get_update_status()
            print("\\n全景图组件统计:")
            print(f"   待更新缓存: {panorama_status['pending_updates']}")
            print(f"   定时器状态: {'活跃' if panorama_status['timer_active'] else '非活跃'}")
            print(f"   批量更新间隔: {panorama_status['update_interval']}ms")
    
    def cleanup(self):
        """清理资源"""
        print("\\n🧹 清理资源...")
        
        # 停止同步
        self.sync_manager.stop_sync()
        
        # 刷新缓冲区
        self.status_buffer.flush()
        
        # 禁用全景图数据库同步
        self.panorama_widget.enable_db_sync(False)
        
        print("   ✅ 资源清理完成")


def main():
    """主函数：运行完整示例"""
    print("🎯 全景图同步系统集成示例")
    print("=" * 50)
    
    try:
        # 创建示例实例
        example = PanoramaSyncIntegrationExample()
        
        # 启动同步系统
        example.start_sync_system()
        
        # 等待初始化完成
        time.sleep(1)
        
        # 模拟不同的检测场景
        example.simulate_detection_process()
        
        time.sleep(2)  # 等待同步完成
        
        example.simulate_detection_with_buffer()
        
        time.sleep(2)  # 等待同步完成
        
        example.demonstrate_manual_operations()
        
        time.sleep(1)
        
        example.demonstrate_batch_operations()
        
        time.sleep(2)  # 等待最后的同步
        
        # 显示最终统计
        example.show_final_statistics()
        
        # 清理
        example.cleanup()
        
        print("\\n🎉 示例运行完成！")
        
    except KeyboardInterrupt:
        print("\\n⚠️ 用户中断示例运行")
    except Exception as e:
        print(f"\\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


def integration_checklist():
    """集成检查清单"""
    print("\\n📋 全景图同步系统集成检查清单")
    print("=" * 50)
    
    checklist = [
        "✅ 1. 创建 DatabaseManager 实例",
        "✅ 2. 调用 db_manager.create_tables() 确保表结构存在", 
        "✅ 3. 创建 CompletePanoramaWidget 实例",
        "✅ 4. 创建 PanoramaSyncManager 实例，传入数据库管理器和全景图组件",
        "✅ 5. 调用 panorama_widget.set_panorama_sync_manager(sync_manager)",
        "✅ 6. 调用 sync_manager.start_sync() 启动自动同步",
        "✅ 7. 调用 panorama_widget.enable_db_sync(True) 启用数据库同步模式",
        "✅ 8. 在检测系统中使用 db_manager.update_hole_status() 更新状态",
        "✅ 9. （可选）使用 StatusUpdateBuffer 进行批量处理",
        "✅ 10. 在应用关闭时调用 sync_manager.stop_sync() 清理资源"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\\n💡 关键集成要点:")
    print("   • 数据库驱动：状态更新写入数据库，同步管理器定期读取")
    print("   • 批量优化：自动批量处理多个更新，提高性能")
    print("   • 容错机制：即使全景图组件出错，状态更新也不会丢失")
    print("   • 可监控性：提供详细的同步统计和状态信息")
    print("   • 向后兼容：保留原有的直接更新接口")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='全景图同步系统示例')
    parser.add_argument('--mode', choices=['example', 'checklist'], 
                       default='example', help='运行模式')
    
    args = parser.parse_args()
    
    if args.mode == 'example':
        main()
    elif args.mode == 'checklist':
        integration_checklist()