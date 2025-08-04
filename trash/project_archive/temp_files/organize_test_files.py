#!/usr/bin/env python3
"""
根目录测试文件整理脚本
将所有测试和诊断文件分类整理到适当目录
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def organize_test_files():
    """整理测试文件到相应目录"""
    
    root_dir = Path(".")
    
    # 创建目标目录
    test_archive_dir = root_dir / "test_archive"
    completed_tests = test_archive_dir / "completed_tests"
    diagnostic_tools = test_archive_dir / "diagnostic_tools" 
    fix_scripts = test_archive_dir / "fix_scripts"
    utility_scripts = test_archive_dir / "utility_scripts"
    
    for dir_path in [test_archive_dir, completed_tests, diagnostic_tools, fix_scripts, utility_scripts]:
        dir_path.mkdir(exist_ok=True)
    
    # 文件分类规则
    file_categories = {
        "completed_tests": [
            # 扇形测试相关
            "test_sector_assignment_verify.py",
            "test_sector_fix.py", 
            "test_sector_gui.py",
            "test_sector_gui_simple.py",
            "test_sector_integration.py",
            "test_sector_refactoring.py",
            "test_sector_screenshot.py",
            "test_sector_visualization.py",
            "test_sector_zoom_adaptive.py",
            "test_sector_zoom_fixed.py",
            "test_sector_zoom_optimized.py",
            "test_sector_zoom_quadrant.py",
            "test_sector_zoom_simple.py",
            "test_sector_zoom_view.py",
            "test_dxf_sector_fixed.py",
            
            # 全景图测试相关
            "test_panorama_click.py",
            "test_panorama_integration.py", 
            "test_panorama_migration.py",
            "simple_panorama_test.py",
            "simple_sector_test.py",
            "standalone_sector_test.py",
            
            # GUI测试相关
            "test_gui_3min.py",
            "test_gui_screenshot.py",
            "test_gui_with_dxf_fix.py",
            "test_complete_gui.py",
            "test_center_view.py",
            
            # 主窗口测试相关
            "test_main_startup.py",
            "test_main_window_direct.py",
            "test_main_window_dxf.py", 
            "test_main_window_panorama.py",
            
            # P1视图测试相关
            "test_p1_import_only.py",
            "test_p1_no_matplotlib.py",
            "test_p1_simple.py",
            "test_p1_view_changes.py",
            "test_p1_workpiece_diagram.py",
            
            # 其他功能测试
            "test_all_fixes_final.py",
            "test_final_integration.py",
            "test_fixed_errors.py",
            "test_fixes.py",
            "test_business_service_fix.py",
            "test_cap1000_loading.py",
            "test_coordinate_system.py",
            "test_dongzhong_render.py",
            "test_dxf_loading.py",
            "test_minimal_import.py",
            "test_new_batch_architecture.py",
            "test_product_selection_simulation.py",
            "test_refactored_data_flow.py",
            "test_refactored_integration.py",
            "test_render_path_fix.py",
            "test_snake_direct.py",
            "test_snake_simulation.py",
            "verify_p1_implementation.py"
        ],
        
        "diagnostic_tools": [
            "diagnose_sector_display.py",
            "diagnose_sector_rendering.py",
            "debug_dxf_loading.py",
            "check_panorama_sectors.py",
            "check_sector_files.py",
            "analyze_hole_distribution.py"
        ],
        
        "fix_scripts": [
            "fix_panorama_imports.py",
            "fix_product_selection_type_mismatch.py",
            "fix_sector_visibility.py"
        ],
        
        "utility_scripts": [
            "update_all_panorama_imports.py",
            "update_cap1000_dxf_path.py",
            "update_panorama_imports.py",
            "demonstrate_batch_system.py"
        ]
    }
    
    # 移动文件
    moved_files = []
    kept_files = []
    
    for category, files in file_categories.items():
        target_dir = test_archive_dir / category
        
        for filename in files:
            source_path = root_dir / filename
            if source_path.exists():
                target_path = target_dir / filename
                try:
                    shutil.move(str(source_path), str(target_path))
                    moved_files.append(f"{filename} -> {category}/")
                    print(f"✅ 移动 {filename} 到 {category}/")
                except Exception as e:
                    print(f"❌ 移动 {filename} 失败: {e}")
            else:
                print(f"⚠️ 文件不存在: {filename}")
    
    # 检查是否有遗漏的测试文件
    remaining_test_files = []
    for file_path in root_dir.glob("*.py"):
        filename = file_path.name
        if any(pattern in filename for pattern in ["test_", "debug_", "diagnose_", "check_", "fix_", "simple_", "standalone_", "update_", "analyze_", "verify_", "demonstrate_"]):
            if filename not in [f for files in file_categories.values() for f in files]:
                remaining_test_files.append(filename)
                kept_files.append(filename)
    
    # 创建整理报告
    report_content = f"""# 测试文件整理报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 整理统计
- 总计移动文件: {len(moved_files)}
- 保留在根目录的文件: {len(kept_files)}

## 文件分类

### 已完成测试 ({len(file_categories['completed_tests'])} 个)
存放位置: `test_archive/completed_tests/`
- 扇形测试相关: {len([f for f in file_categories['completed_tests'] if 'sector' in f])} 个
- 全景图测试相关: {len([f for f in file_categories['completed_tests'] if 'panorama' in f or 'simple' in f or 'standalone' in f])} 个
- GUI测试相关: {len([f for f in file_categories['completed_tests'] if 'gui' in f or 'complete' in f or 'center' in f])} 个
- 主窗口测试相关: {len([f for f in file_categories['completed_tests'] if 'main_window' in f or 'main_startup' in f])} 个
- P1视图测试相关: {len([f for f in file_categories['completed_tests'] if 'p1_' in f])} 个

### 诊断工具 ({len(file_categories['diagnostic_tools'])} 个)
存放位置: `test_archive/diagnostic_tools/`
用于问题诊断和状态检查的脚本

### 修复脚本 ({len(file_categories['fix_scripts'])} 个)
存放位置: `test_archive/fix_scripts/`
用于修复特定问题的脚本

### 实用工具 ({len(file_categories['utility_scripts'])} 个)
存放位置: `test_archive/utility_scripts/`
用于更新和演示的实用脚本

## 移动的文件列表
"""
    
    for moved_file in moved_files:
        report_content += f"- {moved_file}\n"
    
    if kept_files:
        report_content += f"\n## 保留在根目录的文件\n"
        for kept_file in kept_files:
            report_content += f"- {kept_file}\n"
    
    report_content += f"""
## 建议操作
1. ✅ 已完成的测试文件已归档，可安全删除
2. 🔧 诊断工具保留备用，用于未来问题排查
3. 🛠️ 修复脚本保留备用，可用于类似问题修复
4. 🚀 实用工具可集成到项目管理脚本中

## 清理效果
- 根目录Python文件从 {len(moved_files) + len(kept_files)} 个减少到 {len(kept_files)} 个
- 测试相关文件已分类存档到 `test_archive/` 目录
- 项目根目录更加整洁，便于维护
"""
    
    # 写入报告
    report_path = test_archive_dir / "organization_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📊 整理报告已生成: {report_path}")
    print(f"📁 测试文件已整理到: {test_archive_dir}")
    print(f"✨ 根目录清理完成，移动了 {len(moved_files)} 个文件")
    
    return moved_files, kept_files

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 开始整理根目录测试文件")
    print("=" * 60)
    
    moved, kept = organize_test_files()
    
    print("\n" + "=" * 60)
    print("🎉 整理完成")
    print("=" * 60)