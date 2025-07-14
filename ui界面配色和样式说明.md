好的，非常乐意为您效劳。将不同开发者负责的模块在视觉上统一起来，是确保软件专业性和用户体验的关键。

一份清晰、详尽的设计规范文档是实现这一目标的最佳工具。下面我为您起草了一份专门针对您的“现代科技蓝”主题的UI设计规范文档。您可以直接将此文档分享给您的同事，他只需要遵循这份规范，就能轻松地将【主检测视图】的样式与您负责的界面完美统一。

-----

## **上位机软件“现代科技蓝”主题UI设计规范 (v1.0)**

**文档目的**：
本规范旨在为【主检测视图】及未来所有新模块的UI开发提供一套统一、明确的视觉设计和代码实现标准，确保整个上位机软件在风格、颜色、布局和交互上保持高度一致性，提升产品的专业感和用户体验。

### 1\. 设计原则

所有界面的设计应遵循以下核心原则：

  * **清晰为先**：确保关键数据和操作控件在视觉上最醒目、最易于理解。
  * **风格统一**：所有模块使用相同的颜色、字体和控件样式，形成统一的品牌感知。
  * **反馈及时**：用户的任何操作都应有即时的视觉反馈（如按钮悬停、状态变化）。
  * **布局规整**：使用统一的间距和对齐标准，营造专业、有序的界面观感。

### 2\. 色彩规范

整个应用严格遵循以下色彩定义。请在QSS和图表绘制中统一使用这些HEX色值。

| 用途 | 颜色预览 | 色值 (HEX) | 描述 |
| :--- | :--- | :--- | :--- |
| **主背景色** | █ | `#2C313C` | 用于窗口、页面的最底层背景。 |
| **面板背景色** | █ | `#313642` | 用于`QGroupBox`、表格、侧边栏等次级容器的背景，与主背景形成层次感。 |
| **标题栏/高亮背景** | █ | `#3A404E` | 用于独立的标题栏或需要突出的区域背景。 |
| **边框/分割线** | █ | `#404552` | 用于控件边框、分割线等，起到视觉分隔作用。 |
| **主文本/图标色** | █ | `#D3D8E0` | 用于大部分常规文字和图标，确保在深色背景上的可读性。 |
| **标题/醒目文字** | █ | `#FFFFFF` | 用于面板标题等需要强调的文字。 |
| **主操作色/主题蓝** | █ | `#007ACC` | **核心颜色**。用于主要操作按钮、选中的Tab下划线、高亮状态等。 |
| **成功/合格状态** | █ | `#2ECC71` | 用于表示“成功”、“合格”、“已连接”等积极状态。 |
| **警告/异常状态** | █ | `#E67E22` | 用于表示“警告”或需要注意的异常数据（如3D模型中的误差线）。 |
| **错误/不合格状态** | █ | `#E74C3C` | 用于表示“错误”、“失败”、“不合格”等负面状态。 |

### 3\. 字体规范

  * **通用字体族**：为保证在不同平台下的显示效果，字体设置应包含备选项。
    ```css
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC";
    ```
  * **字号层级**：
      * **主标题 (L1)**：`18px`, `bold` - 用于界面最顶层的大标题。
      * **面板标题 (L2)**：`16px`, `bold` - 用于`QGroupBox`或自定义标题栏的标题。
      * **正文/常规 (Body)**：`15px`, `normal` - 用于大部分标签、按钮、表格内容等。
      * **辅助/说明文字 (Caption)**：`13px`, `normal` - 用于状态栏、图例、次要说明等。

### 4\. 布局与间距

  * **标准间距**：控件组之间、布局与布局之间的标准间距建议为 `15px`。
  * **内边距**：容器（如`QGroupBox`）的内边距（`padding`）建议为 `10px`。
  * **控件内边距**：按钮（`QPushButton`）的内边距建议为 `padding: 8px 20px;`，以保证足够的点击区域和舒适的视觉效果。

### 5\. 核心组件QSS样式参考

为了实现全局统一，**强烈建议将所有样式代码集中到一个`theme.qss`文件中，并在Python代码中移除所有内联的`setStyleSheet`调用**。

#### 5.1 按钮 (`QPushButton`)

我们使用属性选择器来定义两种按钮，便于在代码中灵活调用。

  * **QSS 代码**:
    ```qss
    /* 次要/常规操作按钮 */
    QPushButton[class="ActionButton"] {
        background-color: #404552;
        color: #D3D8E0;
        border: 1px solid #505869;
        border-radius: 5px;
        padding: 8px 20px;
        font-weight: bold;
    }
    QPushButton[class="ActionButton"]:hover {
        background-color: #505869;
        border-color: #007ACC;
    }

    /* 主要操作按钮（蓝色） */
    QPushButton[class="PrimaryAction"] {
        background-color: #007ACC;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 20px;
        font-weight: bold;
    }
    QPushButton[class="PrimaryAction"]:hover {
        background-color: #0099FF;
    }
    ```
  * **Python 调用示例**:
    ```python
    # 创建一个次要按钮
    preview_button = QPushButton("预览")
    preview_button.setProperty("class", "ActionButton")

    # 创建一个主要按钮
    generate_button = QPushButton("生成")
    generate_button.setProperty("class", "PrimaryAction")
    ```

