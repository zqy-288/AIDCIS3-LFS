#!/usr/bin/env python3
"""
演示批次处理系统
展示批次的创建、模拟测试和数据保存
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.domain.services.batch_service import BatchService
from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
from src.models.data_path_manager import DataPathManager
from src.models.batch_data_manager import BatchDataManager
from src.core_business.models.hole_data import HoleData


def print_section(title):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)


def demonstrate_batch_creation():
    """演示批次创建"""
    print_section("1. 批次创建演示")
    
    # 创建服务
    repository = BatchRepositoryImpl()
    batch_service = BatchService(repository)
    path_manager = DataPathManager()
    
    # 创建实际检测批次
    print("\n创建实际检测批次...")
    real_batch = batch_service.create_batch(
        product_id=1,
        product_name="CAP1000",
        operator="张三",
        equipment_id="DEVICE-001",
        description="演示实际检测批次",
        is_mock=False
    )
    
    print(f"✓ 实际批次创建成功")
    print(f"  批次ID: {real_batch.batch_id}")
    print(f"  类型: {real_batch.detection_type.value}")
    print(f"  状态: {real_batch.status.value}")
    print(f"  数据路径: {real_batch.data_path}")
    
    # 创建模拟测试批次
    print("\n创建模拟测试批次...")
    mock_batch = batch_service.create_batch(
        product_id=1,
        product_name="CAP1000",
        operator="系统测试",
        equipment_id="SIMULATOR",
        description="演示模拟测试批次",
        is_mock=True
    )
    
    print(f"✓ 模拟批次创建成功")
    print(f"  批次ID: {mock_batch.batch_id}")
    print(f"  类型: {mock_batch.detection_type.value}")
    print(f"  后缀: {'_MOCK' if mock_batch.is_mock else ''}")
    
    return real_batch, mock_batch, batch_service, path_manager


def demonstrate_directory_structure(batch, path_manager):
    """演示目录结构"""
    print_section("2. 目录结构展示")
    
    product_name = batch.batch_id.split('_')[0]
    
    # 获取各种路径
    paths = {
        "批次根目录": path_manager.get_inspection_batch_path(product_name, batch.batch_id),
        "批次信息文件": path_manager.get_batch_info_path(product_name, batch.batch_id),
        "批次汇总文件": path_manager.get_batch_summary_path(product_name, batch.batch_id),
        "数据批次目录": path_manager.get_data_batches_dir(product_name, batch.batch_id),
        "孔位结果目录": path_manager.get_hole_results_dir(product_name, batch.batch_id),
    }
    
    print("\n生成的路径结构:")
    for name, path in paths.items():
        exists = Path(path).exists()
        print(f"  {name}: {path}")
        print(f"    存在: {'✓' if exists else '✗'}")
    
    # 检查batch_info.json内容
    batch_info_path = Path(paths["批次信息文件"])
    if batch_info_path.exists():
        print("\n批次信息文件内容:")
        with open(batch_info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
            print(json.dumps(info, indent=2, ensure_ascii=False))


def demonstrate_simulation(batch, batch_service):
    """演示模拟测试"""
    print_section("3. 模拟测试演示")
    
    if not batch.is_mock:
        print("跳过 - 这不是模拟批次")
        return
    
    # 开始批次
    print("\n开始模拟批次...")
    batch_service.start_batch(batch.batch_id)
    print(f"✓ 批次状态: {batch.status.value}")
    
    # 模拟检测10个孔位
    holes = []
    for i in range(10):
        row = chr(65 + i // 3)  # A, B, C...
        col = (i % 3) + 1
        hole_id = f"{row}C{col:03d}R001"
        holes.append(HoleData(
            hole_id=hole_id,
            center_x=100 + i * 50,
            center_y=200 + (i % 3) * 50,
            radius=8.8
        ))
    
    print(f"\n模拟检测 {len(holes)} 个孔位...")
    
    # 更新进度
    batch_service.update_progress(
        batch_id=batch.batch_id,
        total_holes=len(holes),
        current_index=0
    )
    
    # 模拟检测结果
    qualified_count = 0
    defective_count = 0
    
    for i, hole in enumerate(holes):
        # 模拟检测延迟
        time.sleep(0.1)
        
        # 生成随机结果（95%合格，5%缺陷）
        import random
        is_qualified = random.random() < 0.95
        
        result = {
            'hole_id': hole.hole_id,
            'status': 'qualified' if is_qualified else 'defective',
            'timestamp': datetime.now().isoformat(),
            'measurements': {
                'diameter': 17.6 + random.uniform(-0.1, 0.1),
                'ovality': random.uniform(0, 0.5)
            }
        }
        
        if is_qualified:
            qualified_count += 1
        else:
            defective_count += 1
        
        # 添加检测结果
        batch_service.add_detection_result(batch.batch_id, hole.hole_id, result)
        
        # 更新进度
        batch_service.update_progress(
            batch_id=batch.batch_id,
            current_index=i + 1,
            completed_holes=i + 1,
            qualified_holes=qualified_count,
            defective_holes=defective_count
        )
        
        print(f"  [{i+1:2d}/{len(holes)}] {hole.hole_id}: {'✓' if is_qualified else '✗'} {result['status']}")
    
    print(f"\n检测完成统计:")
    print(f"  总数: {len(holes)}")
    print(f"  合格: {qualified_count} ({qualified_count/len(holes)*100:.1f}%)")
    print(f"  缺陷: {defective_count} ({defective_count/len(holes)*100:.1f}%)")
    
    return holes


def demonstrate_pause_resume(batch, batch_service):
    """演示暂停和恢复"""
    print_section("4. 暂停/恢复演示")
    
    # 暂停批次
    print("\n暂停批次...")
    detection_state = {
        'current_index': 5,
        'detection_results': {'AC001R001': 'qualified', 'AC002R001': 'defective'},
        'pending_holes': ['AC003R001', 'AC004R001', 'AC005R001'],
        'simulation_params': {'speed': 10, 'success_rate': 0.95}
    }
    
    success = batch_service.pause_batch(batch.batch_id, detection_state)
    print(f"✓ 暂停成功: {success}")
    print(f"  保存的状态: 当前索引={detection_state['current_index']}, 待检={len(detection_state['pending_holes'])}个")
    
    # 检查状态文件
    product_name = batch.batch_id.split('_')[0]
    state_file = Path(batch.data_path) / "detection_state.json"
    if state_file.exists():
        print(f"✓ 状态文件已创建: {state_file}")
    
    # 恢复批次
    print("\n恢复批次...")
    resumed_state = batch_service.resume_batch(batch.batch_id)
    if resumed_state:
        print(f"✓ 恢复成功")
        print(f"  恢复的索引: {resumed_state.get('current_index', 0)}")
        print(f"  待检孔位: {len(resumed_state.get('pending_holes', []))}个")


def demonstrate_batch_data_manager(batch, holes):
    """演示批量数据管理"""
    print_section("5. 批量数据管理演示")
    
    product_name = batch.batch_id.split('_')[0]
    
    # 创建批量数据管理器
    data_manager = BatchDataManager(
        product_id=product_name,
        inspection_batch_id=batch.batch_id
    )
    
    print(f"\n数据批次目录: {data_manager.data_dir}")
    
    # 保存批量数据
    print("\n保存批量数据（每10个一批）...")
    for i in range(0, len(holes), 10):
        batch_holes = holes[i:i+10]
        batch_data = {
            'batch_index': i // 10,
            'holes': [
                {
                    'hole_id': hole.hole_id,
                    'center_x': hole.center_x,
                    'center_y': hole.center_y,
                    'radius': hole.radius
                }
                for hole in batch_holes
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # 使用正确的方法创建和保存批次
        from src.models.batch_data_manager import DataBatch
        data_batch = DataBatch(
            batch_id=f"{batch.batch_id}_batch_{i//10:04d}",
            batch_index=i // 10,
            timestamp=datetime.now(),
            data=batch_data
        )
        filepath = data_manager.save_batch(data_batch)
        print(f"  ✓ 保存批次 {i//10}: {data_batch.batch_id}.json ({len(batch_holes)}个孔位)")
    
    # 列出所有批次文件
    print("\n已保存的批次文件:")
    batch_files = data_manager.list_batch_files()
    for file in batch_files[:5]:  # 只显示前5个
        print(f"  - {file}")
    if len(batch_files) > 5:
        print(f"  ... 还有 {len(batch_files) - 5} 个文件")


def demonstrate_completion(batch, batch_service):
    """演示批次完成"""
    print_section("6. 批次完成演示")
    
    print("\n完成批次...")
    success = batch_service.complete_batch(batch.batch_id)
    print(f"✓ 批次完成: {success}")
    print(f"  最终状态: {batch.status.value}")
    
    # 检查汇总文件
    product_name = batch.batch_id.split('_')[0]
    summary_file = Path(batch.data_path) / "batch_summary.json"
    if summary_file.exists():
        print(f"\n✓ 汇总文件已生成: {summary_file}")
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
            print("\n批次汇总:")
            print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    """主函数"""
    print("批次处理系统演示")
    print("展示批次创建、模拟测试、数据保存的完整流程")
    
    try:
        # 1. 创建批次
        real_batch, mock_batch, batch_service, path_manager = demonstrate_batch_creation()
        
        # 2. 展示目录结构
        demonstrate_directory_structure(mock_batch, path_manager)
        
        # 3. 演示模拟测试
        holes = demonstrate_simulation(mock_batch, batch_service)
        
        # 4. 演示暂停/恢复
        demonstrate_pause_resume(mock_batch, batch_service)
        
        # 5. 演示批量数据管理
        if holes:
            demonstrate_batch_data_manager(mock_batch, holes)
        
        # 6. 演示批次完成
        demonstrate_completion(mock_batch, batch_service)
        
        print_section("演示完成")
        print("\n请查看以下目录了解生成的文件:")
        print(f"  {mock_batch.data_path}")
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()