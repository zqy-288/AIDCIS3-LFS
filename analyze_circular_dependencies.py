#!/usr/bin/env python3
"""
分析项目中的循环依赖
"""

import os
import re
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple

class CircularDependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.import_statements: Dict[str, List[str]] = defaultdict(list)
        
    def analyze_file(self, file_path: Path) -> Set[str]:
        """分析单个文件的导入"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找所有导入语句
            import_patterns = [
                r'^from\s+([\w\.]+)\s+import',
                r'^import\s+([\w\.]+)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    # 只保留项目内部的导入
                    if match.startswith('src.'):
                        imports.add(match)
                        self.import_statements[str(file_path)].append(f"import {match}")
                        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            
        return imports
    
    def build_dependency_graph(self):
        """构建依赖图"""
        src_path = self.project_root / 'src'
        
        # 遍历所有Python文件
        for py_file in src_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            # 获取模块名
            relative_path = py_file.relative_to(self.project_root)
            module_name = str(relative_path).replace('/', '.').replace('\\', '.')[:-3]
            
            # 分析导入
            imports = self.analyze_file(py_file)
            
            # 构建依赖关系
            for imp in imports:
                # 转换导入路径为文件路径
                if imp.startswith('src.'):
                    self.dependencies[module_name].add(imp)
    
    def find_cycles_dfs(self) -> List[List[str]]:
        """使用DFS查找所有循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str, start: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, []):
                if neighbor == start and len(path) > 1:
                    # 找到循环
                    cycle = path[:]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor, start)
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            path.pop()
            rec_stack.remove(node)
        
        # 对每个节点进行DFS
        for node in self.dependencies:
            if node not in visited:
                dfs(node, node)
                
        return cycles
    
    def find_all_paths(self, start: str, end: str, max_depth: int = 15) -> List[List[str]]:
        """查找从start到end的所有路径（限制最大深度）"""
        paths = []
        
        def dfs_paths(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
                
            if current == target and len(path) > 1:
                paths.append(path[:])
                return
                
            for neighbor in self.dependencies.get(current, []):
                if neighbor not in path:  # 避免循环
                    path.append(neighbor)
                    dfs_paths(neighbor, target, path, depth + 1)
                    path.pop()
        
        dfs_paths(start, end, [start], 0)
        return paths
    
    def analyze_dependency_depth(self) -> Dict[str, int]:
        """分析每个模块的最大依赖深度"""
        depths = {}
        
        def get_depth(module: str, visited: Set[str]) -> int:
            if module in depths:
                return depths[module]
                
            if module in visited:
                return 0  # 循环依赖
                
            visited.add(module)
            
            if module not in self.dependencies or not self.dependencies[module]:
                depth = 1
            else:
                max_child_depth = 0
                for dep in self.dependencies[module]:
                    child_depth = get_depth(dep, visited.copy())
                    max_child_depth = max(max_child_depth, child_depth)
                depth = max_child_depth + 1
                
            depths[module] = depth
            return depth
        
        for module in self.dependencies:
            if module not in depths:
                get_depth(module, set())
                
        return depths
    
    def generate_report(self):
        """生成分析报告"""
        print("=" * 80)
        print("循环依赖分析报告")
        print("=" * 80)
        
        # 构建依赖图
        self.build_dependency_graph()
        
        # 查找循环依赖
        cycles = self.find_cycles_dfs()
        
        print(f"\n发现 {len(cycles)} 个循环依赖：\n")
        
        for i, cycle in enumerate(cycles, 1):
            print(f"循环 {i}:")
            for j in range(len(cycle)):
                print(f"  {cycle[j]}")
                if j < len(cycle) - 1:
                    print(f"    ↓")
            print(f"    ↓ (回到 {cycle[0]})")
            print()
        
        # 分析依赖深度
        depths = self.analyze_dependency_depth()
        sorted_depths = sorted(depths.items(), key=lambda x: x[1], reverse=True)
        
        print("\n依赖深度分析（前20个最深的模块）：")
        print("-" * 60)
        
        for module, depth in sorted_depths[:20]:
            print(f"{module:<50} 深度: {depth}")
        
        # 查找从main.py开始的最深路径
        main_module = "src.main"
        max_depth_module = sorted_depths[0][0] if sorted_depths else None
        
        if main_module in self.dependencies and max_depth_module:
            print(f"\n从 {main_module} 到最深模块的路径：")
            paths = self.find_all_paths(main_module, max_depth_module)
            
            if paths:
                # 选择最长的路径
                longest_path = max(paths, key=len)
                print(f"\n最长路径（{len(longest_path)}层）：")
                for i, module in enumerate(longest_path, 1):
                    print(f"  第{i}层: {module}")
        
        # 统计依赖最多的模块
        dependency_count = {m: len(deps) for m, deps in self.dependencies.items()}
        sorted_deps = sorted(dependency_count.items(), key=lambda x: x[1], reverse=True)
        
        print("\n依赖数量统计（前10个依赖最多的模块）：")
        print("-" * 60)
        
        for module, count in sorted_deps[:10]:
            print(f"{module:<50} 依赖数: {count}")
            
        # 识别核心模块（被依赖最多的）
        reverse_deps = defaultdict(set)
        for module, deps in self.dependencies.items():
            for dep in deps:
                reverse_deps[dep].add(module)
                
        sorted_reverse = sorted(reverse_deps.items(), key=lambda x: len(x[1]), reverse=True)
        
        print("\n被依赖次数统计（前10个被依赖最多的模块）：")
        print("-" * 60)
        
        for module, dependents in sorted_reverse[:10]:
            print(f"{module:<50} 被依赖次数: {len(dependents)}")

def main():
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建分析器
    analyzer = CircularDependencyAnalyzer(project_root)
    
    # 生成报告
    analyzer.generate_report()

if __name__ == "__main__":
    main()