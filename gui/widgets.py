"""
自定义GUI控件模块
包含FFmpeg GUI工具的自定义控件
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Callable, Optional, Any


class FileSelectFrame(ttk.Frame):
    """文件选择控件"""
    
    def __init__(self, parent, label_text: str, file_types: list = None, 
                 initial_dir: str = None, callback: Callable = None):
        """
        初始化文件选择控件
        
        Args:
            parent: 父控件
            label_text: 标签文本
            file_types: 文件类型过滤器
            initial_dir: 初始目录
            callback: 文件选择回调函数
        """
        super().__init__(parent)
        
        self.file_types = file_types or [("所有文件", "*.*")]
        self.initial_dir = initial_dir
        self.callback = callback
        self.selected_file = tk.StringVar()
        
        self._create_widgets(label_text)
    
    def _create_widgets(self, label_text: str):
        """创建控件"""
        # 标签
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # 文件路径输入框
        self.path_entry = ttk.Entry(self, textvariable=self.selected_file, width=50)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        # 浏览按钮
        self.browse_button = ttk.Button(self, text="浏览", command=self._browse_file)
        self.browse_button.grid(row=0, column=2)
        
        # 配置列权重
        self.columnconfigure(1, weight=1)
    
    def _browse_file(self):
        """浏览文件"""
        initial_dir = self.initial_dir or os.path.expanduser("~")
        
        filename = filedialog.askopenfilename(
            title="选择文件",
            filetypes=self.file_types,
            initialdir=initial_dir
        )
        
        if filename:
            self.selected_file.set(filename)
            if self.callback:
                self.callback(filename)
    
    def get_file_path(self) -> str:
        """获取选择的文件路径"""
        return self.selected_file.get()
    
    def set_file_path(self, path: str):
        """设置文件路径"""
        self.selected_file.set(path)


class DirectorySelectFrame(ttk.Frame):
    """目录选择控件"""
    
    def __init__(self, parent, label_text: str, initial_dir: str = None, 
                 callback: Callable = None):
        """
        初始化目录选择控件
        
        Args:
            parent: 父控件
            label_text: 标签文本
            initial_dir: 初始目录
            callback: 目录选择回调函数
        """
        super().__init__(parent)
        
        self.initial_dir = initial_dir
        self.callback = callback
        self.selected_dir = tk.StringVar()
        
        self._create_widgets(label_text)
    
    def _create_widgets(self, label_text: str):
        """创建控件"""
        # 标签
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # 目录路径输入框
        self.path_entry = ttk.Entry(self, textvariable=self.selected_dir, width=50)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        # 浏览按钮
        self.browse_button = ttk.Button(self, text="浏览", command=self._browse_directory)
        self.browse_button.grid(row=0, column=2)
        
        # 配置列权重
        self.columnconfigure(1, weight=1)
    
    def _browse_directory(self):
        """浏览目录"""
        initial_dir = self.initial_dir or os.path.expanduser("~")
        
        directory = filedialog.askdirectory(
            title="选择目录",
            initialdir=initial_dir
        )
        
        if directory:
            self.selected_dir.set(directory)
            if self.callback:
                self.callback(directory)
    
    def get_directory_path(self) -> str:
        """获取选择的目录路径"""
        return self.selected_dir.get()
    
    def set_directory_path(self, path: str):
        """设置目录路径"""
        self.selected_dir.set(path)


class TimeInputFrame(ttk.Frame):
    """时间输入控件"""
    
    def __init__(self, parent, label_text: str, default_time: str = "00:00:00"):
        """
        初始化时间输入控件
        
        Args:
            parent: 父控件
            label_text: 标签文本
            default_time: 默认时间
        """
        super().__init__(parent)
        
        self.time_vars = {
            'hours': tk.StringVar(value=default_time.split(':')[0]),
            'minutes': tk.StringVar(value=default_time.split(':')[1]),
            'seconds': tk.StringVar(value=default_time.split(':')[2])
        }
        
        self._create_widgets(label_text)
        self._setup_validation()
    
    def _create_widgets(self, label_text: str):
        """创建控件"""
        # 标签
        self.label = ttk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # 小时输入
        self.hour_entry = ttk.Entry(self, textvariable=self.time_vars['hours'], width=3)
        self.hour_entry.grid(row=0, column=1)
        
        # 冒号1
        ttk.Label(self, text=":").grid(row=0, column=2)
        
        # 分钟输入
        self.minute_entry = ttk.Entry(self, textvariable=self.time_vars['minutes'], width=3)
        self.minute_entry.grid(row=0, column=3)
        
        # 冒号2
        ttk.Label(self, text=":").grid(row=0, column=4)
        
        # 秒输入
        self.second_entry = ttk.Entry(self, textvariable=self.time_vars['seconds'], width=3)
        self.second_entry.grid(row=0, column=5)
        
        # 格式提示
        ttk.Label(self, text="(HH:MM:SS)", foreground="gray").grid(row=0, column=6, padx=(5, 0))
    
    def _setup_validation(self):
        """设置输入验证"""
        # 注册验证函数
        vcmd = (self.register(self._validate_time_input), '%P', '%W')
        
        self.hour_entry.config(validate='key', validatecommand=vcmd)
        self.minute_entry.config(validate='key', validatecommand=vcmd)
        self.second_entry.config(validate='key', validatecommand=vcmd)
    
    def _validate_time_input(self, value: str, widget_name: str) -> bool:
        """
        验证时间输入
        
        Args:
            value: 输入值
            widget_name: 控件名称
            
        Returns:
            是否有效
        """
        if not value:
            return True
        
        try:
            num = int(value)
            # 小时可以是任意正整数，分钟和秒需要小于60
            if 'hour' in widget_name:
                return num >= 0 and len(value) <= 2
            else:
                return 0 <= num < 60 and len(value) <= 2
        except ValueError:
            return False
    
    def get_time_string(self) -> str:
        """获取时间字符串"""
        hours = self.time_vars['hours'].get().zfill(2)
        minutes = self.time_vars['minutes'].get().zfill(2)
        seconds = self.time_vars['seconds'].get().zfill(2)
        return f"{hours}:{minutes}:{seconds}"
    
    def set_time_string(self, time_str: str):
        """设置时间字符串"""
        parts = time_str.split(':')
        if len(parts) == 3:
            self.time_vars['hours'].set(parts[0])
            self.time_vars['minutes'].set(parts[1])
            self.time_vars['seconds'].set(parts[2])
    
    def validate_time(self) -> bool:
        """验证时间格式是否正确"""
        try:
            time_str = self.get_time_string()
            parts = time_str.split(':')
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            return (hours >= 0 and 
                   0 <= minutes < 60 and 
                   0 <= seconds < 60)
        except (ValueError, IndexError):
            return False


class ProgressFrame(ttk.Frame):
    """进度显示控件"""
    
    def __init__(self, parent):
        """
        初始化进度显示控件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 进度条
        self.progress_bar = ttk.Progressbar(self, mode='determinate', length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # 进度标签
        self.progress_label = ttk.Label(self, text="就绪")
        self.progress_label.grid(row=1, column=0, sticky="w")
        
        # 详细信息标签
        self.detail_label = ttk.Label(self, text="", foreground="gray")
        self.detail_label.grid(row=1, column=1, sticky="e")
        
        # 配置列权重
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
    
    def update_progress(self, percentage: float, status_text: str = "", detail_text: str = ""):
        """
        更新进度显示
        
        Args:
            percentage: 进度百分比 (0-100)
            status_text: 状态文本
            detail_text: 详细信息文本
        """
        self.progress_bar['value'] = percentage
        
        if status_text:
            self.progress_label.config(text=status_text)
        
        if detail_text:
            self.detail_label.config(text=detail_text)
        
        # 强制更新显示
        self.update_idletasks()
    
    def reset(self):
        """重置进度显示"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="就绪")
        self.detail_label.config(text="")


class GPUModeFrame(ttk.Frame):
    """GPU模式选择控件"""
    
    def __init__(self, parent, callback: Callable = None):
        """
        初始化GPU模式选择控件
        
        Args:
            parent: 父控件
            callback: 模式选择回调函数
        """
        super().__init__(parent)
        
        self.callback = callback
        self.gpu_mode = tk.StringVar(value="cuda")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 标签
        ttk.Label(self, text="GPU加速:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # CUDA选项
        self.cuda_radio = ttk.Radiobutton(
            self, text="CUDA (NVIDIA)", 
            variable=self.gpu_mode, 
            value="cuda",
            command=self._on_mode_changed
        )
        self.cuda_radio.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        # AMD选项
        self.amd_radio = ttk.Radiobutton(
            self, text="AMD", 
            variable=self.gpu_mode, 
            value="amd",
            command=self._on_mode_changed
        )
        self.amd_radio.grid(row=0, column=2, sticky="w", padx=(0, 10))
        
        # CPU选项
        self.cpu_radio = ttk.Radiobutton(
            self, text="CPU", 
            variable=self.gpu_mode, 
            value="cpu",
            command=self._on_mode_changed
        )
        self.cpu_radio.grid(row=0, column=3, sticky="w")
    
    def _on_mode_changed(self):
        """模式变更回调"""
        if self.callback:
            self.callback(self.gpu_mode.get())
    
    def get_gpu_mode(self) -> str:
        """获取当前GPU模式"""
        return self.gpu_mode.get()
    
    def set_gpu_mode(self, mode: str):
        """设置GPU模式"""
        if mode in ["cuda", "amd", "cpu"]:
            self.gpu_mode.set(mode)
    
    def set_mode_availability(self, cuda_available: bool, amd_available: bool):
        """
        设置模式可用性
        
        Args:
            cuda_available: CUDA是否可用
            amd_available: AMD是否可用
        """
        state_cuda = "normal" if cuda_available else "disabled"
        state_amd = "normal" if amd_available else "disabled"
        
        self.cuda_radio.config(state=state_cuda)
        self.amd_radio.config(state=state_amd)
        
        # 如果当前选择的模式不可用，切换到CPU
        current_mode = self.gpu_mode.get()
        if (current_mode == "cuda" and not cuda_available) or \
           (current_mode == "amd" and not amd_available):
            self.gpu_mode.set("cpu")


class VideoInfoFrame(ttk.Frame):
    """视频信息显示控件"""
    
    def __init__(self, parent):
        """
        初始化视频信息显示控件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 创建信息显示区域
        self.info_text = tk.Text(
            self, 
            height=6, 
            width=50, 
            state='disabled',
            wrap='word'
        )
        self.info_text.grid(row=0, column=0, sticky="nsew")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置权重
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
    
    def update_info(self, info_dict: dict):
        """
        更新视频信息显示
        
        Args:
            info_dict: 视频信息字典
        """
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        
        if info_dict:
            info_text = "视频信息:\n"
            info_text += f"时长: {info_dict.get('duration', '未知')}\n"
            info_text += f"分辨率: {info_dict.get('resolution', '未知')}\n"
            info_text += f"视频编码: {info_dict.get('video_codec', '未知')}\n"
            info_text += f"音频编码: {info_dict.get('audio_codec', '未知')}\n"
            info_text += f"比特率: {info_dict.get('bitrate', '未知')}\n"
            info_text += f"帧率: {info_dict.get('frame_rate', '未知')}\n"
            info_text += f"文件大小: {info_dict.get('file_size', '未知')}"
        else:
            info_text = "请选择视频文件以查看信息"
        
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state='disabled')
    
    def clear_info(self):
        """清空信息显示"""
        self.update_info({})


class LogFrame(ttk.Frame):
    """日志显示控件"""
    
    def __init__(self, parent):
        """
        初始化日志显示控件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 创建文本区域
        self.log_text = tk.Text(
            self,
            height=10,
            width=80,
            state='disabled',
            wrap='word'
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置权重
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        添加日志信息
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARNING, ERROR)
        """
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 滚动到最新内容
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
