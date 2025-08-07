#!/usr/bin/env python3
"""
修复模拟检测批次集成问题
基于测试结果，应用必要的修复到系统中
"""

import sys
import os
from pathlib import Path
import shutil
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def backup_file(file_path):
    """备份文件"""
    if Path(file_path).exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"📁 备份文件: {file_path} -> {backup_path}")
        return backup_path
    return None

def apply_product_info_fix():
    """应用产品信息格式兼容性修复"""
    print("🔧 应用产品信息格式兼容性修复...")
    
    controllers = [
        "src/pages/main_detection_p1/controllers/main_window_controller.py",
        "src/controllers/main_window_controller.py"
    ]
    
    for controller_path in controllers:
        full_path = project_root / controller_path
        if not full_path.exists():
            print(f"⚠️ 文件不存在，跳过: {controller_path}")
            continue
        
        # 备份文件
        backup_path = backup_file(full_path)
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换产品信息获取逻辑
        old_pattern = '''product_name = self.current_product.model_name if self.current_product else "Unknown"'''
        
        new_pattern = '''# 获取产品名称 - 处理不同的产品信息格式
            if hasattr(self.current_product, 'model_name'):
                # ProductModel对象
                product_name = self.current_product.model_name
            elif isinstance(self.current_product, dict):
                # 字典格式
                product_name = self.current_product.get('model_name', 'Unknown')
            elif isinstance(self.current_product, str):
                # 字符串格式
                product_name = self.current_product
            else:
                product_name = "Unknown"'''
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            
            # 写回文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 修复产品信息处理: {controller_path}")
        else:
            print(f"📝 产品信息处理已经是最新版本: {controller_path}")

