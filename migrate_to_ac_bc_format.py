#!/usr/bin/env python3
"""
统一迁移脚本：将所有孔位编号格式统一为AC/BC标准格式
清理所有其他编号格式，只保留AC097R001和BC097R001格式
"""

import sys
import os
import shutil
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def migrate_database():
    """迁移数据库到AC/BC格式"""
    print("🔄 开始迁移数据库...")
    
    try:
        from src.modules.models import DatabaseManager
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 更新数据库到AC/BC格式
        db_manager.update_hole_naming_format()
        
        print("✅ 数据库迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_file_system():
    """迁移文件系统目录结构到AC/BC格式"""
    print("🔄 开始迁移文件系统...")
    
    data_dir = project_root / "Data" / "CAP1000"
    if not data_dir.exists():
        print("⚠️ CAP1000数据目录不存在")
        return True
    
    try:
        # 扫描现有目录
        old_dirs = []
        for item in os.listdir(str(data_dir)):
            item_path = data_dir / item
            if item_path.is_dir():
                # 检查是否为旧格式目录
                if item.startswith('R') and 'C' in item:
                    old_dirs.append(item)
        
        if not old_dirs:
            print("✅ 没有需要迁移的文件系统目录")
            return True
        
        print(f"📁 发现 {len(old_dirs)} 个旧格式目录需要迁移")
        
        # 转换每个目录
        import re
        for old_dir in old_dirs:
            # 解析R###C###格式
            match = re.match(r'R(\d+)C(\d+)', old_dir)
            if match:
                row_num = match.group(1)
                col_num = match.group(2)
                
                # 转换为AC/BC格式
                # 假设偶数列为A侧，奇数列为B侧
                side = 'A' if int(col_num) % 2 == 0 else 'B'
                new_dir = f"{side}C{col_num}R{row_num}"
                
                old_path = data_dir / old_dir
                new_path = data_dir / new_dir
                
                # 重命名目录
                if not new_path.exists():
                    shutil.move(str(old_path), str(new_path))
                    print(f"  ✅ {old_dir} -> {new_dir}")
                else:
                    print(f"  ⚠️ 目标目录已存在: {new_dir}")
        
        print("✅ 文件系统迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 文件系统迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_test_files():
    """更新测试文件和脚本中的编号格式"""
    print("🔄 开始更新测试文件...")
    
    try:
        # 查找并更新测试文件中的孔位编号
        test_files = [
            "business_controller_test.py",
            "update_main_window_integration.py",
            "run_playwright_tests.py"
        ]
        
        for test_file in test_files:
            file_path = project_root / test_file
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                # 替换旧格式编号
                # H### -> AC/BC格式
                import re
                
                # H001 -> AC097R001
                content = re.sub(r'H(\d{3})', r'AC\1R001', content)
                
                # H####格式 -> AC/BC格式  
                content = re.sub(r'H(\d{2})(\d{2})', r'AC\1R\2', content)
                
                # C###R### -> AC###R###或BC###R###
                def replace_c_format(match):
                    col = int(match.group(1))
                    row = match.group(2)
                    side = 'A' if col % 2 == 1 else 'B'  # 奇数列A侧，偶数列B侧
                    return f"{side}C{col:03d}R{row}"
                
                content = re.sub(r'C(\d{3})R(\d{3})', replace_c_format, content)
                
                file_path.write_text(content, encoding='utf-8')
                print(f"  ✅ 更新: {test_file}")
        
        print("✅ 测试文件更新完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试文件更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def clean_legacy_references():
    """清理代码中的遗留格式引用"""
    print("🔄 开始清理遗留引用...")
    
    try:
        # 检查关键文件中是否还有旧格式引用
        key_files = [
            "src/controllers/main_window_controller.py",
            "src/services/business_service.py",
            "src/core/shared_data_manager.py"
        ]
        
        issues_found = []
        
        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                
                # 检查是否有旧格式引用
                import re
                old_patterns = [
                    r'\bH\d{3}\b',  # H001格式
                    r'\bC\d{3}R\d{3}\b(?!.*[AB]C)',  # C001R001格式（不包含AC/BC）
                    r'\bR\d{3}C\d{3}\b',  # R001C001格式
                ]
                
                for pattern in old_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues_found.append((file_path, pattern, matches))
        
        if issues_found:
            print("⚠️ 发现遗留格式引用:")
            for file_path, pattern, matches in issues_found:
                print(f"  📄 {file_path}: {matches}")
        else:
            print("✅ 没有发现遗留格式引用")
        
        return len(issues_found) == 0
        
    except Exception as e:
        print(f"❌ 清理遗留引用失败: {e}")
        return False

def verify_migration():
    """验证迁移结果"""
    print("🔍 验证迁移结果...")
    
    try:
        # 测试数据库
        from src.modules.models import DatabaseManager
        db_manager = DatabaseManager()
        
        # 获取所有孔位
        holes = db_manager.get_workpiece_holes("CAP1000")
        
        if not holes:
            print("⚠️ 数据库中没有孔位数据")
            return False
        
        # 检查编号格式
        ac_count = 0
        bc_count = 0
        other_count = 0
        
        for hole in holes:
            hole_id = hole['hole_id']
            if hole_id.startswith('AC') and 'R' in hole_id:
                ac_count += 1
            elif hole_id.startswith('BC') and 'R' in hole_id:
                bc_count += 1
            else:
                other_count += 1
                print(f"  ⚠️ 非标准格式: {hole_id}")
        
        print(f"📊 数据库验证结果:")
        print(f"  A侧孔位 (AC###R###): {ac_count}")
        print(f"  B侧孔位 (BC###R###): {bc_count}")
        print(f"  其他格式: {other_count}")
        
        # 测试文件系统
        data_dir = project_root / "Data" / "CAP1000"
        if data_dir.exists():
            dirs = [d for d in os.listdir(str(data_dir)) if (data_dir / d).is_dir()]
            ac_dirs = [d for d in dirs if d.startswith('AC')]
            bc_dirs = [d for d in dirs if d.startswith('BC')]
            other_dirs = [d for d in dirs if not (d.startswith('AC') or d.startswith('BC'))]
            
            print(f"📁 文件系统验证结果:")
            print(f"  A侧目录 (AC###R###): {len(ac_dirs)}")
            print(f"  B侧目录 (BC###R###): {len(bc_dirs)}")
            print(f"  其他目录: {len(other_dirs)}")
            
            if other_dirs:
                print(f"    其他目录列表: {other_dirs}")
        
        success = other_count == 0
        if success:
            print("✅ 迁移验证通过")
        else:
            print("❌ 迁移验证失败")
        
        return success
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("🚀 统一孔位编号格式迁移")
    print("目标格式: AC097R001 (A侧) 和 BC097R001 (B侧)")
    print("="*60)
    
    steps = [
        ("数据库迁移", migrate_database),
        ("文件系统迁移", migrate_file_system),
        ("测试文件更新", update_test_files),
        ("清理遗留引用", clean_legacy_references),
        ("验证迁移结果", verify_migration)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n📋 执行: {step_name}")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} 完成")
            else:
                print(f"❌ {step_name} 失败")
        except Exception as e:
            print(f"❌ {step_name} 异常: {e}")
    
    print("\n" + "="*60)
    print(f"📊 迁移结果: {success_count}/{len(steps)} 步骤成功")
    print("="*60)
    
    if success_count == len(steps):
        print("\n🎉 所有步骤完成！")
        print("现在所有孔位都使用AC097R001和BC097R001标准格式")
        print("\n📋 格式说明:")
        print("  • AC097R001: A侧，第097列，第001行")
        print("  • BC097R001: B侧，第097列，第001行")
        print("  • 支持双侧管板的大规模孔位管理")
        return True
    else:
        print("\n⚠️ 部分步骤失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)