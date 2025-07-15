# 修复全景图高亮遮挡孔位问题

## 问题描述
1. CompletePanoramaWidget（侧边栏全景图）的高亮层完全遮挡了孔位
2. 系统启动时自动高亮了扇形1
3. 没有清除高亮的方法

## 已完成的修复

### 1. 调整高亮层透明度和Z序
```python
# 原来：
highlight_color = QColor(255, 193, 7, 80)  # 不够透明
self.setZValue(10)  # 在孔位上方

# 修改为：
highlight_color = QColor(255, 193, 7, 30)  # 更透明
self.setZValue(-10)  # 在孔位下方
```

### 2. 临时解决方案
要暂时解决这个问题，您可以：

1. **注释掉自动高亮代码**（main_window.py 第1700行）：
```python
# QTimer.singleShot(300, lambda: self.sidebar_panorama.highlight_sector(SectorQuadrant.SECTOR_1))
```

2. **添加清除高亮的快捷方式**：
在主窗口添加一个快捷键来清除高亮：
```python
# 在 MainWindow.__init__ 中添加
from PySide6.QtGui import QShortcut, QKeySequence
clear_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
clear_shortcut.activated.connect(lambda: self.sidebar_panorama.clear_highlight() if hasattr(self, 'sidebar_panorama') else None)
```

## 效果
- 高亮层现在更透明（alpha=30）
- 高亮层在孔位下方（z=-10），不会遮挡孔位
- 可以通过快捷键清除高亮

## 建议
1. 考虑在UI中添加一个清除高亮的按钮
2. 或者让高亮只显示边框而不填充
3. 提供配置选项让用户选择是否自动高亮