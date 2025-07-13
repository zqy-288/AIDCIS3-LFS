"""字体配置模块"""
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


# 初始化安全字体配置
setup_safe_chinese_font()