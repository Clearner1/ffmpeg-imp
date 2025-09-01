"""
FFmpeg GUI工具主窗口
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ffmpeg_manager import FFmpegManager
from core.gpu_detector import GPUDetector
from core.video_processor import VideoProcessor, ProcessStatus
from utils.config import config
from .widgets import (
    FileSelectFrame, DirectorySelectFrame, TimeInputFrame, 
    ProgressFrame, GPUModeFrame, VideoInfoFrame, LogFrame
)


class FFmpegGUI:
    """FFmpeg GUI主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFmpeg视频处理工具")
        self.root.geometry(config.get_window_geometry())
        
        # 核心组件
        self.ffmpeg_manager = FFmpegManager()
        self.gpu_detector = GPUDetector()
        self.video_processor = VideoProcessor()
        
        # 状态变量
        self.current_video_info = {}
        self.processing_mode = tk.StringVar(value="cut")  # cut 或 subtitle
        
        # 设置处理器回调
        self.video_processor.set_progress_callback(self._on_progress_update)
        self.video_processor.set_status_callback(self._on_status_update)
        
        self._create_widgets()
        self._setup_menu()
        self._init_ffmpeg()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """创建主界面控件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置根窗口权重
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)  # 日志区域可扩展
        main_frame.columnconfigure(0, weight=1)
        
        # FFmpeg设置区域
        self._create_ffmpeg_section(main_frame, 0)
        
        # 视频文件选择区域
        self._create_video_section(main_frame, 1)
        
        # 功能选择区域
        self._create_mode_section(main_frame, 2)
        
        # 功能设置区域
        self._create_settings_section(main_frame, 3)
        
        # 输出设置区域
        self._create_output_section(main_frame, 4)
        
        # 控制按钮区域
        self._create_control_section(main_frame, 5)
        
        # 进度和日志区域
        self._create_progress_log_section(main_frame, 6)
    
    def _create_ffmpeg_section(self, parent, row):
        """创建FFmpeg设置区域"""
        # FFmpeg设置框架
        ffmpeg_frame = ttk.LabelFrame(parent, text="FFmpeg设置", padding="5")
        ffmpeg_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ffmpeg_frame.columnconfigure(1, weight=1)
        
        # FFmpeg路径选择
        self.ffmpeg_select = FileSelectFrame(
            ffmpeg_frame, 
            "FFmpeg路径:", 
            [("可执行文件", "*.exe"), ("所有文件", "*.*")],
            callback=self._on_ffmpeg_selected
        )
        self.ffmpeg_select.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        
        # 状态标签
        self.ffmpeg_status_label = ttk.Label(ffmpeg_frame, text="未设置FFmpeg路径", foreground="red")
        self.ffmpeg_status_label.grid(row=1, column=0, sticky="w")
        
        # 检测GPU按钮
        self.detect_gpu_button = ttk.Button(
            ffmpeg_frame, 
            text="检测GPU支持", 
            command=self._detect_gpu_support
        )
        self.detect_gpu_button.grid(row=1, column=1, sticky="e", padx=(5, 0))
        
        # 自动查找按钮
        self.auto_find_button = ttk.Button(
            ffmpeg_frame, 
            text="自动查找", 
            command=self._auto_find_ffmpeg
        )
        self.auto_find_button.grid(row=1, column=2, sticky="e", padx=(5, 0))
    
    def _create_video_section(self, parent, row):
        """创建视频文件选择区域"""
        video_frame = ttk.LabelFrame(parent, text="视频文件", padding="5")
        video_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        video_frame.columnconfigure(0, weight=2)
        video_frame.columnconfigure(1, weight=1)
        
        # 视频文件选择
        video_types = [
            ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp"),
            ("所有文件", "*.*")
        ]
        
        self.video_select = FileSelectFrame(
            video_frame, 
            "视频文件:", 
            video_types,
            config.get_last_directory("video"),
            callback=self._on_video_selected
        )
        self.video_select.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # 视频信息显示
        self.video_info = VideoInfoFrame(video_frame)
        self.video_info.grid(row=0, column=1, sticky="nsew")
    
    def _create_mode_section(self, parent, row):
        """创建功能选择区域"""
        mode_frame = ttk.LabelFrame(parent, text="功能选择", padding="5")
        mode_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        
        # 功能选择单选按钮
        ttk.Radiobutton(
            mode_frame, 
            text="视频切片", 
            variable=self.processing_mode, 
            value="cut",
            command=self._on_mode_changed
        ).grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        ttk.Radiobutton(
            mode_frame, 
            text="字幕烧录", 
            variable=self.processing_mode, 
            value="subtitle",
            command=self._on_mode_changed
        ).grid(row=0, column=1, sticky="w")
    
    def _create_settings_section(self, parent, row):
        """创建功能设置区域"""
        self.settings_frame = ttk.LabelFrame(parent, text="设置", padding="5")
        self.settings_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        self.settings_frame.columnconfigure(0, weight=1)
        
        # 创建切片设置框架
        self._create_cut_settings()
        
        # 创建字幕设置框架
        self._create_subtitle_settings()
        
        # 显示切片设置（默认）
        self._on_mode_changed()
    
    def _create_cut_settings(self):
        """创建切片设置"""
        self.cut_frame = ttk.Frame(self.settings_frame)
        
        # 时间输入区域
        time_frame = ttk.Frame(self.cut_frame)
        time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        time_frame.columnconfigure(2, weight=1)
        
        # 开始时间
        self.start_time = TimeInputFrame(time_frame, "开始时间:")
        self.start_time.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        # 结束时间
        self.end_time = TimeInputFrame(time_frame, "结束时间:")
        self.end_time.grid(row=0, column=1, sticky="w")
        
        # GPU模式选择
        self.gpu_mode = GPUModeFrame(self.cut_frame, callback=self._on_gpu_mode_changed)
        self.gpu_mode.grid(row=1, column=0, sticky="ew")
        
        # 质量设置
        quality_frame = ttk.Frame(self.cut_frame)
        quality_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Label(quality_frame, text="质量:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.quality_var = tk.StringVar(value="medium")
        quality_combo = ttk.Combobox(
            quality_frame, 
            textvariable=self.quality_var,
            values=["low", "medium", "high"],
            state="readonly"
        )
        quality_combo.grid(row=0, column=1, sticky="w")
    
    def _create_subtitle_settings(self):
        """创建字幕设置"""
        self.subtitle_frame = ttk.Frame(self.settings_frame)
        
        # 字幕文件选择
        subtitle_types = [
            ("字幕文件", "*.srt *.ass *.ssa *.vtt *.sub"),
            ("所有文件", "*.*")
        ]
        
        self.subtitle_select = FileSelectFrame(
            self.subtitle_frame,
            "字幕文件:",
            subtitle_types
        )
        self.subtitle_select.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # GPU模式选择（字幕烧录）
        self.subtitle_gpu_mode = GPUModeFrame(self.subtitle_frame)
        self.subtitle_gpu_mode.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # 字幕样式设置
        style_frame = ttk.Frame(self.subtitle_frame)
        style_frame.grid(row=2, column=0, sticky="ew")
        
        # 字体大小
        ttk.Label(style_frame, text="字体大小:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.font_size_var = tk.StringVar(value="24")
        font_size_entry = ttk.Entry(style_frame, textvariable=self.font_size_var, width=5)
        font_size_entry.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        # 字体颜色
        ttk.Label(style_frame, text="字体颜色:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.font_color_var = tk.StringVar(value="white")
        color_combo = ttk.Combobox(
            style_frame,
            textvariable=self.font_color_var,
            values=["white", "black", "red", "green", "blue", "yellow"],
            state="readonly"
        )
        color_combo.grid(row=0, column=3, sticky="w")
    
    def _create_output_section(self, parent, row):
        """创建输出设置区域"""
        output_frame = ttk.LabelFrame(parent, text="输出设置", padding="5")
        output_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        
        # 输出目录选择
        self.output_select = DirectorySelectFrame(
            output_frame,
            "输出目录:",
            config.get_last_directory("output")
        )
        self.output_select.grid(row=0, column=0, sticky="ew")
    
    def _create_control_section(self, parent, row):
        """创建控制按钮区域"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        
        # 开始处理按钮
        self.start_button = ttk.Button(
            control_frame, 
            text="开始处理", 
            command=self._start_processing
        )
        self.start_button.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # 停止按钮
        self.stop_button = ttk.Button(
            control_frame, 
            text="停止", 
            command=self._stop_processing,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        # 清空日志按钮
        self.clear_log_button = ttk.Button(
            control_frame, 
            text="清空日志", 
            command=self._clear_log
        )
        self.clear_log_button.grid(row=0, column=2, sticky="w")
    
    def _create_progress_log_section(self, parent, row):
        """创建进度和日志区域"""
        progress_log_frame = ttk.Frame(parent)
        progress_log_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 0))
        progress_log_frame.rowconfigure(1, weight=1)
        progress_log_frame.columnconfigure(0, weight=1)
        
        # 进度显示
        self.progress_display = ProgressFrame(progress_log_frame)
        self.progress_display.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # 日志显示
        log_frame = ttk.LabelFrame(progress_log_frame, text="处理日志", padding="5")
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_display = LogFrame(log_frame)
        self.log_display.grid(row=0, column=0, sticky="nsew")
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开视频", command=self._open_video_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="检测GPU支持", command=self._detect_gpu_support)
        tools_menu.add_command(label="FFmpeg信息", command=self._show_ffmpeg_info)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _init_ffmpeg(self):
        """初始化FFmpeg"""
        # 从配置加载FFmpeg路径
        saved_path = config.get_ffmpeg_path()
        if saved_path and os.path.exists(saved_path):
            self.ffmpeg_select.set_file_path(saved_path)
            self._on_ffmpeg_selected(saved_path)
        else:
            # 尝试自动查找
            self._auto_find_ffmpeg()
    
    def _auto_find_ffmpeg(self):
        """自动查找FFmpeg"""
        self.log_display.add_log("正在自动查找FFmpeg...")
        
        def find_thread():
            ffmpeg_path = self.ffmpeg_manager.find_ffmpeg()
            
            def update_ui():
                if ffmpeg_path:
                    self.ffmpeg_select.set_file_path(ffmpeg_path)
                    self._on_ffmpeg_selected(ffmpeg_path)
                    self.log_display.add_log(f"自动找到FFmpeg: {ffmpeg_path}")
                else:
                    self.log_display.add_log("未找到FFmpeg，请手动选择", "WARNING")
            
            self.root.after(0, update_ui)
        
        threading.Thread(target=find_thread, daemon=True).start()
    
    def _on_ffmpeg_selected(self, path: str):
        """FFmpeg路径选择回调"""
        if self.ffmpeg_manager.set_ffmpeg_path(path):
            self.ffmpeg_status_label.config(
                text=f"FFmpeg {self.ffmpeg_manager.version} - 就绪", 
                foreground="green"
            )
            config.set_ffmpeg_path(path)
            self.log_display.add_log(f"FFmpeg设置成功: {path}")
            
            # 检测GPU支持
            self._detect_gpu_support()
        else:
            self.ffmpeg_status_label.config(
                text="FFmpeg路径无效", 
                foreground="red"
            )
            self.log_display.add_log("FFmpeg路径无效", "ERROR")
    
    def _detect_gpu_support(self):
        """检测GPU支持"""
        if not self.ffmpeg_manager.is_valid:
            messagebox.showwarning("警告", "请先设置有效的FFmpeg路径")
            return
        
        self.log_display.add_log("正在检测GPU支持...")
        
        def detect_thread():
            # 检测GPU
            gpus = self.gpu_detector.detect_gpus()
            gpu_support = self.gpu_detector.check_ffmpeg_gpu_support(self.ffmpeg_manager.ffmpeg_path)
            
            def update_ui():
                cuda_available = gpu_support.get("cuda", False) and \
                               any(gpu.vendor == "nvidia" for gpu in gpus)
                amd_available = (gpu_support.get("amf", False) or gpu_support.get("opencl", False)) and \
                              any(gpu.vendor == "amd" for gpu in gpus)
                
                # 更新GPU模式控件
                self.gpu_mode.set_mode_availability(cuda_available, amd_available)
                self.subtitle_gpu_mode.set_mode_availability(cuda_available, amd_available)
                
                # 记录检测结果
                self.log_display.add_log(f"检测到 {len(gpus)} 个GPU")
                for gpu in gpus:
                    self.log_display.add_log(f"  - {gpu.name} ({gpu.vendor})")
                
                self.log_display.add_log(f"FFmpeg GPU支持: CUDA={cuda_available}, AMD={amd_available}")
                
                # 设置推荐模式
                recommended = self.gpu_detector.get_recommended_gpu_mode()
                self.gpu_mode.set_gpu_mode(recommended)
                self.subtitle_gpu_mode.set_gpu_mode(recommended)
                config.set_gpu_mode(recommended)
            
            self.root.after(0, update_ui)
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def _open_video_file(self):
        """打开视频文件"""
        video_types = [
            ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=video_types,
            initialdir=config.get_last_directory("video")
        )
        
        if filename:
            self.video_select.set_file_path(filename)
            self._on_video_selected(filename)
    
    def _on_video_selected(self, path: str):
        """视频文件选择回调"""
        if not os.path.exists(path):
            return
        
        config.set_last_directory("video", path)
        config.add_recent_file(path)
        
        # 处理长文件名显示
        filename = os.path.basename(path)
        if len(filename) > 50:
            display_name = filename[:47] + "..."
            self.log_display.add_log(f"选择视频文件: {display_name}")
            self.log_display.add_log(f"完整路径: {path}", "INFO")
        else:
            self.log_display.add_log(f"选择视频文件: {filename}")
        
        # 检查文件名长度和特殊字符
        if len(path) > 260:
            self.log_display.add_log("注意: 文件路径很长，如果处理出错请考虑移动到较短路径", "WARNING")
        
        # 获取视频信息
        if self.ffmpeg_manager.is_valid:
            def get_info_thread():
                self.log_display.add_log("正在获取视频信息...")
                info = self.ffmpeg_manager.get_video_info(path)
                
                def update_ui():
                    self.current_video_info = info
                    self.video_info.update_info(info)
                    
                    # 设置视频总时长用于进度计算
                    if info.get("duration") and info.get("duration") != "未知":
                        self.video_processor.set_total_duration(info["duration"])
                        self.log_display.add_log(f"视频时长: {info['duration']}")
                    else:
                        self.log_display.add_log("视频信息获取完成 (部分信息可能不可用)", "WARNING")
                
                self.root.after(0, update_ui)
            
            threading.Thread(target=get_info_thread, daemon=True).start()
        else:
            self.video_info.update_info({
                "duration": "需要FFmpeg", 
                "resolution": "需要FFmpeg",
                "video_codec": "需要FFmpeg",
                "audio_codec": "需要FFmpeg",
                "bitrate": "需要FFmpeg",
                "frame_rate": "需要FFmpeg",
                "file_size": self._get_file_size_fallback(path)
            })
    
    def _on_mode_changed(self):
        """功能模式变更回调"""
        mode = self.processing_mode.get()
        
        # 隐藏所有设置框架
        self.cut_frame.grid_remove()
        self.subtitle_frame.grid_remove()
        
        # 显示对应的设置框架
        if mode == "cut":
            self.cut_frame.grid(row=0, column=0, sticky="ew")
            self.settings_frame.config(text="切片设置")
        elif mode == "subtitle":
            self.subtitle_frame.grid(row=0, column=0, sticky="ew")
            self.settings_frame.config(text="字幕烧录设置")
    
    def _on_gpu_mode_changed(self, mode: str):
        """GPU模式变更回调"""
        config.set_gpu_mode(mode)
        self.log_display.add_log(f"GPU模式切换为: {mode.upper()}")
    
    def _start_processing(self):
        """开始处理"""
        if not self._validate_inputs():
            return
        
        # 构建命令
        try:
            command = self._build_command()
            task_name = "视频切片" if self.processing_mode.get() == "cut" else "字幕烧录"
            
            # 更新UI状态
            self._set_processing_state(True)
            
            # 开始处理
            success = self.video_processor.start_process(command, task_name)
            if not success:
                self._set_processing_state(False)
                messagebox.showerror("错误", "启动处理失败")
        
        except Exception as e:
            self._set_processing_state(False)
            messagebox.showerror("错误", f"处理失败: {str(e)}")
            self.log_display.add_log(f"处理失败: {str(e)}", "ERROR")
    
    def _stop_processing(self):
        """停止处理"""
        self.video_processor.stop_process()
        self._set_processing_state(False)
    
    def _validate_inputs(self) -> bool:
        """验证输入"""
        # 检查FFmpeg
        if not self.ffmpeg_manager.is_valid:
            messagebox.showerror("错误", "请先设置有效的FFmpeg路径")
            return False
        
        # 检查视频文件
        video_path = self.video_select.get_file_path()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("错误", "请选择有效的视频文件")
            return False
        
        mode = self.processing_mode.get()
        
        if mode == "cut":
            # 验证时间输入
            if not self.start_time.validate_time() or not self.end_time.validate_time():
                messagebox.showerror("错误", "请输入有效的时间格式 (HH:MM:SS)")
                return False
            
            # 验证时间逻辑
            start_seconds = self.ffmpeg_manager.time_to_seconds(self.start_time.get_time_string())
            end_seconds = self.ffmpeg_manager.time_to_seconds(self.end_time.get_time_string())
            
            if start_seconds >= end_seconds:
                messagebox.showerror("错误", "结束时间必须大于开始时间")
                return False
        
        elif mode == "subtitle":
            # 检查字幕文件
            subtitle_path = self.subtitle_select.get_file_path()
            if not subtitle_path or not os.path.exists(subtitle_path):
                messagebox.showerror("错误", "请选择有效的字幕文件")
                return False
        
        # 检查输出目录
        output_dir = self.output_select.get_directory_path()
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return False
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
                return False
        
        return True
    
    def _build_command(self) -> list:
        """构建FFmpeg命令"""
        video_path = self.video_select.get_file_path()
        output_dir = self.output_select.get_directory_path()
        mode = self.processing_mode.get()
        
        # 生成输出文件名
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        if mode == "cut":
            start_time = self.start_time.get_time_string()
            end_time = self.end_time.get_time_string()
            gpu_mode = self.gpu_mode.get_gpu_mode()
            quality = self.quality_var.get()
            
            output_name = f"{video_name}_cut_{start_time.replace(':', '')}-{end_time.replace(':', '')}.mp4"
            output_path = os.path.join(output_dir, output_name)
            
            command = self.ffmpeg_manager.build_cut_command(
                video_path, output_path, start_time, end_time, gpu_mode, quality
            )
        
        elif mode == "subtitle":
            subtitle_path = self.subtitle_select.get_file_path()
            gpu_mode = self.subtitle_gpu_mode.get_gpu_mode()
            font_size = int(self.font_size_var.get() or "24")
            font_color = self.font_color_var.get()
            
            output_name = f"{video_name}_with_subtitle.mp4"
            output_path = os.path.join(output_dir, output_name)
            
            command = self.ffmpeg_manager.build_subtitle_burn_command(
                video_path, subtitle_path, output_path, gpu_mode, font_size, font_color
            )
        
        else:
            raise ValueError(f"未知的处理模式: {mode}")
        
        config.set_last_directory("output", output_dir)
        self.log_display.add_log(f"输出文件: {output_name}")
        
        # 显示实际的FFmpeg命令（调试用）
        self.log_display.add_log(f"GPU模式: {gpu_mode}")
        cmd_str = " ".join(command)
        if len(cmd_str) > 200:
            cmd_display = cmd_str[:197] + "..."
        else:
            cmd_display = cmd_str
        self.log_display.add_log(f"FFmpeg命令: {cmd_display}")
        
        return command
    
    def _set_processing_state(self, processing: bool):
        """设置处理状态"""
        state = "disabled" if processing else "normal"
        
        self.start_button.config(state=state)
        self.stop_button.config(state="normal" if processing else "disabled")
        
        # 禁用/启用输入控件
        for widget in [self.video_select, self.output_select]:
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button)):
                    child.config(state=state)
    
    def _on_progress_update(self, progress):
        """进度更新回调"""
        def update():
            percentage = progress.percentage
            status_text = f"进度: {percentage:.1f}% - {progress.time_processed}"
            detail_text = f"速度: {progress.speed} | 比特率: {progress.bitrate}"
            
            if progress.eta != "unknown":
                detail_text += f" | 预计剩余: {progress.eta}"
            
            self.progress_display.update_progress(percentage, status_text, detail_text)
        
        self.root.after(0, update)
    
    def _on_status_update(self, status, message):
        """状态更新回调"""
        def update():
            if status == ProcessStatus.COMPLETED:
                self.progress_display.update_progress(100, "处理完成", "")
                self.log_display.add_log("处理完成")
                self._set_processing_state(False)
                messagebox.showinfo("完成", "视频处理完成！")
            
            elif status == ProcessStatus.ERROR:
                self.progress_display.update_progress(0, "处理失败", "")
                self.log_display.add_log(f"处理失败: {message}", "ERROR")
                self._set_processing_state(False)
                messagebox.showerror("错误", f"处理失败: {message}")
            
            elif status == ProcessStatus.CANCELLED:
                self.progress_display.update_progress(0, "已取消", "")
                self.log_display.add_log("处理已取消", "WARNING")
                self._set_processing_state(False)
            
            else:
                self.log_display.add_log(message)
        
        self.root.after(0, update)
    
    def _clear_log(self):
        """清空日志"""
        self.log_display.clear_log()
    
    def _show_ffmpeg_info(self):
        """显示FFmpeg信息"""
        if not self.ffmpeg_manager.is_valid:
            messagebox.showwarning("警告", "请先设置有效的FFmpeg路径")
            return
        
        info = self.ffmpeg_manager.get_ffmpeg_info()
        gpu_summary = self.gpu_detector.get_gpu_summary()
        
        info_text = f"FFmpeg路径: {info['path']}\n"
        info_text += f"版本: {info['version']}\n\n"
        info_text += "GPU支持情况:\n"
        for key, value in info['gpu_support'].items():
            info_text += f"  {key.upper()}: {'是' if value else '否'}\n"
        
        info_text += f"\n检测到的GPU:\n"
        for gpu in gpu_summary['detected_gpus']:
            info_text += f"  - {gpu['name']} ({gpu['vendor']})\n"
        
        messagebox.showinfo("FFmpeg信息", info_text)
    
    def _get_file_size_fallback(self, file_path: str) -> str:
        """备用文件大小获取方法"""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except Exception:
            return "未知"
    
    def _show_about(self):
        """显示关于信息"""
        about_text = """FFmpeg视频处理工具

功能特性:
• 视频切片 - 支持精确时间裁剪
• 字幕烧录 - 将字幕嵌入视频
• GPU加速 - 支持NVIDIA CUDA和AMD硬件加速
• 智能检测 - 自动检测FFmpeg和GPU支持
• 长文件名支持 - 处理包含中文和特殊字符的文件

开发语言: Python + Tkinter
版本: 1.1.0 - 高级GPU优化版"""
        
        messagebox.showinfo("关于", about_text)
    
    def _on_closing(self):
        """窗口关闭事件"""
        # 保存窗口几何信息
        geometry = self.root.geometry()
        config.set_window_geometry(geometry)
        
        # 停止正在运行的处理
        if self.video_processor.status == ProcessStatus.RUNNING:
            if messagebox.askyesno("确认", "有处理正在进行，确定要退出吗？"):
                self.video_processor.stop_process()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """运行GUI应用"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()


def main():
    """主函数"""
    app = FFmpegGUI()
    app.run()


if __name__ == "__main__":
    main()
