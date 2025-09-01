"""
FFmpeg管理模块
管理FFmpeg路径、版本检测和命令构建
"""
import os
import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from .gpu_detector import GPUDetector


class FFmpegManager:
    """FFmpeg管理器"""
    
    def __init__(self):
        self.ffmpeg_path: str = ""
        self.version: str = ""
        self.is_valid: bool = False
        self.gpu_detector = GPUDetector()
        self.supported_formats = {
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            'subtitle': ['.srt', '.ass', '.ssa', '.vtt', '.sub']
        }
    
    def find_ffmpeg(self) -> Optional[str]:
        """
        自动查找FFmpeg可执行文件
        
        Returns:
            FFmpeg路径，如果未找到则返回None
        """
        # 常见的FFmpeg可能位置
        possible_paths = [
            "ffmpeg",  # 系统PATH中
            "ffmpeg.exe",  # Windows
            "/usr/bin/ffmpeg",  # Linux标准位置
            "/usr/local/bin/ffmpeg",  # Linux本地安装
            "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew ARM
            "/usr/local/Cellar/ffmpeg/*/bin/ffmpeg",  # macOS Homebrew Intel
        ]
        
        # Windows额外路径
        if os.name == 'nt':
            possible_paths.extend([
                "C:\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
            ])
        
        for path in possible_paths:
            if self._test_ffmpeg_path(path):
                return path
        
        # 尝试使用which命令查找
        try:
            result = shutil.which("ffmpeg")
            if result and self._test_ffmpeg_path(result):
                return result
        except Exception:
            pass
        
        return None
    
    def _test_ffmpeg_path(self, path: str) -> bool:
        """
        测试FFmpeg路径是否有效
        
        Args:
            path: FFmpeg路径
            
        Returns:
            是否有效
        """
        try:
            # 扩展路径中的通配符
            if '*' in path:
                from glob import glob
                matches = glob(path)
                if matches:
                    path = matches[0]
                else:
                    return False
            
            if not os.path.exists(path):
                return False
            
            # 尝试运行FFmpeg获取版本信息
            result = subprocess.run(
                [path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result.returncode == 0 and "ffmpeg version" in result.stdout.lower()
        
        except Exception:
            return False
    
    def set_ffmpeg_path(self, path: str) -> bool:
        """
        设置FFmpeg路径并验证
        
        Args:
            path: FFmpeg路径
            
        Returns:
            设置是否成功
        """
        if self._test_ffmpeg_path(path):
            self.ffmpeg_path = path
            self.is_valid = True
            self._get_version_info()
            
            # 重要：设置FFmpeg路径后，检测GPU支持
            self.gpu_detector.detect_gpus()
            self.gpu_detector.check_ffmpeg_gpu_support(path)
            
            return True
        else:
            self.ffmpeg_path = ""
            self.is_valid = False
            self.version = ""
            return False
    
    def _get_version_info(self) -> None:
        """获取FFmpeg版本信息"""
        if not self.is_valid:
            return
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                # 解析版本号
                version_match = re.search(r'ffmpeg version (\S+)', result.stdout)
                if version_match:
                    self.version = version_match.group(1)
                else:
                    self.version = "未知版本"
        except Exception as e:
            print(f"获取FFmpeg版本失败: {e}")
            self.version = "版本获取失败"
    
    def get_video_info(self, video_path: str) -> Dict[str, any]:
        """
        获取视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        if not self.is_valid or not os.path.exists(video_path):
            return {}
        
        try:
            # 处理长文件名和特殊字符
            # 在Windows上，如果路径太长或包含特殊字符，使用短路径或引号包装
            safe_video_path = self._make_safe_path(video_path)
            
            cmd = [
                self.ffmpeg_path, "-i", safe_video_path,
                "-hide_banner", "-f", "null", "-",
                "-v", "quiet"  # 减少输出，提高性能
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,  # 减少超时时间
                encoding='utf-8',
                errors='ignore'
            )
            
            # FFmpeg将信息输出到stderr
            output = result.stderr
            
            info = {
                "duration": self._extract_duration(output),
                "resolution": self._extract_resolution(output),
                "video_codec": self._extract_codec(output, "Video"),
                "audio_codec": self._extract_codec(output, "Audio"),
                "bitrate": self._extract_bitrate(output),
                "frame_rate": self._extract_frame_rate(output),
                "file_size": self._get_file_size(video_path)
            }
            
            return info
        
        except subprocess.TimeoutExpired:
            print(f"获取视频信息超时: 文件名可能过长或包含特殊字符")
            # 返回基本信息
            return {
                "duration": "未知",
                "resolution": "未知", 
                "video_codec": "未知",
                "audio_codec": "未知",
                "bitrate": "未知",
                "frame_rate": "未知",
                "file_size": self._get_file_size(video_path)
            }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return {}
    
    def _extract_duration(self, output: str) -> str:
        """从FFmpeg输出中提取时长"""
        duration_match = re.search(r'Duration: (\d{2}:\d{2}:\d{2}\.\d{2})', output)
        return duration_match.group(1) if duration_match else "未知"
    
    def _extract_resolution(self, output: str) -> str:
        """从FFmpeg输出中提取分辨率"""
        resolution_match = re.search(r'(\d{3,4}x\d{3,4})', output)
        return resolution_match.group(1) if resolution_match else "未知"
    
    def _extract_codec(self, output: str, stream_type: str) -> str:
        """从FFmpeg输出中提取编解码器"""
        pattern = rf'{stream_type}: (\w+)'
        codec_match = re.search(pattern, output)
        return codec_match.group(1) if codec_match else "未知"
    
    def _extract_bitrate(self, output: str) -> str:
        """从FFmpeg输出中提取比特率"""
        bitrate_match = re.search(r'bitrate: (\d+) kb/s', output)
        return f"{bitrate_match.group(1)} kb/s" if bitrate_match else "未知"
    
    def _extract_frame_rate(self, output: str) -> str:
        """从FFmpeg输出中提取帧率"""
        fps_match = re.search(r'(\d+(?:\.\d+)?)\s*fps', output)
        return f"{fps_match.group(1)} fps" if fps_match else "未知"
    
    def _get_file_size(self, file_path: str) -> str:
        """获取文件大小"""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except Exception:
            return "未知"
    
    def _make_safe_path(self, file_path: str) -> str:
        """
        创建安全的文件路径，处理长文件名和特殊字符
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            安全的文件路径
        """
        try:
            # 标准化路径
            normalized_path = os.path.normpath(file_path)
            
            # Windows系统特殊处理
            if os.name == 'nt':
                # 检查路径长度
                if len(normalized_path) > 260:
                    try:
                        # 尝试获取短路径名
                        import ctypes
                        from ctypes import wintypes
                        
                        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                        GetShortPathNameW.restype = wintypes.DWORD
                        
                        buffer_size = 500
                        buffer = ctypes.create_unicode_buffer(buffer_size)
                        result = GetShortPathNameW(normalized_path, buffer, buffer_size)
                        
                        if result > 0:
                            return buffer.value
                    except Exception:
                        pass
                
                # 对于包含Unicode字符的路径，保持原样
                # subprocess.run() 会正确处理Unicode路径
            
            return normalized_path
            
        except Exception as e:
            print(f"路径安全化失败: {e}")
            return file_path
    
    def build_cut_command(self, 
                         input_file: str,
                         output_file: str,
                         start_time: str,
                         end_time: str,
                         gpu_mode: str = "cpu",
                         quality: str = "medium") -> List[str]:
        """
        构建视频切片命令
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            start_time: 开始时间 (HH:MM:SS)
            end_time: 结束时间 (HH:MM:SS)
            gpu_mode: GPU模式 (cuda, amd, cpu)
            quality: 质量设置 (low, medium, high)
            
        Returns:
            FFmpeg命令列表
        """
        if not self.is_valid:
            raise ValueError("FFmpeg路径无效")
        
        cmd = [self.ffmpeg_path]
        
        # 添加GPU加速参数（包含高级优化）
        gpu_args = self.gpu_detector.get_gpu_acceleration_args(gpu_mode, advanced=True)
        cmd.extend(gpu_args)
        
        # 时间参数（在输入文件之前，更高效的seeking）
        cmd.extend(["-ss", start_time, "-to", end_time])
        
        # 输入文件 - 使用安全路径
        safe_input_file = self._make_safe_path(input_file)
        cmd.extend(["-i", safe_input_file])
        
        # 编码器设置
        video_encoder = self.gpu_detector.get_gpu_encoder(gpu_mode, "h264")
        if video_encoder:
            cmd.extend(["-c:v", video_encoder])
        else:
            cmd.extend(["-c:v", "libx264"])
        
        # 质量设置
        quality_settings = self._get_quality_settings(quality, gpu_mode)
        cmd.extend(quality_settings)
        
        # 音频编码
        cmd.extend(["-c:a", "copy"])  # 复制音频，不重新编码
        
        # 输出文件 - 使用安全路径
        safe_output_file = self._make_safe_path(output_file)
        cmd.append(safe_output_file)
        
        return cmd
    
    def build_subtitle_burn_command(self,
                                  input_file: str,
                                  subtitle_file: str,
                                  output_file: str,
                                  gpu_mode: str = "cpu",
                                  font_size: int = 24,
                                  font_color: str = "white") -> List[str]:
        """
        构建字幕烧录命令
        
        Args:
            input_file: 输入视频文件路径
            subtitle_file: 字幕文件路径
            output_file: 输出文件路径
            gpu_mode: GPU模式 (cuda, amd, cpu)
            font_size: 字体大小
            font_color: 字体颜色
            
        Returns:
            FFmpeg命令列表
        """
        if not self.is_valid:
            raise ValueError("FFmpeg路径无效")
        
        cmd = [self.ffmpeg_path]
        
        # 添加GPU加速参数（包含高级优化）
        gpu_args = self.gpu_detector.get_gpu_acceleration_args(gpu_mode, advanced=True)
        cmd.extend(gpu_args)
        
        # 输入文件 - 使用安全路径
        safe_input_file = self._make_safe_path(input_file)
        cmd.extend(["-i", safe_input_file])
        
        # 字幕滤镜 - 使用安全路径，并转义特殊字符
        safe_subtitle_file = self._make_safe_path(subtitle_file)
        # 对于字幕文件路径，需要特殊处理反斜杠和单引号
        escaped_subtitle_path = safe_subtitle_file.replace("\\", "/").replace("'", "\\'")
        subtitle_filter = f"subtitles='{escaped_subtitle_path}':force_style='FontSize={font_size},PrimaryColour=&H{self._color_to_hex(font_color)}'"
        cmd.extend(["-vf", subtitle_filter])
        
        # 编码器设置
        video_encoder = self.gpu_detector.get_gpu_encoder(gpu_mode, "h264")
        if video_encoder:
            cmd.extend(["-c:v", video_encoder])
        else:
            cmd.extend(["-c:v", "libx264"])
        
        # 音频编码
        cmd.extend(["-c:a", "copy"])
        
        # 输出文件 - 使用安全路径
        safe_output_file = self._make_safe_path(output_file)
        cmd.append(safe_output_file)
        
        return cmd
    
    def _get_quality_settings(self, quality: str, gpu_mode: str) -> List[str]:
        """
        获取质量设置参数
        
        Args:
            quality: 质量等级 (low, medium, high)
            gpu_mode: GPU模式
            
        Returns:
            质量参数列表
        """
        if gpu_mode == "cuda":
            # NVIDIA GPU编码器质量设置 - 使用比特率控制获得更好效果
            quality_map = {
                "low": ["-preset", "fast", "-b:v", "3M"],
                "medium": ["-preset", "medium", "-b:v", "5M"], 
                "high": ["-preset", "slow", "-b:v", "8M"]
            }
        elif gpu_mode == "amd":
            # AMD GPU编码器质量设置
            quality_map = {
                "low": ["-b:v", "3M"],
                "medium": ["-b:v", "5M"],
                "high": ["-b:v", "8M"]
            }
        else:
            # CPU编码器质量设置 - 使用CRF获得更好的压缩效率
            quality_map = {
                "low": ["-preset", "fast", "-crf", "28"],
                "medium": ["-preset", "medium", "-crf", "23"],
                "high": ["-preset", "slow", "-crf", "18"]
            }
        
        return quality_map.get(quality, quality_map["medium"])
    
    def _color_to_hex(self, color_name: str) -> str:
        """
        颜色名称转换为十六进制
        
        Args:
            color_name: 颜色名称
            
        Returns:
            十六进制颜色值
        """
        color_map = {
            "white": "FFFFFF",
            "black": "000000",
            "red": "FF0000",
            "green": "00FF00",
            "blue": "0000FF",
            "yellow": "FFFF00",
            "cyan": "00FFFF",
            "magenta": "FF00FF"
        }
        return color_map.get(color_name.lower(), "FFFFFF")
    
    def is_supported_video_format(self, file_path: str) -> bool:
        """
        检查是否为支持的视频格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats['video']
    
    def is_supported_subtitle_format(self, file_path: str) -> bool:
        """
        检查是否为支持的字幕格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats['subtitle']
    
    def validate_time_format(self, time_str: str) -> bool:
        """
        验证时间格式
        
        Args:
            time_str: 时间字符串 (HH:MM:SS)
            
        Returns:
            格式是否正确
        """
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5]?[0-9]):([0-5]?[0-9])$'
        return bool(re.match(pattern, time_str))
    
    def time_to_seconds(self, time_str: str) -> int:
        """
        将时间字符串转换为秒数
        
        Args:
            time_str: 时间字符串 (HH:MM:SS)
            
        Returns:
            秒数
        """
        if not self.validate_time_format(time_str):
            raise ValueError(f"无效的时间格式: {time_str}")
        
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_ffmpeg_info(self) -> Dict[str, any]:
        """
        获取FFmpeg信息摘要
        
        Returns:
            FFmpeg信息字典
        """
        if not self.is_valid:
            return {"valid": False, "message": "FFmpeg路径无效或未设置"}
        
        # 获取GPU支持信息
        gpu_support = self.gpu_detector.check_ffmpeg_gpu_support(self.ffmpeg_path)
        
        return {
            "valid": True,
            "path": self.ffmpeg_path,
            "version": self.version,
            "gpu_support": gpu_support,
            "supported_formats": self.supported_formats
        }
