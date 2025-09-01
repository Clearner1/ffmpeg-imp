"""
配置管理模块
用于管理FFmpeg GUI工具的配置设置
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件名
        """
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {}
        self._default_config = {
            "ffmpeg_path": "",
            "last_video_directory": "",
            "last_output_directory": "",
            "default_gpu_mode": "cuda",  # cuda, amd, cpu
            "video_quality": "medium",   # low, medium, high
            "remember_settings": True,
            "window_geometry": "800x600+100+100",
            "recent_files": [],
            "subtitle_font_size": 24,
            "subtitle_font_color": "white",
            "max_recent_files": 10
        }
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                    # 合并默认配置，确保所有键都存在
                    for key, value in self._default_config.items():
                        if key not in self.config_data:
                            self.config_data[key] = value
            else:
                self.config_data = self._default_config.copy()
                self.save_config()
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"配置文件加载失败: {e}")
            self.config_data = self._default_config.copy()
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            return True
        except (PermissionError, OSError) as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config_data[key] = value
    
    def get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径"""
        return self.get("ffmpeg_path", "")
    
    def set_ffmpeg_path(self, path: str) -> None:
        """设置FFmpeg路径"""
        self.set("ffmpeg_path", path)
        self.save_config()
    
    def get_last_directory(self, dir_type: str) -> str:
        """
        获取最后使用的目录
        
        Args:
            dir_type: 目录类型 ('video' 或 'output')
            
        Returns:
            目录路径
        """
        key = f"last_{dir_type}_directory"
        directory = self.get(key, "")
        if directory and os.path.exists(directory):
            return directory
        return os.path.expanduser("~")  # 默认返回用户主目录
    
    def set_last_directory(self, dir_type: str, path: str) -> None:
        """
        设置最后使用的目录
        
        Args:
            dir_type: 目录类型 ('video' 或 'output')
            path: 目录路径
        """
        key = f"last_{dir_type}_directory"
        self.set(key, os.path.dirname(path) if os.path.isfile(path) else path)
        self.save_config()
    
    def add_recent_file(self, file_path: str) -> None:
        """
        添加最近使用的文件
        
        Args:
            file_path: 文件路径
        """
        recent_files = self.get("recent_files", [])
        
        # 如果文件已存在，先移除
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # 添加到开头
        recent_files.insert(0, file_path)
        
        # 限制最大数量
        max_files = self.get("max_recent_files", 10)
        if len(recent_files) > max_files:
            recent_files = recent_files[:max_files]
        
        self.set("recent_files", recent_files)
        self.save_config()
    
    def get_recent_files(self) -> list:
        """获取最近使用的文件列表"""
        recent_files = self.get("recent_files", [])
        # 过滤掉不存在的文件
        existing_files = [f for f in recent_files if os.path.exists(f)]
        if len(existing_files) != len(recent_files):
            self.set("recent_files", existing_files)
            self.save_config()
        return existing_files
    
    def get_gpu_mode(self) -> str:
        """获取GPU模式"""
        return self.get("default_gpu_mode", "cuda")
    
    def set_gpu_mode(self, mode: str) -> None:
        """设置GPU模式"""
        if mode in ["cuda", "amd", "cpu"]:
            self.set("default_gpu_mode", mode)
            self.save_config()
    
    def get_window_geometry(self) -> str:
        """获取窗口几何信息"""
        return self.get("window_geometry", "800x600+100+100")
    
    def set_window_geometry(self, geometry: str) -> None:
        """设置窗口几何信息"""
        self.set("window_geometry", geometry)
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.config_data = self._default_config.copy()
        self.save_config()


# 全局配置实例
config = ConfigManager()
