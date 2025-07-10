#!/usr/bin/env python3
"""
数据库系统与项目要求集成演示
展示如何将SQLAlchemy数据库与文件系统数据管理结合
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

from modules.models import hybrid_manager, db_manager


def demo_database_integration():
    """演示数据库系统与项目要求的集成"""
    
    print("=" * 80)
    print("数据库系统与项目要求集成演示")
    print("=" * 80)
    
    # 1. 展示当前数据库结构
    print("\n1. 当前数据库系统概览")
    print("-" * 40)
    print("✅ 数据库类型: SQLite")
    print("✅ 数据库文件: detection_system.db")
    print("✅ ORM框架: SQLAlchemy")
    print("✅ 主要数据表:")
    print("   - workpieces (工件表)")
    print("   - holes (孔表)")
    print("   - measurements (测量数据表)")
    print("   - endoscope_images (内窥镜图像表)")
    print("   - annotations (标注数据表)")
    
    # 2. 演示项目创建流程
    print("\n2. 项目创建流程演示")
    print("-" * 40)
    
    dxf_file_path = "东重管板.dxf"
    workpiece_name = "东重管板检测项目"
    
    print(f"📁 DXF文件: {dxf_file_path}")
    print(f"🏭 工件名称: {workpiece_name}")
    
    # 创建项目
    project_id, project_path = hybrid_manager.create_project_from_dxf(
        dxf_file_path, workpiece_name
    )
    
    if project_id:
        print(f"✅ 项目创建成功:")
        print(f"   - 项目ID: {project_id}")
        print(f"   - 项目路径: {project_path}")
        print(f"   - 数据库记录: 已创建")
    else:
        print("❌ 项目创建失败")
        return
    
    # 3. 演示孔位数据结构创建
    print("\n3. 孔位数据结构创建")
    print("-" * 40)
    
    demo_holes = ["H00001", "H00002"]
    
    for hole_id in demo_holes:
        success = hybrid_manager.create_hole_data_structure(project_id, hole_id)
        if success:
            print(f"✅ {hole_id} 数据结构创建成功")
            print(f"   - {project_path}/holes/{hole_id}/BISDM/")
            print(f"   - {project_path}/holes/{hole_id}/CCIDM/")
        else:
            print(f"❌ {hole_id} 数据结构创建失败")
    
    # 4. 演示测量数据复制
    print("\n4. 测量数据复制演示")
    print("-" * 40)
    
    csv_files = [
        ("cache/measurement_data_Fri_Jul__4_18_40_29_2025.csv", "H00001"),
        ("cache/measurement_data_Sat_Jul__5_15_18_46_2025.csv", "H00002")
    ]
    
    for csv_file, hole_id in csv_files:
        if os.path.exists(csv_file):
            success = hybrid_manager.copy_measurement_data(project_id, hole_id, csv_file)
            if success:
                print(f"✅ {hole_id} 测量数据复制成功")
                print(f"   - 源文件: {csv_file}")
                print(f"   - 目标: {project_path}/holes/{hole_id}/CCIDM/")
            else:
                print(f"❌ {hole_id} 测量数据复制失败")
        else:
            print(f"⚠️  源文件不存在: {csv_file}")
    
    # 5. 演示数据检索
    print("\n5. 数据检索演示")
    print("-" * 40)
    
    for hole_id in demo_holes:
        csv_path = hybrid_manager.get_hole_measurement_file(project_id, hole_id)
        if csv_path:
            print(f"✅ {hole_id} 测量文件: {csv_path}")
        else:
            print(f"❌ {hole_id} 未找到测量文件")
    
    # 6. 展示与现有功能的集成点
    print("\n6. 与项目要求的集成点")
    print("-" * 40)
    
    print("🎯 优先级1 - DXF预览区域鼠标交互优化:")
    print("   - 数据库关联: 孔位选择时查询holes表获取详细信息")
    print("   - 集成点: graphics_view.py中的孔位点击事件")
    
    print("\n🔍 优先级2 - 孔位搜索功能调试和修复:")
    print("   - 数据库关联: 搜索结果可选择性与holes表同步")
    print("   - 集成点: update_hole_completer()方法")
    print("   - 建议: 支持数据库和内存双重数据源")
    
    print("\n📊 优先级3 - 数据管理系统与实时监控集成:")
    print("   - 数据库关联: 完整的项目-孔位-测量数据链路")
    print("   - 文件系统: 按项目组织的CSV数据文件")
    print("   - 集成点: 实时监控界面的数据加载")
    
    # 7. 建议的集成架构
    print("\n7. 建议的集成架构")
    print("-" * 40)
    
    print("📋 数据存储双轨制:")
    print("   - SQLAlchemy数据库: 结构化数据、关系查询、元数据管理")
    print("   - 文件系统: 大量测量数据、CSV文件、图像文件")
    
    print("\n🔄 数据同步机制:")
    print("   - DXF加载 → 创建项目 → 数据库记录 + 文件目录")
    print("   - 测量数据 → 同时保存到数据库 + CSV文件")
    print("   - 实时监控 → 从文件系统读取 + 数据库元数据")
    
    print("\n🎛️ 用户界面集成:")
    print("   - 主检测视图: 显示项目概览（数据库查询）")
    print("   - 孔位搜索: 基于数据库holes表的智能搜索")
    print("   - 实时监控: 加载对应孔位的CSV数据文件")
    
    print("\n" + "=" * 80)
    print("集成演示完成！")
    print("数据库系统已成功扩展以支持项目要求的数据管理架构")
    print("=" * 80)


def show_current_database_status():
    """显示当前数据库状态"""
    print("\n📊 当前数据库状态:")
    print("-" * 30)
    
    session = db_manager.get_session()
    try:
        from modules.models import Workpiece, Hole, Measurement
        
        workpiece_count = session.query(Workpiece).count()
        hole_count = session.query(Hole).count()
        measurement_count = session.query(Measurement).count()
        
        print(f"工件数量: {workpiece_count}")
        print(f"孔位数量: {hole_count}")
        print(f"测量记录: {measurement_count}")
        
        # 显示最近的工件
        recent_workpieces = session.query(Workpiece).order_by(Workpiece.created_at.desc()).limit(3).all()
        if recent_workpieces:
            print("\n最近的工件:")
            for wp in recent_workpieces:
                print(f"  - {wp.workpiece_id}: {wp.name}")
        
    except Exception as e:
        print(f"查询数据库状态失败: {e}")
    finally:
        db_manager.close_session(session)


if __name__ == "__main__":
    # 显示当前数据库状态
    show_current_database_status()
    
    # 运行集成演示
    demo_database_integration()
