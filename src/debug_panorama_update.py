"""
全景图更新问题调试工具
用于诊断为什么只有部分孔位被更新
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.models import DatabaseManager
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget


def analyze_hole_distribution(hole_collection):
    """分析孔位分布"""
    if not hole_collection or not hole_collection.holes:
        print("❌ 没有孔位数据")
        return
    
    print("\n🔍 孔位分布分析:")
    print(f"总孔位数: {len(hole_collection.holes)}")
    
    # 按行列统计
    row_stats = {}
    col_stats = {}
    
    for hole_id, hole in hole_collection.holes.items():
        # 解析(row,column)格式的ID
        if hole_id.startswith('(') and hole_id.endswith(')'):
            try:
                parts = hole_id[1:-1].split(',')
                row = int(parts[0])
                col = int(parts[1])
                
                row_stats[row] = row_stats.get(row, 0) + 1
                col_stats[col] = col_stats.get(col, 0) + 1
            except:
                pass
    
    # 打印行分布
    print(f"\n行分布 (共{len(row_stats)}行):")
    for row in sorted(row_stats.keys())[:10]:  # 只显示前10行
        print(f"  行{row}: {row_stats[row]}个孔位")
    if len(row_stats) > 10:
        print(f"  ... 还有{len(row_stats)-10}行")
    
    # 打印列分布
    print(f"\n列分布 (共{len(col_stats)}列):")
    for col in sorted(col_stats.keys())[:10]:  # 只显示前10列
        print(f"  列{col}: {col_stats[col]}个孔位")
    if len(col_stats) > 10:
        print(f"  ... 还有{len(col_stats)-10}列")
    
    # 检查坐标分布
    print("\n坐标分布:")
    x_coords = []
    y_coords = []
    
    for hole in hole_collection.holes.values():
        x_coords.append(hole.center_x)
        y_coords.append(hole.center_y)
    
    if x_coords and y_coords:
        print(f"  X范围: [{min(x_coords):.1f}, {max(x_coords):.1f}]")
        print(f"  Y范围: [{min(y_coords):.1f}, {max(y_coords):.1f}]")
        print(f"  X跨度: {max(x_coords) - min(x_coords):.1f}")
        print(f"  Y跨度: {max(y_coords) - min(y_coords):.1f}")


def analyze_detection_path(holes_list):
    """分析检测路径"""
    if not holes_list:
        print("❌ 没有检测路径数据")
        return
    
    print(f"\n🛤️ 检测路径分析:")
    print(f"路径总长度: {len(holes_list)}个孔位")
    
    # 分析前20个孔位
    print("\n前20个检测孔位:")
    for i, hole in enumerate(holes_list[:20]):
        print(f"  {i+1}. {hole.hole_id} at ({hole.center_x:.1f}, {hole.center_y:.1f})")
    
    # 按列统计
    column_count = {}
    for hole in holes_list:
        if hole.hole_id.startswith('('):
            try:
                row = int(hole.hole_id.split(',')[0][1:])
                column_count[row] = column_count.get(row, 0) + 1
            except:
                pass
    
    print(f"\n检测路径中各列的孔位数:")
    for col in sorted(column_count.keys())[:10]:
        print(f"  列{col}: {column_count[col]}个孔位")


def analyze_panorama_holes(panorama_widget):
    """分析全景图中的孔位"""
    if not panorama_widget or not hasattr(panorama_widget, 'panorama_view'):
        print("❌ 全景图组件不可用")
        return
    
    if not hasattr(panorama_widget.panorama_view, 'hole_items'):
        print("❌ 全景图没有hole_items")
        return
    
    hole_items = panorama_widget.panorama_view.hole_items
    print(f"\n🎨 全景图孔位分析:")
    print(f"总孔位数: {len(hole_items)}")
    
    # 显示一些示例ID
    sample_ids = list(hole_items.keys())[:20]
    print("\n前20个孔位ID:")
    for i, hole_id in enumerate(sample_ids):
        print(f"  {i+1}. {hole_id}")
    
    # 统计更新状态
    from aidcis2.models.hole_data import HoleStatus
    status_count = {
        HoleStatus.PENDING: 0,
        HoleStatus.QUALIFIED: 0,
        HoleStatus.DEFECTIVE: 0,
        HoleStatus.PROCESSING: 0,
        HoleStatus.BLIND: 0,
        HoleStatus.TIE_ROD: 0
    }
    
    for hole_id, hole_item in hole_items.items():
        if hasattr(hole_item, 'hole_data') and hasattr(hole_item.hole_data, 'status'):
            status = hole_item.hole_data.status
            if status in status_count:
                status_count[status] += 1
    
    print("\n状态分布:")
    for status, count in status_count.items():
        if count > 0:
            print(f"  {status.name}: {count}个孔位")


def check_database_updates():
    """检查数据库中的状态更新记录"""
    db_manager = DatabaseManager()
    
    print("\n💾 数据库状态更新分析:")
    
    # 获取最近的状态更新
    session = db_manager.get_session()
    try:
        from modules.models import HoleStatusUpdate
        recent_updates = session.query(HoleStatusUpdate).order_by(
            HoleStatusUpdate.update_timestamp.desc()
        ).limit(20).all()
        
        print(f"最近20条状态更新:")
        for update in recent_updates:
            hole = update.hole
            print(f"  {hole.hole_id}: {update.old_status} -> {update.new_status} "
                  f"({update.update_timestamp}, 同步: {update.sync_to_panorama})")
        
        # 统计未同步的更新
        pending_count = session.query(HoleStatusUpdate).filter_by(
            sync_to_panorama=False
        ).count()
        
        total_count = session.query(HoleStatusUpdate).count()
        
        print(f"\n同步统计:")
        print(f"  总更新数: {total_count}")
        print(f"  待同步数: {pending_count}")
        print(f"  已同步数: {total_count - pending_count}")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
    finally:
        db_manager.close_session(session)


def main():
    """主调试函数"""
    print("🔍 全景图更新问题调试工具")
    print("=" * 50)
    
    # 这里需要从主窗口获取实际的数据
    # 在实际使用时，需要传入真实的对象
    print("\n💡 使用方法:")
    print("1. 在main_window.py中添加调试代码:")
    print("   from debug_panorama_update import analyze_hole_distribution, analyze_detection_path")
    print("   analyze_hole_distribution(self.hole_collection)")
    print("   analyze_detection_path(self.holes_list_v2)")
    print("\n2. 或者在适当位置调用:")
    print("   self.sidebar_panorama.debug_hole_items_format()")
    
    # 检查数据库更新
    check_database_updates()


if __name__ == '__main__':
    main()