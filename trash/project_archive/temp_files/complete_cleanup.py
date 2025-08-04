#!/usr/bin/env python3
"""
完整的根目录清理脚本
处理所有临时文件、报告文件和截图等
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def complete_cleanup():
    """完整清理根目录"""
    
    root_dir = Path(".")
    
    # 创建目标目录
    cleanup_archive = root_dir / "project_archive"
    reports_dir = cleanup_archive / "reports"
    screenshots_dir = cleanup_archive / "screenshots" 
    logs_dir = cleanup_archive / "logs"
    temp_files_dir = cleanup_archive / "temp_files"
    
    for dir_path in [cleanup_archive, reports_dir, screenshots_dir, logs_dir, temp_files_dir]:
        dir_path.mkdir(exist_ok=True)
    
    # 文件分类规则
    file_categories = {
        "reports": [
            # Markdown报告文件
            "BATCH_MODEL_REMOVAL_SUMMARY.md",
            "BATCH_SYSTEM_SUMMARY.md", 
            "BUTTON_FUNCTIONALITY_REPORT.md",
            "COHESION_COUPLING_ANALYSIS.md",
            "DATA_PATH_SUMMARY.md",
            "INSPECTION_BATCH_MIGRATION_SUMMARY.md",
            "NATIVE_RESTORATION_SUCCESS_REPORT.md",
            "QT_COORDINATE_SYSTEM_LESSON.md",
            "SECTOR_ASSIGNMENT_REFACTOR_COMPLETE.md",
            "SECTOR_ASSIGNMENT_REFACTOR_PLAN.md", 
            "SECTOR_REFACTOR_TEST_REPORT.md",
            "simulation_detection_summary.md"
        ],
        
        "screenshots": [
            # 截图文件
            "dongzhong_original.png",
            "dongzhong_sectors.png", 
            "dongzhong_snake_path.png",
            "gui_test_screenshot_1753782123.png",
            "hole_distribution_analysis.png",
            "sector_gui_test_screenshot.png"
        ],
        
        "logs": [
            # 日志文件
            "native_functionality_test.log",
            "cap1000_test_report.txt"
        ],
        
        "temp_files": [
            # 临时脚本文件
            "organize_test_files.py"
        ]
    }
    
    # 移动文件
    moved_files = []
    
    for category, files in file_categories.items():
        if category == "reports":
            target_dir = reports_dir
        elif category == "screenshots":
            target_dir = screenshots_dir
        elif category == "logs":
            target_dir = logs_dir
        else:
            target_dir = temp_files_dir
            
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
    
    # 检查是否还有其他临时文件
    remaining_files = []
    exclude_patterns = [
        "main.py",           # 主程序入口
        "README.md",         # 项目说明
        ".gitattributes",    # Git配置
        ".gitignore",        # Git忽略
        "detection_system.db" # 数据库
    ]
    
    for file_path in root_dir.iterdir():
        if file_path.is_file() and file_path.name not in exclude_patterns:
            # 检查是否是重要的目录
            if not any(important_dir in str(file_path) for important_dir in [
                "src", "config", "assets", "Data", "docs", "tests", 
                "reports", "logs", "backup", "backups", "trash",
                "test_archive", "project_archive", "old", "内窥镜图片", "数据"
            ]):
                remaining_files.append(file_path.name)
    
    # 创建清理报告
    report_content = f"""# 完整根目录清理报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 清理统计
- 移动文件总数: {len(moved_files)}
- 剩余需检查文件: {len(remaining_files)}

## 已移动文件分类

### 报告文档 ({len(file_categories['reports'])} 个)
存放位置: `project_archive/reports/`
- 项目重构和迁移报告
- 系统分析和设计文档
- 测试总结报告

### 截图文件 ({len(file_categories['screenshots'])} 个) 
存放位置: `project_archive/screenshots/`
- 测试截图和分析图表
- 功能演示图片

### 日志文件 ({len(file_categories['logs'])} 个)
存放位置: `project_archive/logs/`
- 测试运行日志
- 功能测试报告

### 临时文件 ({len(file_categories['temp_files'])} 个)
存放位置: `project_archive/temp_files/`
- 清理脚本和临时工具

## 移动的文件列表
"""
    
    for moved_file in moved_files:
        report_content += f"- {moved_file}\n"
    
    if remaining_files:
        report_content += f"\n## 剩余文件需要检查\n"
        for remaining_file in remaining_files:
            report_content += f"- {remaining_file}\n"
        report_content += f"\n⚠️ 请手动检查这些文件是否需要保留或移动\n"
    
    report_content += f"""
## 保留的核心文件
- main.py (项目入口)
- README.md (项目说明)
- .gitattributes, .gitignore (Git配置)
- detection_system.db (数据库)

## 保留的重要目录
- src/ (源代码)
- config/ (配置文件)
- assets/ (资源文件) 
- Data/ (数据目录)
- docs/ (文档)
- tests/ (测试)
- test_archive/ (测试存档)

## 清理效果
- 根目录文件大幅减少
- 所有报告、截图、日志已分类存档
- 项目结构更加清晰
- 便于后续维护和开发
"""
    
    # 写入报告
    report_path = cleanup_archive / "complete_cleanup_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📊 完整清理报告已生成: {report_path}")
    print(f"📁 文件已整理到: {cleanup_archive}")
    print(f"✨ 完成清理，移动了 {len(moved_files)} 个文件")
    
    if remaining_files:
        print(f"\n⚠️ 还有 {len(remaining_files)} 个文件需要手动检查")
        print("请查看报告了解详情")
    
    return moved_files, remaining_files

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 开始完整根目录清理")
    print("=" * 60)
    
    moved, remaining = complete_cleanup()
    
    print("\n" + "=" * 60)
    print("🎉 完整清理完成")
    print("=" * 60)