import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import re
import threading
import os
import webbrowser
import time
from py.extract_iframe import extract_nested_iframe_content
from PIL import Image, ImageTk
from py.config import load_config, save_config
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.scrolledtext import ScrolledText

class LicenseDialog:
    """免责声明弹窗"""
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
    def show(self):
        """显示免责声明弹窗"""
        dialog = Toplevel(self.parent)
        dialog.title("免责声明")
        dialog.geometry("1000x700")  # 增加宽度以便二等分
        dialog.resizable(False, False)
        dialog.configure(bg='#f8f9fa')

        # 设置窗口图标
        try:
            self.root.iconbitmap("icon/icon.ico")
        except:
            pass

        # 使弹窗始终在最前面
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.focus_force()
        
        # 居中显示
        self.center_window(dialog, 1000, 700)
        
        # 主容器
        main_frame = tk.Frame(dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 标题
        title_frame = tk.Frame(main_frame, bg='#4361ee', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="使用前请阅读",
            font=('Microsoft YaHei', 18, 'bold'),
            bg='#4361ee',
            fg='white'
        ).pack(expand=True)
        
        # 内容区域
        content_frame = tk.Frame(main_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 使用PanedWindow实现可调节的左右二等分
        paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, sashwidth=2, sashrelief='raised')
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧免责声明区域
        left_pane = tk.Frame(paned, bg='white')
        right_pane = tk.Frame(paned, bg='white')
        
        # 设置左右等宽
        paned.add(left_pane, width=500)
        paned.add(right_pane, width=500)
        
        # 左侧：免责声明文本
        tk.Label(
            left_pane,
            text="免责声明与用户协议",
            font=('Microsoft YaHei', 16, 'bold'),
            bg='white',
            fg='#333333',
            anchor='w',
            padx=20,
            pady=20
        ).pack(fill=tk.X)
        
        # 创建滚动文本框
        text_frame = tk.Frame(left_pane, bg='white', padx=20)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 免责声明文本
        license_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 10),
            bg='#f8f9fa',
            fg='#333333',
            padx=10,
            pady=10,
            height=12,
            yscrollcommand=scrollbar.set
        )
        license_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=license_text.yview)
        
        # 免责声明内容
        disclaimer_content = """重要提示：在使用本软件前，请仔细阅读以下条款。使用本软件即表示您同意遵守以下所有条款。

一、软件性质
1. 本软件为开源工具，采用MIT许可证，仅供学习和研究使用。
2. 本软件不得用于商业用途或任何违法活动。
3. 仓库链接：

二、用户责任
1. 用户应确保其行为符合相关法律法规。
2. 用户应对使用本软件产生的后果承担全部责任。
3. 禁止将本软件用于侵权、破解或其他非法目的。
4. 提取后的软件请勿用于商业用途。

三、知识产权
1. 本软件尊重并保护所有版权和知识产权。
2. 用户应确保所处理的内容拥有合法使用权。
3. 如涉及第三方内容，请遵守相应的使用条款。

四、免责条款
1. 开发者对使用本软件产生的任何损失不承担责任。
2. 软件按"现状"提供，不提供任何形式的担保。
3. 开发者保留随时修改和更新软件的权利。

五、使用限制
1. 不得对本软件进行反向工程、反编译或修改。
2. 不得将本软件用于任何破坏性目的。
3. 不得利用本软件进行恶意行为。

六、风险提示
1. 网络操作存在风险，请谨慎处理敏感信息。
2. 建议在使用前备份重要数据。
3. 如遇问题，请通过官方渠道反馈。

七、隐私保护
1. 本软件不会收集用户个人信息。
2. 所有处理均在本地完成，不涉及网络传输。
3. 请妥善保管生成的文件。

八、其他
1. 本协议最终解释权归开发者所有。
2. 开发者有权随时更新本协议内容。
3. 如不同意本协议，请立即停止使用。
4.请详细阅读并同意以下协议：
    -《文幻工作室隐私政策》https://atrbfac.top/Privacy_policy/
    -《文幻工作室用户协议》https://atrbfac.top/User_agreement/

我已阅读、理解并同意上述所有条款。"""
        
        license_text.insert('1.0', disclaimer_content)
        license_text.config(state='disabled')
        
        # 同意选项
        self.agree_var = tk.BooleanVar(value=False)
        
        agree_check = tk.Checkbutton(
            left_pane,
            text="我已阅读、理解并同意上述所有条款",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='white',
            fg='#333333',
            variable=self.agree_var,
            selectcolor='white',
            activebackground='white',
            activeforeground='#333333',
            command=lambda: self.update_button_state(dialog)
        )
        agree_check.pack(fill=tk.X, padx=20, pady=20)
        
        # 右侧：赞赏二维码
        tk.Label(
            right_pane,
            text="支持我们",
            font=('Microsoft YaHei', 16, 'bold'),
            bg='white',
            fg='#333333',
            anchor='center',
            pady=20
        ).pack()
        
        tk.Label(
            right_pane,
            text="如果本软件对您有帮助，\n可以扫码支持开发者",
            font=('Microsoft YaHei', 10),
            bg='white',
            fg='#666666',
            justify='center'
        ).pack(pady=(0, 20))
        
        # 二维码图片容器
        qr_container = tk.Frame(right_pane, bg='white')
        qr_container.pack(expand=True)
        
        qr_frame = tk.Frame(qr_container, bg='#f0f0f0', width=300, height=300)
        qr_frame.pack_propagate(False)
        qr_frame.pack()
        
        try:
            # 尝试加载本地二维码图片
            qr_image = Image.open("images/qrcode.png")
            qr_image = qr_image.resize((280, 280), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_image)
            
            qr_label = tk.Label(
                qr_frame,
                image=qr_photo,
                bg='#f0f0f0'
            )
            qr_label.image = qr_photo
            qr_label.pack(expand=True)
        except:
            # 如果图片不存在，显示占位符
            tk.Label(
                qr_frame,
                text="二维码加载失败……",
                font=('Microsoft YaHei', 10),
                bg='#f0f0f0',
                fg='#666666',
                justify='center',
                wraplength=280
            ).pack(expand=True)
        
        # 提示文本
        tk.Label(
            right_pane,
            text="您的支持是我们持续更新的动力！",
            font=('Microsoft YaHei', 9, 'italic'),
            bg='white',
            fg='#888888',
            pady=20
        ).pack()
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg='white', pady=20)
        button_frame.pack(fill=tk.X)
        
        # 退出按钮
        exit_btn = tk.Button(
            button_frame,
            text="不同意并退出",
            font=('Microsoft YaHei', 10),
            bg='#6c757d',
            fg='white',
            activebackground='#5a6268',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=15,
            command=self.parent.quit
        )
        exit_btn.pack(side=tk.LEFT, padx=(20, 10))
        
        # 同意按钮 - 蓝色主题
        self.agree_btn = tk.Button(
            button_frame,
            text="同意并继续",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#4361ee',  # 蓝色
            fg='white',
            activebackground='#3a56d4',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=15,
            state='disabled',
            command=lambda: self.on_agree(dialog)
        )
        self.agree_btn.pack(side=tk.RIGHT, padx=(10, 20))
        
        # 等待对话框关闭
        dialog.wait_window()
        
    def update_button_state(self, dialog):
        """更新按钮状态"""
        if self.agree_var.get():
            self.agree_btn.config(state='normal', bg='#4361ee', activebackground='#3a56d4')
        else:
            self.agree_btn.config(state='disabled', bg='#4361ee', activebackground='#3a56d4')
    
    def on_agree(self, dialog):
        """同意按钮点击事件"""
        if self.agree_var.get():
            dialog.destroy()
            return True
        return False
    
    def center_window(self, window, width, height):
        """居中显示窗口"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f'{width}x{height}+{x}+{y}')


class ProgressDialog:
    """进度条弹窗"""
    def __init__(self, parent, total_wait_time):
        self.parent = parent
        self.total_wait_time = total_wait_time
        self.dialog = None
        self.progress_bar = None
        self.status_label = None
        self.progress_percent_label = None
        self.current_progress = 0
        self.is_extracting = False
        
    def show(self):
        """显示进度条弹窗"""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("提取进度")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg='white')
        
        # 使弹窗始终在最前面
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.center_window(self.dialog, 500, 300)
        
        # 标题
        tk.Label(
            self.dialog,
            text="正在提取内容...",
            font=('Microsoft YaHei', 16, 'bold'),
            bg='white',
            fg='#333333',
            pady=20
        ).pack()
        
        # 进度百分比标签
        self.progress_percent_label = tk.Label(
            self.dialog,
            text="0%",
            font=('Microsoft YaHei', 24, 'bold'),
            bg='white',
            fg='#4361ee'
        )
        self.progress_percent_label.pack(pady=10)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=20, padx=50)
        
        # 状态标签
        self.status_label = tk.Label(
            self.dialog,
            text="正在解析链接...",
            font=('Microsoft YaHei', 10),
            bg='white',
            fg='#666666'
        )
        self.status_label.pack(pady=10)
        
        # 禁用关闭按钮
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def update_progress(self, value, text=None):
        """更新进度条"""
        if self.dialog and self.dialog.winfo_exists():
            self.current_progress = value
            self.progress_bar['value'] = value
            self.progress_percent_label.config(text=f"{int(value)}%")
            if text:
                self.status_label.config(text=text)
            self.dialog.update()
    
    def update_status(self, text):
        """更新状态文本"""
        if self.dialog and self.dialog.winfo_exists():
            self.status_label.config(text=text)
            self.dialog.update()
    
    def set_extracting_status(self, is_extracting):
        """设置提取状态"""
        self.is_extracting = is_extracting
        
    def close(self):
        """关闭进度条弹窗"""
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()
    
    def center_window(self, window, width, height):
        """居中显示窗口"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f'{width}x{height}+{x}+{y}')


class APKToolboxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("灵光APK工具箱")
        self.root.geometry("700x500")
        self.root.minsize(700, 500)
        self.style = ttk.Style(theme='flatly')
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon/icon.ico")
        except:
            pass
        
        # 颜色方案 - 将按钮颜色改为蓝色
        self.colors = {
            'primary': '#4361ee',  # 主蓝色
            'primary_light': '#e0e7ff',
            'secondary': '#6c757d',
            'success': '#4361ee',  # 原来是绿色，现在改为蓝色
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'border': '#dee2e6',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'accent': '#4361ee',
        }
        
        # 字体设置
        self.fonts = {
            'h1': ('Microsoft YaHei', 20, 'bold'),
            'h2': ('Microsoft YaHei', 16, 'bold'),
            'h3': ('Microsoft YaHei', 14, 'bold'),
            'body': ('Microsoft YaHei', 11),
            'small': ('Microsoft YaHei', 10),
            'mono': ('Consolas', 10)
        }
        
        # 加载配置
        self.config = load_config()
        
        # 初始化状态
        self.extraction_thread = None
        self.is_extracting = False
        self.extracted_path = None
        self.current_progress = 0
        self.progress_running = False
        self.extraction_completed = False
        self.extracted_content = None
        
        # 进度条弹窗实例
        self.progress_dialog = None
        
        # 先显示免责声明
        self.show_license_dialog()
        
        # 如果用户同意，创建主界面
        if not self.license_agreed:
            return
            
        # 创建UI
        self.create_ui()
        
        # 居中显示窗口
        self.center_window()
    
    def show_license_dialog(self):
        """显示免责声明对话框"""
        license_dialog = LicenseDialog(self.root)
        self.license_agreed = False
        
        # 显示对话框
        self.root.attributes('-topmost', True)  # 主窗口置顶
        license_dialog.show()
        
        # 恢复窗口状态
        self.root.attributes('-topmost', False)
        
        # 检查用户是否同意
        if hasattr(license_dialog, 'agree_var') and license_dialog.agree_var.get():
            self.license_agreed = True
        else:
            # 用户不同意，退出程序
            self.root.quit()
    
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_ui(self):
        """创建UI界面"""
        # 创建主容器
        main_container = tk.Frame(self.root, bg=self.colors['light'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 创建顶部导航栏
        self.create_navbar(main_container)
        
        # 创建主要内容区域
        self.create_main_content(main_container)
        
        # 创建底部状态栏
        self.create_status_bar(main_container)
    
    def create_navbar(self, parent):
        """创建顶部导航栏"""
        navbar = tk.Frame(parent, bg=self.colors['white'], height=60)
        navbar.pack(fill=tk.X, pady=(0, 20))
        navbar.pack_propagate(False)
        
        # 应用标题
        title_frame = tk.Frame(navbar, bg=self.colors['white'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        
        tk.Label(
            title_frame,
            text="灵光APK工具箱",
            font=self.fonts['h1'],
            bg=self.colors['white'],
            fg=self.colors['primary']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="自动化提取与打包工具",
            font=self.fonts['small'],
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 导航按钮 - 改为蓝色主题
        button_frame = tk.Frame(navbar, bg=self.colors['white'])
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20)
        
        # 设置按钮
        settings_btn = tk.Button(
            button_frame,
            text="设置",
            font=self.fonts['body'],
            bg=self.colors['white'],
            fg=self.colors['primary'],  # 蓝色
            activebackground=self.colors['light'],
            activeforeground=self.colors['primary'],  # 蓝色
            relief='flat',
            bd=1,
            cursor='hand2',
            command=self.show_settings
        )
        settings_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 关于按钮
        about_btn = tk.Button(
            button_frame,
            text="关于",
            font=self.fonts['body'],
            bg=self.colors['white'],
            fg=self.colors['primary'],  # 蓝色
            activebackground=self.colors['light'],
            activeforeground=self.colors['primary'],  # 蓝色
            relief='flat',
            bd=1,
            cursor='hand2',
            command=self.show_about
        )
        about_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    def create_main_content(self, parent):
        """创建主要内容区域"""
        # 主内容容器
        content_frame = tk.Frame(parent, bg=self.colors['light'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧输入面板
        left_panel = tk.Frame(content_frame, bg=self.colors['light'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 输入卡片
        input_card = tk.Frame(
            left_panel,
            bg=self.colors['white'],
            relief='solid',
            bd=1
        )
        input_card.pack(fill=tk.BOTH, expand=True)
        
        # 卡片标题
        card_title = tk.Frame(input_card, bg=self.colors['light'], height=40)
        card_title.pack(fill=tk.X)
        card_title.pack_propagate(False)
        
        tk.Label(
            card_title,
            text="输入分享链接",
            font=self.fonts['h3'],
            bg=self.colors['light'],
            fg=self.colors['dark'],
            padx=15
        ).pack(side=tk.LEFT)
        
        # 输入说明
        tk.Label(
            input_card,
            text="粘贴包含灵光分享链接的文本：",
            font=self.fonts['small'],
            bg=self.colors['white'],
            fg=self.colors['text_secondary'],
            anchor='w',
            padx=20,
            pady=5
        ).pack(fill=tk.X)
        
        # 输入文本框框架
        text_frame = tk.Frame(input_card, bg=self.colors['white'], padx=20, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动文本框
        self.input_text = ScrolledText(
            text_frame,
            height=8,
            font=self.fonts['body'],
            bg=self.colors['white'],
            fg=self.colors['text_primary'],
            relief='solid',
            bd=1,
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置占位符
        self.placeholder_text = "复制此口令打开灵光👉或直接点击快来看看我在灵光 App 一句话创建的闪应用：\"XXX\"https://www.lingguang.com/share/FLASH_APP-XXXX-XXXX…"
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors['text_secondary'])
        
        # 绑定事件
        self.input_text.bind('<FocusIn>', self.on_input_focus_in)
        self.input_text.bind('<FocusOut>', self.on_input_focus_out)
        
        # 按钮区域
        button_frame = tk.Frame(input_card, bg=self.colors['white'], pady=10)
        button_frame.pack(fill=tk.X, padx=20)
        
        # 示例按钮
        tk.Button(
            button_frame,
            text="点击查看使用说明",
            font=self.fonts['body'],
            bg=self.colors['light'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['border'],
            activeforeground=self.colors['text_secondary'],
            relief='flat',
            bd=1,
            cursor='hand2',
            command=self.show_example
        ).pack(side=tk.LEFT)
        
        # 提取按钮 - 改为蓝色主题
        self.extract_btn = tk.Button(
            button_frame,
            text="开始提取",
            font=self.fonts['body'],
            bg=self.colors['primary'],  # 蓝色
            fg='white',
            activebackground='#3a56d4',  # 深蓝色
            activeforeground='white',
            relief='flat',
            bd=1,
            cursor='hand2',
            command=self.start_extraction_from_button
        )
        self.extract_btn.pack(side=tk.RIGHT)
        
        # 右侧进度面板
        right_panel = tk.Frame(content_frame, bg=self.colors['light'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_panel.pack_propagate(False)
        
        # 进度卡片 - 保持原有布局，但不显示进度条
        progress_card = tk.Frame(
            right_panel,
            bg=self.colors['white'],
            relief='solid',
            bd=1
        )
        progress_card.pack(fill=tk.BOTH, expand=True)
        
        # 卡片标题
        progress_title = tk.Frame(progress_card, bg=self.colors['light'], height=40)
        progress_title.pack(fill=tk.X)
        progress_title.pack_propagate(False)
        
        tk.Label(
            progress_title,
            text="操作状态",
            font=self.fonts['h3'],
            bg=self.colors['light'],
            fg=self.colors['dark'],
            padx=15
        ).pack(side=tk.LEFT)
        
        # 状态显示区域
        status_content = tk.Frame(progress_card, bg=self.colors['white'], padx=20, pady=20)
        status_content.pack(fill=tk.BOTH, expand=True)
        
        # 状态图标
        self.status_icon_label = tk.Label(
            status_content,
            text="⏳",
            font=('Segoe UI', 48),
            bg=self.colors['white'],
            fg=self.colors['text_secondary']
        )
        self.status_icon_label.pack(pady=(20, 10))
        
        # 状态文本
        self.status_text_label = tk.Label(
            status_content,
            text="等待开始提取",
            font=('Microsoft YaHei', 12),
            bg=self.colors['white'],
            fg=self.colors['text_primary']
        )
        self.status_text_label.pack(pady=(0, 10))
        
        # 详细说明
        status_info_text = tk.Text(
            status_content,
            height=6,
            font=('Microsoft YaHei', 10),
            bg=self.colors['light'],
            fg=self.colors['text_secondary'],
            wrap=tk.WORD,
            relief='flat',
            padx=10,
            pady=10
        )
        status_info_text.pack(fill=tk.BOTH, expand=True)
        
        info_content = f"""提取过程将显示在独立的进度窗口中。

设置信息：
• 页面等待时间：{self.config['wait_time']}秒
• 进度条将按照设定时间逐步推进
• 如果提前完成，进度条会直接跳到100%

点击"开始提取"按钮开始处理。"""
        
        status_info_text.insert('1.0', info_content)
        status_info_text.config(state='disabled')
    
    def create_status_bar(self, parent):
        """创建底部状态栏"""
        status_bar = tk.Frame(parent, bg=self.colors['dark'], height=30)
        status_bar.pack(fill=tk.X, pady=(20, 0))
        status_bar.pack_propagate(False)
        
        # 状态信息
        self.global_status = tk.Label(
            status_bar,
            text="就绪：粘贴包含链接的文本，然后点击开始提取",
            font=self.fonts['small'],
            bg=self.colors['dark'],
            fg='white',
            padx=10
        )
        self.global_status.pack(side=tk.LEFT, fill=tk.Y)
        
        # 版权信息
        tk.Label(
            status_bar,
            text="© 2026 文幻工作室 | 灵光APK工具箱 v1.0",
            font=self.fonts['small'],
            bg=self.colors['dark'],
            fg='white',
            padx=10
        ).pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_input_focus_in(self, event):
        """输入框获得焦点"""
        if self.input_text.get("1.0", "end-1c") == self.placeholder_text:
            self.input_text.delete("1.0", "end")
            self.input_text.config(fg=self.colors['text_primary'])
    
    def on_input_focus_out(self, event):
        """输入框失去焦点"""
        if not self.input_text.get("1.0", "end-1c").strip():
            self.input_text.insert("1.0", self.placeholder_text)
            self.input_text.config(fg=self.colors['text_secondary'])
    
    def show_example(self):
        """使用说明"""
        example_text = """使用说明：
1.点击应用右上角的"···"三点按钮，选择分享选项，点击复制链接
2.使用CTRL＋V快捷键，将链接粘贴进输入框中，点击开始提取按钮，系统自动进行识别提取
3.如遇到应用内部分功能无法使用，请先在浏览器内预览测试一下（部分功能依赖灵光的API，会导致功能异常，可以尝试对灵光AI说：“把所有依赖lingguangAPI的接口全部换成原生API”）
4.如果使用过程中多次遇到问题，请联系开发者处理（附带错误截图与操作步骤，以及灵光闪应用链接等）
        
"""
        
        messagebox.showinfo("使用说明", example_text)
    
    def start_extraction_from_button(self):
        """从按钮开始提取"""
        content = self.input_text.get("1.0", "end-1c").strip()
        
        # 检查是否是占位符文本
        if content == self.placeholder_text or not content:
            messagebox.showwarning("提示", "请输入包含网址的内容！")
            return
        
        # 提取网址
        urls = self.extract_urls(content)
        if not urls:
            messagebox.showwarning("提示", "未在输入内容中找到有效的网址！")
            return
        
        # 取第一个网址
        url = urls[0]
        self.start_extraction(url)
    
    def extract_urls(self, text):
        """从文本中提取URL"""
        url_pattern = r'https?://[^\s\'"<>]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    def start_extraction(self, url):
        """开始提取过程"""
        if self.is_extracting:
            return
        
        self.is_extracting = True
        self.current_progress = 0
        self.extraction_completed = False
        
        # 禁用输入框和按钮
        self.input_text.configure(state='disabled')
        self.extract_btn.configure(state='disabled')
        self.global_status.configure(text="正在提取内容...")
        self.status_icon_label.config(text="⏳", fg=self.colors['warning'])
        self.status_text_label.config(text="提取中...", fg=self.colors['warning'])
        
        # 显示进度条弹窗
        self.progress_dialog = ProgressDialog(self.root, self.config['wait_time'])
        self.progress_dialog.show()
        
        # 启动提取线程
        self.extraction_thread = threading.Thread(target=self.run_extraction, args=(url,))
        self.extraction_thread.daemon = True
        self.extraction_thread.start()
        
        # 启动进度更新线程
        self.progress_thread = threading.Thread(target=self.update_extraction_progress)
        self.progress_thread.daemon = True
        self.progress_thread.start()
    
    def update_extraction_progress(self):
        """更新提取进度"""
        wait_time = self.config['wait_time']
        
        # 步骤1: 解析链接 (0-20%)
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("正在解析链接..."))
        
        step_time = wait_time * 0.2
        for i in range(0, 21):
            if not self.progress_running or self.extraction_completed:
                break
            if self.progress_dialog:
                self.root.after(0, lambda v=i: self.progress_dialog.update_progress(v))
            time.sleep(step_time / 15)
        
        if self.extraction_completed:
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.update_progress(100, "处理完成"))
            time.sleep(0.5)
            return
        
        # 步骤2: 获取内容 (20-50%)
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("正在获取网页内容..."))
        
        step_time = wait_time * 0.3
        for i in range(21, 51):
            if not self.progress_running or self.extraction_completed:
                break
            if self.progress_dialog:
                self.root.after(0, lambda v=i: self.progress_dialog.update_progress(v))
            time.sleep(step_time / 20)
        
        if self.extraction_completed:
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.update_progress(100, "处理完成"))
            time.sleep(0.5)
            return
        
        # 步骤3: 处理数据 (50-80%)
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("正在处理数据..."))
        
        step_time = wait_time * 0.3
        for i in range(51, 81):
            if not self.progress_running or self.extraction_completed:
                break
            if self.progress_dialog:
                self.root.after(0, lambda v=i: self.progress_dialog.update_progress(v))
            time.sleep(step_time / 20)
        
        if self.extraction_completed:
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.update_progress(100, "处理完成"))
            time.sleep(0.5)
            return
        
        # 步骤4: 生成结果 (80-95%)
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("正在生成结果..."))
        
        step_time = wait_time * 0.3
        for i in range(81, 96):
            if not self.progress_running or self.extraction_completed:
                break
            if self.progress_dialog:
                self.root.after(0, lambda v=i: self.progress_dialog.update_progress(v))
            time.sleep(step_time / 10)
        
        if self.extraction_completed:
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.update_progress(100, "处理完成"))
            time.sleep(0.5)
            return
        
        # 减速阶段: 95-99%
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("即将完成..."))
        
        step_time = wait_time * 0.15
        for i in range(96, 100):
            if not self.progress_running or self.extraction_completed:
                break
            if self.progress_dialog:
                self.root.after(0, lambda v=i: self.progress_dialog.update_progress(v))
            time.sleep(step_time / 2)  # 更慢的速度
        
        # 等待提取完成
        if self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_status("正在完成最后处理..."))
        
        # 卡在99%直到提取完成
        start_wait_time = time.time()
        while not self.extraction_completed and self.progress_running:
            elapsed = time.time() - start_wait_time
            if elapsed > wait_time * 0.5:  # 最多等待一半的等待时间
                break
            time.sleep(0.1)
        
        # 如果提取完成，跳到100%
        if self.extraction_completed and self.progress_running:
            if self.progress_dialog:
                self.root.after(0, lambda: self.progress_dialog.update_progress(100, "处理完成"))
            time.sleep(0.5)
    
    def run_extraction(self, url):
        """运行提取过程"""
        try:
            self.progress_running = True
            
            # 开始提取
            content = extract_nested_iframe_content(url)
            
            if content is not None:
                # 保存提取的内容到实例变量
                self.extracted_content = content
                self.extraction_completed = True
                time.sleep(0.5)  # 给动画一点完成时间
                self.root.after(0, self.on_extraction_complete_with_content)
            else:
                self.progress_running = False
                self.extraction_completed = True
                self.root.after(0, self.on_extraction_error, "提取失败，无法获取内容")
                
        except Exception as e:
            self.progress_running = False
            self.extraction_completed = True
            self.root.after(0, self.on_extraction_error, str(e))
    
    def on_extraction_complete_with_content(self):
        """提取完成并获取到内容后的回调"""
        # 关闭进度条弹窗
        if self.progress_dialog:
            self.root.after(0, self.progress_dialog.close)
        
        # 更新主界面状态
        self.status_icon_label.config(text="✓", fg=self.colors['success'])
        self.status_text_label.config(text="提取完成", fg=self.colors['success'])
        
        # 弹出文件保存对话框
        file_path = filedialog.asksaveasfilename(
            title="保存提取的HTML文件",
            defaultextension=".html",
            filetypes=[("HTML文件", "*.html"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            self.reset_extraction_ui()
            return
        
        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.extracted_content)
            
            self.extracted_path = os.path.abspath(file_path)
            self.show_result_dialog()
            
        except Exception as e:
            self.root.after(0, self.on_extraction_error, f"保存文件时出错: {str(e)}")
    
    def reset_extraction_ui(self):
        """重置提取UI状态"""
        # 启用输入框和按钮
        self.input_text.configure(state='normal')
        self.extract_btn.configure(state='normal')
        
        # 重置状态标签
        self.status_icon_label.config(text="⏳", fg=self.colors['text_secondary'])
        self.status_text_label.config(text="等待开始提取", fg=self.colors['text_primary'])
        self.global_status.configure(text="就绪：粘贴包含链接的文本，然后点击开始提取")
        
        # 清空输入框
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors['text_secondary'])
        
        self.is_extracting = False
        self.progress_running = False
        self.extraction_completed = False
    
    def on_extraction_error(self, error_msg):
        """提取错误"""
        # 关闭进度条弹窗
        if self.progress_dialog:
            self.root.after(0, self.progress_dialog.close)
        
        # 更新主界面状态
        self.status_icon_label.config(text="❌", fg=self.colors['danger'])
        self.status_text_label.config(text="提取失败", fg=self.colors['danger'])
        
        # 更新UI
        self.extract_btn.configure(state='normal')
        self.input_text.configure(state='normal')
        self.global_status.configure(text="提取失败")
        
        # 显示错误消息
        error_dialog = Toplevel(self.root)
        error_dialog.title("提取失败")
        error_dialog.geometry("400x200")
        error_dialog.configure(bg='white')
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # 居中显示
        window_width = 400
        window_height = 200
        screen_width = error_dialog.winfo_screenwidth()
        screen_height = error_dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        error_dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 错误信息
        tk.Label(
            error_dialog,
            text="错误",
            font=('Segoe UI', 20, 'bold'),
            bg='white',
            fg=self.colors['danger']
        ).pack(pady=20)
        
        # 错误信息
        tk.Label(
            error_dialog,
            text="提取过程中发生错误",
            font=('Segoe UI', 12, 'bold'),
            bg='white',
            fg=self.colors['dark']
        ).pack(pady=(0, 5))
        
        tk.Label(
            error_dialog,
            text=error_msg[:100] + "..." if len(error_msg) > 100 else error_msg,
            font=('Segoe UI', 9),
            bg='white',
            fg=self.colors['text_secondary'],
            wraplength=350
        ).pack(pady=(0, 20))
        
        # 确定按钮 - 改为蓝色主题
        tk.Button(
            error_dialog,
            text="确定",
            font=('Microsoft YaHei', 10),
            bg=self.colors['primary'],  # 蓝色
            fg='white',
            activebackground='#3a56d4',  # 深蓝色
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            command=error_dialog.destroy
        ).pack()
        
        self.is_extracting = False
    
    def show_result_dialog(self):
        """显示结果弹窗"""
        result_dialog = Toplevel(self.root)
        result_dialog.title("提取完成")
        result_dialog.geometry("500x500")
        result_dialog.configure(bg='white')
        result_dialog.resizable(False, False)

        # 设置窗口图标
        try:
            self.root.iconbitmap("icon/icon.ico")
        except:
            pass

        # 居中显示
        window_width = 500
        window_height = 500
        screen_width = result_dialog.winfo_screenwidth()
        screen_height = result_dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        result_dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        result_dialog.transient(self.root)
        result_dialog.grab_set()
        
        # 对话框内容
        container = tk.Frame(result_dialog, bg='white', padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 成功图标
        tk.Label(
            container,
            text="✓",
            font=('Segoe UI', 50),
            bg='white',
            fg=self.colors['success']  # 已经是蓝色
        ).pack(pady=(0, 20))
        
        # 成功标题
        tk.Label(
            container,
            text="提取成功！",
            font=('Segoe UI', 20, 'bold'),
            bg='white',
            fg=self.colors['success']  # 已经是蓝色
        ).pack(pady=(0, 10))
        
        # 描述文本
        tk.Label(
            container,
            text="内容已成功提取并保存为HTML文件",
            font=('Segoe UI', 11),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack(pady=(0, 20))
        
        # 文件路径卡片
        path_card = tk.Frame(
            container,
            bg=self.colors['light'],
            relief='solid',
            bd=1
        )
        path_card.pack(fill=tk.X, pady=(0, 30))
        
        # 卡片标题
        tk.Label(
            path_card,
            text="保存路径",
            font=('Microsoft YaHei', 10, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark'],
            padx=10,
            pady=5
        ).pack(anchor='w')
        
        # 路径文本
        path_text = tk.Text(
            path_card,
            height=3,
            font=self.fonts['mono'],
            bg='white',
            fg=self.colors['text_primary'],
            wrap=tk.WORD,
            relief='flat',
            padx=10,
            pady=5
        )
        path_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        path_text.insert('1.0', self.extracted_path)
        path_text.configure(state='disabled')
        
        # 按钮容器
        button_frame = tk.Frame(container, bg='white')
        button_frame.pack(fill=tk.X)
        
        # 查看文件按钮 - 改为蓝色主题
        tk.Button(
            button_frame,
            text="查看文件",
            font=('Microsoft YaHei', 10),
            bg=self.colors['white'],
            fg=self.colors['primary'],  # 蓝色
            activebackground=self.colors['light'],
            activeforeground=self.colors['primary'],  # 蓝色
            relief='flat',
            bd=1,
            cursor='hand2',
            command=self.open_file
        ).pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        # 打包APK按钮 - 改为蓝色主题
        tk.Button(
            button_frame,
            text="打包成APK",
            font=('Microsoft YaHei', 10, 'bold'),
            bg=self.colors['primary'],  # 蓝色
            fg='white',
            activebackground='#3a56d4',  # 深蓝色
            activeforeground='white',
            relief='flat',
            bd=1,
            cursor='hand2',
            command=lambda: self.generate_apk_with_info(result_dialog)
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 完成按钮 - 改为蓝色主题
        tk.Button(
            button_frame,
            text="完成",
            font=('Microsoft YaHei', 10),
            bg=self.colors['primary'],  # 蓝色
            fg='white',
            activebackground='#3a56d4',  # 深蓝色
            activeforeground='white',
            relief='flat',
            bd=1,
            cursor='hand2',
            command=result_dialog.destroy
        ).pack(side=tk.LEFT, padx=(10, 0), expand=True, fill=tk.X)
        
        # 重置UI
        self.reset_extraction_ui()
    
    def generate_apk_with_info(self, parent_dialog):
        """使用收集的信息生成APK"""
        if not self.extracted_path or not os.path.exists(self.extracted_path):
            messagebox.showerror("错误", "未找到提取的HTML文件！")
            return
        
        parent_dialog.destroy()
        
        try:
            from py.Generate_apk import APKGenerator
            generator = APKGenerator()
            generator.show_apk_info_dialog(self.extracted_path)
        except Exception as e:
            messagebox.showerror("错误", f"执行Generate_apk.py失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def open_file(self):
        """打开提取的文件"""
        if self.extracted_path and os.path.exists(self.extracted_path):
            webbrowser.open(f"file://{self.extracted_path}")
        else:
            messagebox.showerror("错误", "提取的文件不存在！")
    
    def show_about(self):
        """显示关于弹窗"""
        about_dialog = Toplevel(self.root)
        about_dialog.title("关于")
        about_dialog.geometry("500x600")
        about_dialog.configure(bg='white')
        about_dialog.resizable(False, False)

        # 设置窗口图标
        try:
            self.root.iconbitmap("icon/icon.ico")
        except:
            pass

        # 居中显示
        window_width = 500
        window_height = 600
        screen_width = about_dialog.winfo_screenwidth()
        screen_height = about_dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        about_dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # 对话框内容
        container = tk.Frame(about_dialog, bg='white', padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Logo区域
        logo_frame = tk.Frame(container, bg='white')
        logo_frame.pack(pady=(0, 20))
        
        # Logo
        try:
            image = Image.open("images/icon.png")
            image = image.resize((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            logo_label = tk.Label(logo_frame, image=photo, bg='white')
            logo_label.image = photo
            logo_label.pack()
        except:
            tk.Label(
                logo_frame,
                text="灵光APK工具箱",
                font=('Microsoft YaHei', 12, 'bold'),
                bg='white',
                fg=self.colors['primary']
            ).pack()
        
        # 应用名称
        tk.Label(
            container,
            text="灵光APK工具箱",
            font=('Segoe UI', 24, 'bold'),
            bg='white',
            fg=self.colors['primary']
        ).pack(pady=(0, 5))
        
        # 版本
        tk.Label(
            container,
            text="版本 1.0.0",
            font=('Segoe UI', 10),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack(pady=(0, 30))
        
        # 描述卡片
        desc_card = tk.Frame(
            container,
            bg=self.colors['light'],
            relief='solid',
            bd=1
        )
        desc_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            desc_card,
            text="应用描述",
            font=('Microsoft YaHei', 10, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark'],
            padx=10,
            pady=5
        ).pack(anchor='w')
        
        tk.Label(
            desc_card,
            text="一款自动提取灵光闪应用网页内容并转换为APK应用的工具，简化您的开发流程。",
            font=('Segoe UI', 10),
            bg='white',
            fg=self.colors['text_secondary'],
            wraplength=400,
            justify='center',
            padx=10,
            pady=10
        ).pack()
        
        # 信息卡片
        info_card = tk.Frame(
            container,
            bg=self.colors['light'],
            relief='solid',
            bd=1
        )
        info_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            info_card,
            text="开发信息",
            font=('Microsoft YaHei', 10, 'bold'),
            bg=self.colors['light'],
            fg=self.colors['dark'],
            padx=10,
            pady=5
        ).pack(anchor='w')
        
        info_items = [
            ("开发团队", "文幻工作室"),
            ("联系方式", "atrbfac@163.com"),
            ("QQ交流群", "981642484"),
            ("官方网站", "https://atrbfac.top")
        ]
        
        for title, content in info_items:
            item_frame = tk.Frame(info_card, bg='white')
            item_frame.pack(fill=tk.X, pady=3, padx=10)
            
            tk.Label(
                item_frame,
                text=title,
                font=('Microsoft YaHei', 10, 'bold'),
                bg='white',
                fg=self.colors['dark'],
                width=12,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            tk.Label(
                item_frame,
                text=content,
                font=('Microsoft YaHei', 10),
                bg='white',
                fg=self.colors['text_secondary']
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 版权信息
        tk.Label(
            container,
            text="© 2026 文幻工作室 版权所有",
            font=('Segoe UI', 9),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack()
    
    def show_settings(self):
        """显示设置窗口"""
        cfg = load_config()
        
        settings_dialog = Toplevel(self.root)
        settings_dialog.title("设置")
        settings_dialog.geometry("450x450")
        settings_dialog.configure(bg='white')
        settings_dialog.resizable(False, False)

        # 设置窗口图标
        try:
            self.root.iconbitmap("icon/icon.ico")
        except:
            pass

        # 居中显示
        window_width = 450
        window_height = 450
        screen_width = settings_dialog.winfo_screenwidth()
        screen_height = settings_dialog.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        settings_dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # 对话框内容
        container = tk.Frame(settings_dialog, bg='white', padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        tk.Label(
            container,
            text="设置",
            font=('Segoe UI', 18, 'bold'),
            bg='white',
            fg=self.colors['primary']
        ).pack(pady=(0, 20))
        
        # 设置项框架
        settings_frame = tk.Frame(container, bg='white')
        settings_frame.pack(fill=tk.X, pady=(0, 30))
        
        # 页面加载时间设置
        tk.Label(
            settings_frame,
            text="页面等待加载时间（秒）：",
            font=('Microsoft YaHei', 11),
            bg='white',
            fg=self.colors['dark']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 当前值显示
        value_frame = tk.Frame(settings_frame, bg='white')
        value_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            value_frame,
            text="当前值：",
            font=('Microsoft YaHei', 10),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT)
        
        value_label = tk.Label(
            value_frame,
            text=f"{cfg['wait_time']} 秒",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='white',
            fg=self.colors['primary']
        )
        value_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 滑块
        time_var = tk.IntVar(value=cfg["wait_time"])
        
        def update_value(val):
            value_label.configure(text=f"{int(float(val))} 秒")
        
        time_slider = tk.Scale(
            settings_frame,
            from_=10,
            to=80,
            orient=tk.HORIZONTAL,
            variable=time_var,
            command=update_value,
            bg='white',
            fg=self.colors['dark'],
            highlightbackground=self.colors['white']
        )
        time_slider.pack(fill=tk.X, pady=(0, 10))
        
        # 范围标签
        range_frame = tk.Frame(settings_frame, bg='white')
        range_frame.pack(fill=tk.X)
        
        tk.Label(
            range_frame,
            text="20秒",
            font=('Microsoft YaHei', 9),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            range_frame,
            text="80秒",
            font=('Microsoft YaHei', 9),
            bg='white',
            fg=self.colors['text_secondary']
        ).pack(side=tk.RIGHT)
        
        # 描述文本
        tk.Label(
            container,
            text="注意：较短的等待时间可能导致内容加载不完整，较长的等待时间会降低处理速度。",
            font=('Microsoft YaHei', 9),
            bg='white',
            fg=self.colors['text_secondary'],
            wraplength=350,
            justify='center'
        ).pack(pady=(0, 20))
        
        # 按钮框架
        button_frame = tk.Frame(container, bg='white')
        button_frame.pack(fill=tk.X)
        
        def save_settings():
            cfg["wait_time"] = time_var.get()
            save_config(cfg)
            self.config = cfg
            settings_dialog.destroy()
            messagebox.showinfo("设置已保存", "页面等待时间设置已保存。")
        
        tk.Button(
            button_frame,
            text="取消",
            font=('Microsoft YaHei', 10),
            bg=self.colors['light'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['border'],
            activeforeground=self.colors['text_secondary'],
            relief='flat',
            cursor='hand2',
            command=settings_dialog.destroy
        ).pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        tk.Button(
            button_frame,
            text="保存设置",
            font=('Microsoft YaHei', 10, 'bold'),
            bg=self.colors['primary'],  # 蓝色
            fg='white',
            activebackground='#3a56d4',  # 深蓝色
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            command=save_settings
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X)


def main():
    root = tk.Tk()
    app = APKToolboxGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
