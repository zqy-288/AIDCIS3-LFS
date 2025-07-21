#!/usr/bin/env python3
"""
快速归档测试
验证ArchiveManager能否正确检测H00001孔位
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def quick_test():
    """快速测试"""
    print("🔍 快速归档测试")
    print("=" * 30)
    
    try:
        from modules.image_scanner import ImageScanner
        from modules.archive_manager import ArchiveManager
        
        # 创建ImageScanner
        scanner = ImageScanner("Data")
        success = scanner.scan_directories()
        
        print(f"扫描结果: {success}")
        
        hole_ids = scanner.get_hole_ids()
        print(f"ImageScanner孔位: {hole_ids}")
        
        # 创建ArchiveManager（使用共享的ImageScanner）
        archive_mgr = ArchiveManager("Data", "Archive", scanner)
        archive_hole_ids = archive_mgr.image_scanner.get_hole_ids()
        
        print(f"ArchiveManager孔位: {archive_hole_ids}")
        
        # 检查H00001
        h00001_in_scanner = "H00001" in hole_ids
        h00001_in_archive = "H00001" in archive_hole_ids
        
        print(f"H00001在ImageScanner: {h00001_in_scanner}")
        print(f"H00001在ArchiveManager: {h00001_in_archive}")
        
        if h00001_in_scanner and h00001_in_archive:
            print("✅ H00001检测正常，归档应该可以工作")
            return True
        else:
            print("❌ H00001检测失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 修复成功！现在可以正常归档了")
    else:
        print("\n⚠️ 仍有问题需要解决")
    sys.exit(0 if success else 1)
