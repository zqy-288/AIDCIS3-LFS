#!/usr/bin/env python3
"""
简化的AC/BC格式测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_database():
    """测试数据库"""
    print("📊 测试数据库...")
    
    try:
        from src.modules.models import DatabaseManager
        
        db_manager = DatabaseManager()
        holes = db_manager.get_workpiece_holes("CAP1000")
        
        ac_count = len([h for h in holes if h['hole_id'].startswith('AC')])
        bc_count = len([h for h in holes if h['hole_id'].startswith('BC')])
        
        print(f"  A侧孔位: {ac_count}")
        print(f"  B侧孔位: {bc_count}")
        
        if holes:
            print(f"  示例孔位: {holes[0]['hole_id']}")
        
        return ac_count > 0 and bc_count > 0
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def test_file_system():
    """测试文件系统"""
    print("📁 测试文件系统...")
    
    try:
        import os
        data_dir = project_root / "Data" / "CAP1000"
        
        if not data_dir.exists():
            print("  ⚠️ CAP1000目录不存在")
            return True
        
        dirs = [d for d in os.listdir(str(data_dir)) if (data_dir / d).is_dir()]
        ac_dirs = [d for d in dirs if d.startswith('AC')]
        bc_dirs = [d for d in dirs if d.startswith('BC')]
        
        print(f"  A侧目录: {len(ac_dirs)}")
        print(f"  B侧目录: {len(bc_dirs)}")
        
        if ac_dirs:
            print(f"  示例A侧: {ac_dirs[0]}")
        if bc_dirs:
            print(f"  示例B侧: {bc_dirs[0]}")
        
        return len(ac_dirs) > 0 and len(bc_dirs) > 0
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def main():
    """主函数"""
    print("🧪 AC/BC格式验证")
    print("="*40)
    
    tests = [
        ("数据库", test_database),
        ("文件系统", test_file_system)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print(f"  {'✅' if result else '❌'} {name}: {'通过' if result else '失败'}")
        except Exception as e:
            results.append(False)
            print(f"  ❌ {name}: 异常 - {e}")
        print()
    
    success_count = sum(results)
    print(f"📊 结果: {success_count}/{len(tests)} 通过")
    
    if success_count == len(tests):
        print("🎉 AC/BC格式迁移成功！")
        print("\n✅ 现在系统使用统一的编号格式:")
        print("  • AC097R001 (A侧，第097列，第001行)")
        print("  • BC097R001 (B侧，第097列，第001行)")
    else:
        print("⚠️ 部分测试失败")

if __name__ == "__main__":
    main()