#!/usr/bin/env python3
"""
性能警告禁用脚本
临时禁用频繁的性能警告，提升用户体验
"""

import sys
from pathlib import Path

# 添加src路径到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def disable_performance_warnings():
    """禁用性能警告"""
    try:
        from modules.performance_optimizer import get_performance_optimizer
        
        # 获取性能优化器实例
        optimizer = get_performance_optimizer()
        
        if optimizer:
            # 临时禁用性能警告
            optimizer.config.log_performance_warnings = False
            optimizer.config.enable_performance_monitoring = False
            
            # 停止监控定时器
            if hasattr(optimizer, 'metrics_timer'):
                optimizer.metrics_timer.stop()
            
            # 停止内存监控定时器
            if hasattr(optimizer.memory_monitor, 'monitor_timer'):
                optimizer.memory_monitor.monitor_timer.stop()
            
            print("✅ 性能警告已禁用")
            print("✅ 性能监控已停止")
            print("✅ 内存监控已停止")
            print("\n注意: 这是临时解决方案，重启应用后会恢复默认设置")
            return True
        else:
            print("❌ 未找到性能优化器实例")
            return False
            
    except Exception as e:
        print(f"❌ 禁用性能警告失败: {e}")
        return False

def enable_conservative_mode():
    """启用保守模式"""
    try:
        from modules.performance_optimizer import get_performance_optimizer, MemoryStrategy
        
        optimizer = get_performance_optimizer()
        
        if optimizer:
            # 设置保守配置
            optimizer.config.memory_strategy = MemoryStrategy.CONSERVATIVE
            optimizer.config.max_visible_items = 200
            optimizer.config.update_interval_ms = 1000  # 1秒更新一次
            optimizer.config.log_performance_warnings = False
            optimizer.config.gc_threshold_mb = 480.0  # 更高的阈值
            
            print("✅ 已切换到保守模式")
            print("- 减少可见项目数: 200")
            print("- 降低更新频率: 1秒")
            print("- 提高内存阈值: 480MB")
            print("- 禁用性能警告")
            return True
        else:
            print("❌ 未找到性能优化器实例")
            return False
            
    except Exception as e:
        print(f"❌ 启用保守模式失败: {e}")
        return False

def show_current_config():
    """显示当前配置"""
    try:
        from modules.performance_optimizer import get_performance_optimizer
        
        optimizer = get_performance_optimizer()
        
        if optimizer:
            config = optimizer.config
            print("📊 当前性能优化器配置:")
            print(f"- 渲染策略: {config.rendering_strategy.value}")
            print(f"- 内存策略: {config.memory_strategy.value}")
            print(f"- 最大可见项目: {config.max_visible_items}")
            print(f"- 最大内存: {config.max_memory_mb}MB")
            print(f"- 垃圾回收阈值: {config.gc_threshold_mb}MB")
            print(f"- 更新间隔: {config.update_interval_ms}ms")
            print(f"- 性能监控: {'启用' if config.enable_performance_monitoring else '禁用'}")
            print(f"- 性能警告: {'启用' if config.log_performance_warnings else '禁用'}")
            print(f"- 异步渲染: {'启用' if config.enable_async_rendering else '禁用'}")
            
            # 显示当前性能指标
            metrics = optimizer.get_performance_metrics()
            print(f"\n📈 当前性能指标:")
            print(f"- 帧率: {metrics.get('frame_rate', 0):.1f} FPS")
            print(f"- 内存使用: {metrics.get('memory_usage_mb', 0):.1f}MB")
            print(f"- 渲染时间: {metrics.get('render_time_ms', 0):.1f}ms")
            print(f"- 缓存命中率: {metrics.get('cache_hit_rate', 0)*100:.1f}%")
            
            return True
        else:
            print("❌ 未找到性能优化器实例")
            return False
            
    except Exception as e:
        print(f"❌ 获取配置失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 性能优化器配置工具")
    print("=" * 40)
    
    while True:
        print("\n请选择操作:")
        print("1. 禁用性能警告")
        print("2. 启用保守模式")
        print("3. 显示当前配置")
        print("4. 退出")
        
        try:
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                disable_performance_warnings()
            elif choice == '2':
                enable_conservative_mode()
            elif choice == '3':
                show_current_config()
            elif choice == '4':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择，请输入1-4")
                
        except KeyboardInterrupt:
            print("\n👋 用户取消，退出")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()