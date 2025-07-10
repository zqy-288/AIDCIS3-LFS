#!/usr/bin/env python3
"""
最终CSV路径修复验证测试
"""

import os
import sys

def test_csv_path_fixes():
    """测试CSV路径修复"""
    print("🔧 CSV路径修复验证测试")
    print("=" * 60)
    
    # 1. 检查实际文件结构
    print("📁 检查实际文件结构:")
    
    expected_paths = [
        "Data/H00001/CCIDM",
        "Data/H00002/CCIDM",
        "Data/H00001/BISDM/result",
        "Data/H00002/BISDM/result"
    ]
    
    all_exist = True
    for path in expected_paths:
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {path}")
        
        if exists and "CCIDM" in path:
            try:
                files = os.listdir(path)
                csv_files = [f for f in files if f.endswith('.csv')]
                print(f"    📄 CSV文件: {len(csv_files)} 个")
                if csv_files:
                    print(f"    📋 示例: {csv_files[0]}")
            except Exception as e:
                print(f"    ⚠️ 读取失败: {e}")
        
        if not exists:
            all_exist = False
    
    print()
    
    # 2. 测试路径映射修复
    print("🔄 测试路径映射修复:")
    
    # 模拟realtime_chart.py中的路径映射
    hole_to_csv_map = {
        "H00001": "Data/H00001/CCIDM",
        "H00002": "Data/H00002/CCIDM"
    }
    
    hole_to_image_map = {
        "H00001": "Data/H00001/BISDM/result",
        "H00002": "Data/H00002/BISDM/result"
    }
    
    mapping_correct = True
    for hole_id, csv_path in hole_to_csv_map.items():
        image_path = hole_to_image_map[hole_id]
        
        csv_exists = os.path.exists(csv_path)
        image_exists = os.path.exists(image_path)
        
        print(f"  {hole_id}:")
        print(f"    📄 CSV路径: {csv_path} {'✅' if csv_exists else '❌'}")
        print(f"    🖼️ 图像路径: {image_path} {'✅' if image_exists else '❌'}")
        
        if not csv_exists or not image_exists:
            mapping_correct = False
    
    print()
    
    # 3. 测试历史查看器路径查找
    print("📊 测试历史查看器路径查找:")
    
    def test_hole_csv_discovery(hole_id):
        """测试孔位CSV发现功能"""
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]
        
        csv_files = []
        found_path = None
        
        for path in csv_paths:
            if os.path.exists(path):
                found_path = path
                for csv_file in os.listdir(path):
                    if csv_file.endswith('.csv'):
                        csv_files.append(os.path.join(path, csv_file))
                if csv_files:
                    break
        
        return found_path, csv_files
    
    discovery_works = True
    for hole_id in ["H00001", "H00002"]:
        found_path, csv_files = test_hole_csv_discovery(hole_id)
        
        if found_path and csv_files:
            print(f"  ✅ {hole_id}: 找到 {len(csv_files)} 个CSV文件")
            print(f"    📁 路径: {found_path}")
            print(f"    📄 文件: {os.path.basename(csv_files[0])}")
        else:
            print(f"  ❌ {hole_id}: 未找到CSV文件")
            discovery_works = False
    
    print()
    
    # 4. 总结
    print("📋 修复验证总结:")
    print(f"  📁 文件结构: {'✅ 正确' if all_exist else '❌ 有问题'}")
    print(f"  🔄 路径映射: {'✅ 正确' if mapping_correct else '❌ 有问题'}")
    print(f"  🔍 路径发现: {'✅ 正常' if discovery_works else '❌ 有问题'}")
    
    overall_success = all_exist and mapping_correct and discovery_works
    
    print()
    if overall_success:
        print("🎉 所有CSV路径修复验证通过!")
        print("💡 现在历史查看器应该能正常找到H00001的CSV数据文件了")
    else:
        print("⚠️ 仍有问题需要解决:")
        if not all_exist:
            print("  - 检查文件结构是否完整")
        if not mapping_correct:
            print("  - 检查路径映射配置")
        if not discovery_works:
            print("  - 检查路径发现逻辑")
    
    return overall_success

if __name__ == "__main__":
    success = test_csv_path_fixes()
    sys.exit(0 if success else 1)
