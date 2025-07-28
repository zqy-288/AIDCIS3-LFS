"""
字体配置模块
"""
import matplotlib
import matplotlib.pyplot as plt


def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        # 使用简化的字体配置，避免复杂的字体检测
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        # 使用最基本的配置
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'


def apply_matplotlib_dark_theme(figure):
    """为matplotlib图表应用深色主题"""
    # 设置图形背景色
    figure.patch.set_facecolor('#2E3440')
    
    # 遍历所有子图
    for ax in figure.get_axes():
        # 设置子图背景色
        ax.set_facecolor('#3B4252')
        
        # 设置边框颜色
        ax.spines['bottom'].set_color('#D8DEE9')
        ax.spines['top'].set_color('#D8DEE9')
        ax.spines['right'].set_color('#D8DEE9')
        ax.spines['left'].set_color('#D8DEE9')
        
        # 设置刻度颜色
        ax.tick_params(axis='x', colors='#D8DEE9')
        ax.tick_params(axis='y', colors='#D8DEE9')
        
        # 设置标签颜色
        ax.xaxis.label.set_color('#D8DEE9')
        ax.yaxis.label.set_color('#D8DEE9')
        
        # 设置标题颜色
        ax.title.set_color('#D8DEE9')
        
        # 设置网格样式
        ax.grid(True, linestyle='--', alpha=0.3, color='#4C566A')
        
    # 刷新画布
    figure.canvas.draw_idle()