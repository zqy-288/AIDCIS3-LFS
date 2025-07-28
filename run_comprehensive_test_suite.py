#!/usr/bin/env python3
"""
综合测试套件运行器 - 零容忍全面测试
Comprehensive test suite runner with zero tolerance
包含: 单元测试 + 集成测试 + UI自动化测试 + 性能测试
"""

import sys
import os
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'comprehensive_test_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    """综合测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.test_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'execution_time': 0
        }
    
    def run_all_tests(self):
        """运行所有测试套件"""
        logger.info("🚀 开始综合测试套件 - 零容忍测试")
        logger.info("=" * 60)
        
        # 测试套件配置
        test_suites = [
            {
                'name': '零容忍核心测试',
                'script': 'test_runner_zero_tolerance_fixed.py',
                'critical': True,
                'timeout': 120
            },
            {
                'name': 'UI自动化测试',
                'script': 'tests/playwright/test_comprehensive_ui_automation.py',
                'critical': True,
                'timeout': 300,
                'use_pytest': True
            },
            {
                'name': '主窗口初始化测试',
                'script': 'tests/playwright/test_main_window_initialization.py',
                'critical': True,
                'timeout': 180,
                'use_pytest': True
            },
            {
                'name': 'DXF功能测试',
                'script': 'tests/playwright/test_dxf_loading_functionality.py',
                'critical': False,
                'timeout': 240,
                'use_pytest': True
            }
        ]
        
        # 执行测试套件
        for suite in test_suites:
            logger.info(f"🧪 执行测试套件: {suite['name']}")
            result = self.run_test_suite(suite)
            self.test_results[suite['name']] = result
            
            # 关键测试失败则停止
            if suite['critical'] and not result['passed']:
                logger.error(f"❌ 关键测试套件失败: {suite['name']}")
                logger.error("🛑 停止执行后续测试")
                break
        
        # 生成综合报告
        self.generate_comprehensive_report()
        
        # 返回总体结果
        return self.calculate_overall_success()
    
    def run_test_suite(self, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试套件"""
        result = {
            'name': suite_config['name'],
            'passed': False,
            'output': '',
            'error': '',
            'execution_time': 0,
            'test_count': 0,
            'passed_count': 0,
            'failed_count': 0
        }
        
        start_time = time.time()
        
        try:
            # 构建命令
            if suite_config.get('use_pytest', False):
                cmd = [
                    sys.executable, '-m', 'pytest',
                    suite_config['script'],
                    '-v', '--tb=short',
                    '--disable-warnings'
                ]
            else:
                cmd = [sys.executable, suite_config['script']]
            
            logger.info(f"📝 执行命令: {' '.join(cmd)}")
            
            # 运行测试
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite_config.get('timeout', 300),
                cwd=PROJECT_ROOT
            )
            
            result['execution_time'] = time.time() - start_time
            result['output'] = process.stdout
            result['error'] = process.stderr
            
            # 分析测试结果
            if process.returncode == 0:
                result['passed'] = True
                logger.info(f"✅ {suite_config['name']} - 通过")
            else:
                result['passed'] = False
                logger.error(f"❌ {suite_config['name']} - 失败 (返回码: {process.returncode})")
            
            # 解析测试统计
            self.parse_test_statistics(result)
            
        except subprocess.TimeoutExpired:
            result['error'] = f"测试超时 ({suite_config.get('timeout', 300)}秒)"
            result['execution_time'] = suite_config.get('timeout', 300)
            logger.error(f"⏰ {suite_config['name']} - 超时")
            
        except Exception as e:
            result['error'] = f"执行异常: {e}"
            result['execution_time'] = time.time() - start_time
            logger.error(f"💥 {suite_config['name']} - 异常: {e}")
        
        return result
    
    def parse_test_statistics(self, result: Dict[str, Any]):
        """解析测试统计信息"""
        output = result['output'] + result['error']
        
        # 查找pytest格式的统计信息
        import re
        
        # pytest格式: "5 passed" 或 "3 failed, 2 passed"
        pytest_pattern = r'(\d+)\s+(passed|failed|skipped)'
        matches = re.findall(pytest_pattern, output, re.IGNORECASE)
        
        for count, status in matches:
            count = int(count)
            if status.lower() == 'passed':
                result['passed_count'] = count
            elif status.lower() == 'failed':
                result['failed_count'] = count
            elif status.lower() == 'skipped':
                result['skipped_count'] = count
        
        result['test_count'] = result['passed_count'] + result['failed_count'] + result.get('skipped_count', 0)
        
        # 查找自定义测试格式 "通过: X/Y"
        custom_pattern = r'通过:\s*(\d+)\/(\d+)'
        custom_match = re.search(custom_pattern, output)
        if custom_match:
            result['passed_count'] = int(custom_match.group(1))
            result['test_count'] = int(custom_match.group(2))
            result['failed_count'] = result['test_count'] - result['passed_count']
        
        # 更新全局统计
        self.test_stats['total_tests'] += result['test_count']
        self.test_stats['passed_tests'] += result['passed_count']
        self.test_stats['failed_tests'] += result['failed_count']
    
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        logger.info("📊 生成综合测试报告...")
        
        total_execution_time = time.time() - self.start_time
        self.test_stats['execution_time'] = total_execution_time
        
        # 计算成功率
        success_rate = 0
        if self.test_stats['total_tests'] > 0:
            success_rate = (self.test_stats['passed_tests'] / self.test_stats['total_tests']) * 100
        
        # 生成Markdown报告
        report_content = f"""# 🎯 AIDCIS3-LFS 综合测试报告

## 📋 执行摘要

**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**总执行时间**: {total_execution_time:.2f} 秒  
**测试成功率**: {success_rate:.1f}%

## 📊 统计概览

| 指标 | 数量 |
|------|------|
| 总测试数 | {self.test_stats['total_tests']} |
| 通过测试 | {self.test_stats['passed_tests']} ✅ |
| 失败测试 | {self.test_stats['failed_tests']} ❌ |
| 跳过测试 | {self.test_stats.get('skipped_tests', 0)} ⏭️ |

## 🧪 测试套件详情

"""
        
        for suite_name, result in self.test_results.items():
            status_icon = "✅" if result['passed'] else "❌"
            report_content += f"""### {status_icon} {suite_name}

- **状态**: {'通过' if result['passed'] else '失败'}
- **执行时间**: {result['execution_time']:.2f} 秒
- **测试数量**: {result['test_count']}
- **通过数量**: {result['passed_count']}
- **失败数量**: {result['failed_count']}

"""
            
            if result['error']:
                report_content += f"""**错误信息**:
```
{result['error'][:500]}{'...' if len(result['error']) > 500 else ''}
```

"""
        
        # 添加总结
        if success_rate == 100:
            report_content += """## 🎉 测试结论

**所有测试通过！** 系统已达到零容忍质量标准，可以安全部署到生产环境。

"""
        elif success_rate >= 90:
            report_content += f"""## ⚠️ 测试结论

**大部分测试通过** ({success_rate:.1f}%)，但仍有少量失败需要修复。系统基本达到质量标准。

"""
        else:
            report_content += f"""## ❌ 测试结论

**测试失败过多** ({success_rate:.1f}%)，系统未达到质量标准，需要重大修复。

"""
        
        # 保存报告
        report_file = PROJECT_ROOT / 'COMPREHENSIVE_TEST_REPORT.md'
        report_file.write_text(report_content, encoding='utf-8')
        
        # 保存JSON格式的详细结果
        json_report = {
            'timestamp': time.time(),
            'execution_time': total_execution_time,
            'success_rate': success_rate,
            'statistics': self.test_stats,
            'test_results': self.test_results
        }
        
        json_file = PROJECT_ROOT / 'test_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 报告已保存: {report_file}")
        logger.info(f"📊 详细结果已保存: {json_file}")
    
    def calculate_overall_success(self) -> bool:
        """计算总体成功状态"""
        if self.test_stats['total_tests'] == 0:
            logger.warning("⚠️ 没有执行任何测试")
            return False
        
        success_rate = (self.test_stats['passed_tests'] / self.test_stats['total_tests']) * 100
        
        logger.info("=" * 60)
        logger.info(f"🎯 综合测试完成")
        logger.info(f"📊 成功率: {success_rate:.1f}% ({self.test_stats['passed_tests']}/{self.test_stats['total_tests']})")
        logger.info(f"⏱️ 总时间: {time.time() - self.start_time:.2f}秒")
        
        if success_rate == 100:
            logger.info("🎉 所有测试通过！系统达到零容忍质量标准！")
            return True
        elif success_rate >= 90:
            logger.warning(f"⚠️ 大部分测试通过，但有{self.test_stats['failed_tests']}个失败")
            return False
        else:
            logger.error(f"❌ 测试失败过多，系统未达到质量标准")
            return False

def main():
    """主函数"""
    logger.info("🚀 启动AIDCIS3-LFS综合测试套件")
    
    # 检查环境
    if not PROJECT_ROOT.exists():
        logger.error("❌ 项目根目录不存在")
        return 1
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(PROJECT_ROOT)
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # 运行测试套件
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())