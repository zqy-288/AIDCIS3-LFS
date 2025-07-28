#!/usr/bin/env python3
"""
绘制DynamicSectorDisplayRefactored缩放功能流程图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建图形
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# 定义颜色
color_init = '#E8F4FD'      # 初始化 - 浅蓝
color_data = '#FFF4E6'      # 数据加载 - 浅橙
color_switch = '#E8F5E9'    # 扇形切换 - 浅绿
color_user = '#FCE4EC'      # 用户交互 - 浅粉
color_core = '#F3E5F5'      # 核心功能 - 浅紫

# 定义框样式
def create_box(ax, x, y, width, height, text, color, style='round'):
    """创建文本框"""
    if style == 'round':
        box = FancyBboxPatch((x, y), width, height,
                           boxstyle="round,pad=0.1",
                           facecolor=color,
                           edgecolor='black',
                           linewidth=1.5)
    else:
        box = FancyBboxPatch((x, y), width, height,
                           boxstyle="square,pad=0.1",
                           facecolor=color,
                           edgecolor='black',
                           linewidth=1.5)
    ax.add_patch(box)
    
    # 添加文本
    ax.text(x + width/2, y + height/2, text,
            ha='center', va='center',
            fontsize=10, weight='bold',
            wrap=True)
    
    return box

# 定义箭头
def create_arrow(ax, x1, y1, x2, y2, text='', style='->'):
    """创建箭头"""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                          connectionstyle="arc3,rad=.2",
                          arrowstyle=style,
                          mutation_scale=20,
                          linewidth=1.5,
                          color='black')
    ax.add_patch(arrow)
    
    # 添加箭头上的文本
    if text:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(mid_x, mid_y, text,
                ha='center', va='bottom',
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

# 标题
ax.text(50, 95, 'DynamicSectorDisplayRefactored 缩放功能流程图',
        ha='center', va='center',
        fontsize=16, weight='bold')

# 1. 初始化阶段
create_box(ax, 5, 80, 20, 8, '组件初始化', color_init)
create_box(ax, 30, 80, 25, 8, 'graphics_view创建\ndisable_auto_fit=True\nmax_auto_scale=1.5', color_init)
create_arrow(ax, 25, 84, 30, 84)

# 2. 数据加载阶段
create_box(ax, 5, 65, 20, 8, '数据加载\n_process_hole_collection', color_data)
create_box(ax, 30, 65, 25, 8, 'load_holes()\n场景设置但不缩放', color_data)
create_box(ax, 60, 65, 25, 8, '隐藏所有孔位\nsetVisible(False)', color_data)
create_arrow(ax, 25, 69, 30, 69)
create_arrow(ax, 55, 69, 60, 69)

# 3. 扇形切换阶段
create_box(ax, 5, 45, 20, 8, '扇形切换\nswitch_to_sector', color_switch)
create_box(ax, 30, 50, 20, 5, '显示扇形孔位', color_switch)
create_box(ax, 30, 40, 20, 5, '隐藏其他孔位', color_switch)
create_box(ax, 55, 45, 25, 8, '延迟50ms执行\ndelayed_fit()', color_switch)
create_arrow(ax, 25, 49, 30, 49)
create_arrow(ax, 25, 49, 30, 42.5)
create_arrow(ax, 50, 47.5, 55, 49)
create_arrow(ax, 50, 42.5, 55, 49)

# 4. 缩放执行
create_box(ax, 5, 25, 20, 8, '缩放执行\n_calculate_visible_bounds', color_core)
create_box(ax, 30, 25, 25, 8, '计算可见边界\n添加10%边距', color_core)
create_box(ax, 60, 25, 25, 8, 'fitInView()\nKeepAspectRatio', color_core)
create_arrow(ax, 25, 29, 30, 29)
create_arrow(ax, 55, 29, 60, 29)
create_arrow(ax, 55, 45, 12.5, 33, '触发缩放', '->')

# 5. 用户交互
create_box(ax, 5, 10, 15, 5, '键盘缩放', color_user)
create_box(ax, 25, 10, 15, 5, 'Ctrl +/-/0', color_user)
create_box(ax, 45, 10, 15, 5, 'F键适应', color_user)
create_box(ax, 65, 10, 20, 5, 'NavigationMixin处理', color_user)
create_arrow(ax, 20, 12.5, 25, 12.5)
create_arrow(ax, 40, 12.5, 45, 12.5)
create_arrow(ax, 60, 12.5, 65, 12.5)

# 添加说明框
legend_elements = [
    mpatches.Rectangle((0, 0), 1, 1, facecolor=color_init, edgecolor='black', label='初始化阶段'),
    mpatches.Rectangle((0, 0), 1, 1, facecolor=color_data, edgecolor='black', label='数据加载阶段'),
    mpatches.Rectangle((0, 0), 1, 1, facecolor=color_switch, edgecolor='black', label='扇形切换阶段'),
    mpatches.Rectangle((0, 0), 1, 1, facecolor=color_core, edgecolor='black', label='核心缩放功能'),
    mpatches.Rectangle((0, 0), 1, 1, facecolor=color_user, edgecolor='black', label='用户交互')
]
ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))

# 添加关键点说明
notes = [
    "1. disable_auto_fit=True 防止加载时自动缩放",
    "2. 数据加载后先隐藏所有孔位，避免初始显示问题",
    "3. 切换扇形时延迟50ms执行缩放，让UI有时间更新",
    "4. 计算可见孔位边界时添加10%边距",
    "5. 支持键盘缩放但禁用鼠标滚轮（Mac兼容性）"
]

y_pos = 2
for note in notes:
    ax.text(5, y_pos, note, fontsize=9, style='italic')
    y_pos -= 1.5

plt.title('缩放功能流程图', fontsize=16, weight='bold', pad=20)
plt.tight_layout()
plt.savefig('zoom_functionality_flowchart.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.savefig('zoom_functionality_flowchart.pdf', bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.show()