#!/usr/bin/env python3
"""
全景图第26列更新问题调试脚本
用于诊断为什么只有部分孔位被更新
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from modules.models import DatabaseManager
from aidcis2.data_management.panorama_sync_manager import PanoramaSyncManager


def analyze_panorama_update_issue():
    """分析全景图更新问题"""
    print("=" * 60)
    print("🔍 全景图第26列更新问题诊断")
    print("=" * 60)
    
    # 创建应用（某些Qt组件需要）
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 1. 检查数据库状态
    print("\n1️⃣ 检查数据库状态更新记录")
    check_database_updates()
    
    # 2. 分析孔位分布
    print("\n2️⃣ 分析孔位分布")
    analyze_hole_distribution()
    
    # 3. 测试全景图更新
    print("\n3️⃣ 测试全景图更新机制")
    test_panorama_update()
    
    # 4. 检查同步管理器状态
    print("\n4️⃣ 检查同步管理器配置")
    check_sync_manager_status()
    
    print("\n" + "=" * 60)
    print("诊断完成！")


def check_database_updates():
    """检查数据库中的状态更新记录"""
    db_manager = DatabaseManager()
    
    try:
        # 检查是否有hole_status_updates表
        session = db_manager.get_session()
        
        # 尝试查询hole_status_updates表
        try:
            from modules.models import HoleStatusUpdate
            
            # 获取最近的更新记录
            recent_updates = session.query(HoleStatusUpdate).order_by(
                HoleStatusUpdate.update_timestamp.desc()
            ).limit(20).all()
            
            if recent_updates:
                print(f"✅ 找到 {len(recent_updates)} 条最近的状态更新记录")
                
                # 分析更新的孔位ID格式
                id_formats = {}
                for update in recent_updates:
                    hole = update.hole
                    hole_id = hole.hole_id
                    
                    # 分类ID格式
                    if hole_id.startswith('('):
                        id_formats['tuple'] = id_formats.get('tuple', 0) + 1
                    elif hole_id.startswith('H'):
                        id_formats['H_format'] = id_formats.get('H_format', 0) + 1
                    else:
                        id_formats['other'] = id_formats.get('other', 0) + 1
                
                print(f"   孔位ID格式分布: {id_formats}")
                
                # 统计同步状态
                synced = sum(1 for u in recent_updates if u.sync_to_panorama)
                pending = len(recent_updates) - synced
                print(f"   同步状态: {synced} 已同步, {pending} 待同步")
                
            else:
                print("⚠️ hole_status_updates表存在但没有记录")
                print("   这表明新的数据库驱动更新机制可能未被使用")
                
        except Exception as e:
            print(f"❌ 无法访问hole_status_updates表: {e}")
            print("   新的数据库架构可能未正确初始化")
            
        # 检查holes表中的数据
        from modules.models import Hole
        total_holes = session.query(Hole).count()
        
        # 按状态统计
        status_counts = {}
        holes = session.query(Hole).limit(100).all()
        for hole in holes:
            status_counts[hole.status] = status_counts.get(hole.status, 0) + 1
        
        print(f"\n   holes表统计:")
        print(f"   总孔位数: {total_holes}")
        print(f"   状态分布（前100个）: {status_counts}")
        
        # 分析孔位ID分布
        hole_id_samples = [h.hole_id for h in holes[:20]]
        print(f"   孔位ID示例: {hole_id_samples[:5]}")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    finally:
        db_manager.close_session(session)


def analyze_hole_distribution():
    """分析孔位分布情况"""
    print("\n尝试从不同来源分析孔位分布...")
    
    # 1. 从数据库分析
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        from modules.models import Hole
        holes = session.query(Hole).all()
        
        if holes:
            # 分析行列分布（针对(row,column)格式）
            row_distribution = {}
            col_distribution = {}
            
            for hole in holes:
                if hole.hole_id.startswith('(') and hole.hole_id.endswith(')'):
                    try:
                        # 解析(row,column)格式
                        parts = hole.hole_id[1:-1].split(',')
                        if len(parts) == 2:
                            row = int(parts[0])
                            col = int(parts[1])
                            
                            row_distribution[row] = row_distribution.get(row, 0) + 1
                            col_distribution[col] = col_distribution.get(col, 0) + 1
                    except:
                        pass
            
            if row_distribution:
                print(f"\n✅ 发现(row,column)格式的孔位")
                print(f"   行分布（前10行）:")
                for row in sorted(row_distribution.keys())[:10]:
                    count = row_distribution[row]
                    bar = "█" * min(count // 2, 30)  # 简单条形图
                    print(f"     行{row:3d}: {count:3d} {bar}")
                
                if len(row_distribution) > 10:
                    print(f"     ... 还有 {len(row_distribution) - 10} 行")
                
                # 检查是否只有第26行
                if 26 in row_distribution and len(row_distribution) == 1:
                    print("\n❗ 警告：只有第26行的孔位！")
                elif 26 in row_distribution:
                    percentage = row_distribution[26] / sum(row_distribution.values()) * 100
                    print(f"\n   第26行占比: {percentage:.1f}%")
            
            # 分析坐标分布
            x_coords = [h.position_x for h in holes if h.position_x is not None]
            y_coords = [h.position_y for h in holes if h.position_y is not None]
            
            if x_coords and y_coords:
                print(f"\n   坐标分布:")
                print(f"   X范围: [{min(x_coords):.1f}, {max(x_coords):.1f}]")
                print(f"   Y范围: [{min(y_coords):.1f}, {max(y_coords):.1f}]")
                
                # 检查X坐标聚类
                x_clusters = {}
                tolerance = 50  # 50像素容差
                for x in x_coords:
                    cluster_found = False
                    for cluster_x in x_clusters:
                        if abs(x - cluster_x) < tolerance:
                            x_clusters[cluster_x] += 1
                            cluster_found = True
                            break
                    if not cluster_found:
                        x_clusters[x] = 1
                
                print(f"   X坐标聚类数: {len(x_clusters)}")
                if len(x_clusters) <= 5:
                    print("   ⚠️ X坐标聚类较少，可能存在列分组问题")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    finally:
        db_manager.close_session(session)


def test_panorama_update():
    """测试全景图更新机制"""
    print("\n测试全景图更新机制...")
    
    try:
        from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
        from aidcis2.models.hole_data import HoleStatus
        
        # 创建全景图组件
        panorama = CompletePanoramaWidget()
        
        # 测试不同格式的孔位ID更新
        test_updates = [
            ("(26,27)", HoleStatus.QUALIFIED),
            ("(25,27)", HoleStatus.QUALIFIED),  # 不同行
            ("(26,1)", HoleStatus.DEFECTIVE),   # 同行不同列
            ("H001", HoleStatus.QUALIFIED),     # H格式
        ]
        
        print("测试批量更新不同格式的孔位ID...")
        
        # 方法1：直接调用update_hole_status
        for hole_id, status in test_updates:
            print(f"   更新 {hole_id} -> {status.name}")
            panorama.update_hole_status(hole_id, status)
        
        # 触发批量更新
        print("\n   强制立即更新...")
        panorama.force_immediate_update()
        
        # 方法2：使用batch_update_hole_status
        batch_updates = {hid: status for hid, status in test_updates}
        print("\n   测试批量更新接口...")
        panorama.batch_update_hole_status(batch_updates)
        
        print("\n✅ 更新测试完成")
        
        # 调用调试方法
        if hasattr(panorama, 'debug_hole_items_format'):
            print("\n调用全景图调试方法...")
            panorama.debug_hole_items_format()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def check_sync_manager_status():
    """检查同步管理器状态"""
    print("\n检查PanoramaSyncManager配置...")
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 创建模拟的全景图组件
        from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
        panorama = CompletePanoramaWidget()
        
        # 创建同步管理器
        sync_manager = PanoramaSyncManager(db_manager, panorama)
        
        # 获取状态
        stats = sync_manager.get_sync_stats()
        
        print("✅ PanoramaSyncManager可以正常创建")
        print(f"   配置:")
        print(f"   - 同步间隔: {stats['sync_interval']}ms")
        print(f"   - 批量大小: {sync_manager.batch_size}")
        print(f"   - 自动同步: {'启用' if stats['auto_sync_enabled'] else '禁用'}")
        
        # 检查数据库统计
        db_stats = stats.get('db_stats', {})
        if db_stats:
            print(f"\n   数据库状态:")
            print(f"   - 总更新数: {db_stats.get('total_updates', 0)}")
            print(f"   - 待同步数: {db_stats.get('pending_updates', 0)}")
            print(f"   - 同步率: {db_stats.get('sync_rate', 0):.1f}%")
        
        # 测试手动同步
        print("\n   测试手动同步...")
        sync_manager.force_sync()
        print("   ✅ 手动同步完成")
        
    except Exception as e:
        print(f"❌ 同步管理器检查失败: {e}")
        import traceback
        traceback.print_exc()


def suggest_solutions():
    """提供解决方案建议"""
    print("\n" + "=" * 60)
    print("💡 解决方案建议")
    print("=" * 60)
    
    print("""
1. **启用数据库驱动的全景图更新**：
   在main_window.py中添加：
   ```python
   # 初始化同步管理器
   self.panorama_sync_manager = PanoramaSyncManager(self.db_manager, self.sidebar_panorama)
   self.sidebar_panorama.set_panorama_sync_manager(self.panorama_sync_manager)
   
   # 启动自动同步
   self.panorama_sync_manager.start_sync(1000)  # 1秒间隔
   self.sidebar_panorama.enable_db_sync(True)
   ```

2. **检查扇形划分逻辑**：
   确保所有扇形的孔位都被包含在holes_list_v2中

3. **增加列分组容差**：
   已经修改为50像素，可能需要进一步调整

4. **添加更多调试日志**：
   在_optimize_global_detection_path和_create_spiral_detection_path中
   添加日志，查看孔位是如何被筛选和排序的

5. **验证DXF解析**：
   检查DXF解析器是否正确识别了所有孔位
   """)


if __name__ == "__main__":
    analyze_panorama_update_issue()
    suggest_solutions()