#### 5.2 面板 (`QGroupBox`)

为了实现带序号的步骤引导式布局，我们采用自定义标题栏的模式。

  * **QSS 代码**:
    ```qss
    /* 面板容器本身的样式 */
    QGroupBox {
        background-color: #313642;
        border: 1px solid #404552;
        border-radius: 8px;
        margin-top: 10px; /* 为自定义标题行留出空间 */
    }

    /* 步骤序号标签的样式 */
    #StepNumberLabel {
        font-size: 16px;
        font-weight: bold;
        color: white;
        background-color: #007ACC;
        min-width: 24px; max-width: 24px;
        min-height: 24px; max-height: 24px;
        border-radius: 12px;
        qproperty-alignment: 'AlignCenter';
    }

    /* 步骤标题文字的样式 */
    #StepTitleLabel {
        font-size: 16px;
        font-weight: bold;
        color: #D3D8E0;
    }
    ```
  * **Python 调用示例**:
    ```python
    # 步骤1：工件选择
    step1_header = self.create_step_header("1", "工件选择")
    main_layout.addWidget(step1_header)

    workpiece_group = QGroupBox() # GroupBox本身不再需要标题
    # ... 在workpiece_group中添加控件 ...
    main_layout.addWidget(workpiece_group)

    # create_step_header 是一个辅助方法，用于创建带序号和文字的QHBoxLayout
    ```

### 6\. 图标使用规范

  * **图标库**：强烈推荐使用 `qtawesome` 库来集成 Font Awesome 等矢量图标，以保证图标在任何分辨率下都清晰美观，且易于更换颜色。
  * **使用场景**：
      * **表格操作**：对于表格中的“打开”、“删除”等操作，应使用只有图标的`QToolButton`，并提供详细的`setToolTip`。
      * **状态指示**：在状态栏或信息标签旁，使用图标（如`✅`, `❌`, `⚠️`, `⚙️`）来辅助文字，增强信息传达效率。

### 7\. 可视化图表样式 (Matplotlib)

对于嵌入的Matplotlib图表，必须通过Python代码设置其样式，以匹配深色主题。请将以下函数作为公共模块，在绘制图表时调用。

  * **2D图表样式函数**:

    ```python
    def apply_dark_theme_2d(figure, axes):
        figure.patch.set_facecolor('#313642')
        axes.set_facecolor('#313642')
        axes.spines['bottom'].set_color('#505869')
        axes.spines['top'].set_color('#505869')
        axes.spines['left'].set_color('#505869')
        axes.spines['right'].set_color('#505869')
        axes.tick_params(axis='x', colors='#D3D8E0')
        axes.tick_params(axis='y', colors='#D3D8E0')
        axes.xaxis.label.set_color('#D3D8E0')
        axes.yaxis.label.set_color('#D3D8E0')
        axes.title.set_color('#FFFFFF')
        axes.grid(True, color='#404552', linestyle='--', alpha=0.5)
    ```

  * **3D图表样式函数**:

    ```python
    def apply_dark_theme_3d(figure, axes):
        figure.patch.set_facecolor('#2C313C')
        axes.set_facecolor('#2C313C')
        axes.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        axes.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        axes.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        # ... 其他3D样式设置，参考之前提供的代码 ...
    ```

### 8\. 整合 checklist

为方便您的同事进行修改，请他遵循以下步骤：

1.  [ ] **引入全局QSS**：确保主程序加载了统一的 `theme.qss` 文件。
2.  [ ] **移除内联样式**：在他的代码中（如`main_inspection_view.py`），搜索并删除所有的 `widget.setStyleSheet(...)` 调用。
3.  [ ] **应用规范样式**：对于按钮等需要区分主次的控件，使用 `widget.setProperty("class", "PrimaryAction")` 的方式来应用样式。
4.  [ ] **统一布局**：遵循规范中定义的间距和边距标准。
5.  [ ] **适配图表**：在创建Matplotlib图表后，调用对应的 `apply_dark_theme_*` 函数。
6.  [ ] **使用图标**：将功能性强、空间小的按钮替换为`qtawesome`图标。

-----

希望这份详尽的文档能帮助您和您的同事高效地完成工作整合，打造出一款风格统一、体验卓越的优秀软件产品。