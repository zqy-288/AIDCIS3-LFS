# 搜索显示ID格式修复

## 问题描述
搜索孔位 C001R002 时，UI显示的ID标签是 'R002C001' 而不是 'C001R002'，格式被错误地反转了。

## 问题原因
在 `update_hole_info_display()` 方法中（main_window.py 第1839行），使用了错误的格式：
```python
id_text = f"R{hole.row:03d}C{hole.column:03d}"  # 错误：R行C列
```

## 修复方案
改为使用项目标准的 C{column}R{row} 格式：
```python
id_text = f"C{hole.column:03d}R{hole.row:03d}"  # 正确：C列R行
```

## 效果
- 孔位ID显示格式与项目标准一致
- 搜索 C001R002 时，UI显示为 C001R002 而不是 R002C001
- 保持了整个项目的ID格式统一性