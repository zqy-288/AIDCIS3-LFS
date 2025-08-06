"""
字体配置模块
统一处理matplotlib中文字体设置，避免字体警告
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import os
import warnings


def suppress_font_warnings():
    """抑制字体相关警告"""
    # 过滤matplotlib字体警告
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    warnings.filterwarnings('ignore', message='.*Glyph.*missing from font.*')


def get_available_chinese_fonts():
    """获取系统可用的中文字体"""
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 常见中文字体列表
    chinese_fonts = [
        'Microsoft YaHei',
        'SimHei', 
        'SimSun',
        'KaiTi',
        'FangSong',
        'Arial Unicode MS',
        'Noto Sans CJK SC',
        'WenQuanYi Micro Hei',
        'Hiragino Sans GB',
        'PingFang SC',
        'STHeiti',
        'STSong'
    ]
    
    # 查找可用的中文字体
    found_fonts = []
    for font in chinese_fonts:
        if font in available_fonts:
            found_fonts.append(font)
    
    return found_fonts


def setup_matplotlib_chinese_font():
    """设置matplotlib中文字体"""
    # 抑制字体警告
    suppress_font_warnings()
    
    # 获取可用中文字体
    chinese_fonts = get_available_chinese_fonts()
    
    if chinese_fonts:
        primary_font = chinese_fonts[0]
        print(f"使用中文字体: {primary_font}")
        
        # 设置字体优先级列表
        font_list = chinese_fonts + ['DejaVu Sans', 'Arial', 'sans-serif']
    else:
        print("未找到中文字体，使用默认字体")
        primary_font = 'DejaVu Sans'
        font_list = ['DejaVu Sans', 'Arial', 'sans-serif']
    
    # 配置matplotlib字体参数
    plt.rcParams.update({
        'font.sans-serif': font_list,
        'font.family': 'sans-serif',
        'axes.unicode_minus': False,  # 解决负号显示问题
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9
    })
    
    return primary_font


def add_system_fonts():
    """添加系统字体到matplotlib"""
    system = platform.system()
    
    if system == "Windows":
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
            r"C:\Windows\Fonts\msyh.ttf",      # Microsoft YaHei
            r"C:\Windows\Fonts\simhei.ttf",    # SimHei
            r"C:\Windows\Fonts\simsun.ttc",    # SimSun
            r"C:\Windows\Fonts\kaiti.ttf",     # KaiTi
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    
    added_fonts = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                fm.fontManager.addfont(font_path)
                added_fonts.append(font_path)
                print(f"添加字体: {font_path}")
            except Exception as e:
                print(f"添加字体失败 {font_path}: {e}")
    
    return added_fonts


def configure_matplotlib_for_chinese():
    """配置matplotlib以支持中文显示"""
    # 设置后端 - 只在需要时设置
    try:
        # 检查是否在GUI环境中
        import os
        if 'DISPLAY' in os.environ or platform.system() == 'Darwin' or platform.system() == 'Windows':
            # 尝试设置Qt后端
            try:
                import PySide6
                matplotlib.use('Qt5Agg')
            except ImportError:
                try:
                    import PyQt5
                    matplotlib.use('Qt5Agg')
                except ImportError:
                    # 如果没有Qt，使用Agg后端
                    matplotlib.use('Agg')
        else:
            # 非GUI环境使用Agg后端
            matplotlib.use('Agg')
    except Exception as e:
        print(f"设置matplotlib后端失败: {e}")
        matplotlib.use('Agg')

    # 添加系统字体
    add_system_fonts()

    # 设置中文字体
    primary_font = setup_matplotlib_chinese_font()

    # 刷新字体缓存
    try:
        fm.fontManager.__init__()
    except Exception as e:
        print(f"刷新字体缓存失败: {e}")

    return primary_font


def create_figure_with_chinese_support(figsize=(10, 8), dpi=100):
    """创建支持中文的matplotlib图形"""
    # 确保字体配置
    configure_matplotlib_for_chinese()
    
    # 创建图形
    fig = plt.figure(figsize=figsize, dpi=dpi)
    
    return fig


def set_axes_chinese_labels(ax, title="", xlabel="", ylabel=""):
    """为坐标轴设置中文标签"""
    if title:
        ax.set_title(title, fontsize=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)


# 在模块导入时自动配置
if __name__ != "__main__":
    # 只在非主程序运行时配置
    try:
        configure_matplotlib_for_chinese()
    except Exception as e:
        print(f"字体配置失败: {e}")
        # 使用基本配置
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['DejaVu Sans', 'Arial'],
            'axes.unicode_minus': False
        })


if __name__ == "__main__":
    # 测试字体配置
    print("测试字体配置...")
    
    # 获取可用字体
    fonts = get_available_chinese_fonts()
    print(f"可用中文字体: {fonts}")
    
    # 配置字体
    primary_font = configure_matplotlib_for_chinese()
    print(f"主要字体: {primary_font}")
    
    # 测试绘图
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3], [1, 4, 2])
    ax.set_title("测试中文标题")
    ax.set_xlabel("X轴标签")
    ax.set_ylabel("Y轴标签")
    
    print("字体配置测试完成")