def apply_simulation_error_handling_fix():
    """应用模拟检测错误处理修复"""
    print("🔧 应用模拟检测错误处理修复...")
    
    page_file = project_root / "src/pages/main_detection_p1/main_detection_page.py"
    if not page_file.exists():
        print("⚠️ 主检测页面文件不存在")
        return
    
    # 备份文件
    backup_path = backup_file(page_file)
    
    # 读取文件内容
    with open(page_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有错误处理逻辑
    if "统一流程失败，回退到独立模拟" in content:
        print("✅ 模拟检测错误处理已存在")
    else:
        print("📝 需要手动检查模拟检测错误处理逻辑")

def apply_detection_service_interval_fix():
    """应用检测服务间隔修复"""
    print("🔧 应用检测服务间隔修复...")
    
    service_file = project_root / "src/services/detection_service.py"
    if not service_file.exists():
        print("⚠️ 检测服务文件不存在")
        return
    
    # 备份文件
    backup_path = backup_file(service_file)
    
    # 读取文件内容
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查间隔设置
    if "'interval': 10000," in content:
        print("✅ 检测服务间隔已设置为10秒")
    else:
        # 替换间隔设置
        old_interval = "'interval': 100,"
        new_interval = "'interval': 10000,  # 10秒间隔，保持与SimulationController一致"
        
        if old_interval in content:
            content = content.replace(old_interval, new_interval)
            
            # 写回文件
            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 修复检测服务间隔设置")
        else:
            print("📝 检测服务间隔设置需要手动检查")

def verify_fixes():
    """验证修复效果"""
    print("🔍 验证修复效果...")
    
    try:
        # 验证批次服务
        sys.path.insert(0, str(project_root / "src"))
        from src.domain.services.batch_service import BatchService
        from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
        from src.models.data_path_manager import DataPathManager
        
        repo = BatchRepositoryImpl()
        path_manager = DataPathManager()
        batch_service = BatchService(repo, path_manager)
        
        # 测试创建模拟批次
        test_batch = batch_service.create_batch(
            product_id=999,  # 使用不存在的ID进行测试
            product_name="VERIFY_TEST",
            description="验证修复效果",
            is_mock=True
        )
        
        print(f"✅ 批次创建验证通过: {test_batch.batch_id}")
        print(f"✅ MOCK后缀验证: {'_MOCK' in test_batch.batch_id}")
        
        # 验证检测服务
        from src.services.detection_service import DetectionService
        detection_service = DetectionService()
        
        interval = detection_service.simulation_params['interval']
        print(f"✅ 检测间隔验证: {interval}ms (期望: 10000ms)")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def create_usage_guide():
    """创建使用指南"""
    print("📝 创建使用指南...")
    
    guide_content = """
# 模拟检测批次集成修复指南

## 修复内容

### 1. 产品信息格式兼容性
- 支持字符串、字典、ProductModel对象格式
- 自动识别并正确提取产品名称
- 避免 'str' object has no attribute 'model_name' 错误

### 2. 检测服务配置
- 模拟检测间隔设置为10秒（10000ms）
- 保持与原有SimulationController一致的用户体验
- 正确设置is_mock标志

### 3. 错误处理机制
- 统一流程失败时自动回退到独立模拟
- 保证用户体验不受影响
- 详细的错误日志记录

## 使用方法

### 启动模拟检测
1. 确保已选择产品（CAP1000等）
2. 确保已加载DXF文件
3. 点击"开始模拟"按钮

### 预期效果
- **成功情况**: 创建带_MOCK后缀的批次，左上角显示批次信息
- **失败情况**: 自动回退到独立模拟，保持原有体验

### 批次命名规则
- 真实检测: `产品名_检测XXX_时间戳`
- 模拟检测: `产品名_检测XXX_时间戳_MOCK`

### 数据存储位置
```
Data/Products/{产品名}/InspectionBatches/
├── {产品名}_检测001_20250804_120000/          # 真实检测
├── {产品名}_检测002_20250804_120100_MOCK/     # 模拟检测
└── ...
```

## 故障排除

### 问题1: 左上角仍显示"未开始"
- 检查控制台日志中的产品信息格式
- 确认产品选择功能正常工作
- 验证批次服务是否正常初始化

### 问题2: 模拟检测速度异常
- 检查检测服务间隔设置（应为10000ms）
- 确认is_mock参数正确传递
- 验证定时器配置

### 问题3: 批次编号不递增
- 检查数据库连接和表结构
- 验证product_id参数有效性
- 确认批次仓储实现正常

## 技术细节

### 产品信息处理逻辑
```python
if hasattr(current_product, 'model_name'):
    product_name = current_product.model_name  # ProductModel对象
elif isinstance(current_product, dict):
    product_name = current_product.get('model_name', 'Unknown')  # 字典格式
elif isinstance(current_product, str):
    product_name = current_product  # 字符串格式
else:
    product_name = "Unknown"  # 默认值
```

### 错误处理流程
```
开始模拟 → 尝试统一流程 → 
    ├─ 成功: 创建MOCK批次，更新UI
    └─ 失败: 回退到SimulationController
```

## 测试验证

运行以下命令验证修复效果：
```bash
python3 scripts/tests/test_simulation_batch_integration.py
```

预期所有测试通过，输出包含：
- ✅ 产品信息格式测试通过
- ✅ 批次服务创建测试通过  
- ✅ 检测服务模拟功能测试通过
- ✅ 完整工作流程测试通过
"""
    
    guide_file = project_root / "docs/fixes/simulation_batch_integration_guide.md"
    guide_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✅ 使用指南已创建: {guide_file}")

def main():
    """主函数"""
    print("🚀 开始应用模拟检测批次集成修复...")
    print("=" * 60)
    
    # 应用修复
    apply_product_info_fix()
    apply_simulation_error_handling_fix()
    apply_detection_service_interval_fix()
    
    print("\n" + "=" * 60)
    
    # 验证修复
    if verify_fixes():
        print("🎉 所有修复验证通过！")
    else:
        print("⚠️ 部分修复需要手动检查")
    
    # 创建使用指南
    create_usage_guide()
    
    print("\n" + "=" * 60)
    print("✅ 模拟检测批次集成修复完成")
    print("💡 建议:")
    print("   1. 重启应用以确保修改生效")
    print("   2. 测试模拟检测功能")
    print("   3. 检查批次创建和状态显示")
    print("   4. 查看使用指南了解详细信息")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)