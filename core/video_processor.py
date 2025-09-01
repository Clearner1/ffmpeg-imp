"""
视频处理模块
负责执行FFmpeg命令和监控处理进度
"""
import subprocess
import threading
import re
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ProcessStatus(Enum):
    """处理状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProcessProgress:
    """处理进度数据类"""
    percentage: float = 0.0
    time_processed: str = "00:00:00"
    speed: str = "0x"
    bitrate: str = "0 kbits/s"
    fps: float = 0.0
    eta: str = "unknown"
    current_frame: int = 0
    total_frames: int = 0


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.status = ProcessStatus.IDLE
        self.progress = ProcessProgress()
        self.error_message: str = ""
        self.progress_callback: Optional[Callable[[ProcessProgress], None]] = None
        self.status_callback: Optional[Callable[[ProcessStatus, str], None]] = None
        self.current_task: str = ""
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
    def set_progress_callback(self, callback: Callable[[ProcessProgress], None]) -> None:
        """
        设置进度回调函数
        
        Args:
            callback: 进度回调函数，接收ProcessProgress参数
        """
        self.progress_callback = callback
    
    def set_status_callback(self, callback: Callable[[ProcessStatus, str], None]) -> None:
        """
        设置状态回调函数
        
        Args:
            callback: 状态回调函数，接收状态和消息参数
        """
        self.status_callback = callback
    
    def start_process(self, command: list, task_name: str = "处理中") -> bool:
        """
        启动FFmpeg处理过程
        
        Args:
            command: FFmpeg命令列表
            task_name: 任务名称
            
        Returns:
            启动是否成功
        """
        if self.status == ProcessStatus.RUNNING:
            print("已有任务正在运行")
            return False
        
        try:
            self.current_task = task_name
            self.status = ProcessStatus.RUNNING
            self.error_message = ""
            self.progress = ProcessProgress()
            self._stop_event.clear()
            
            # 不使用-progress，直接从stderr读取进度信息
            command_with_progress = command.copy()
            # 移除可能存在的-nostats参数，我们需要stats来显示进度
            if "-nostats" in command_with_progress:
                command_with_progress.remove("-nostats")
            
            # 启动FFmpeg进程
            self.process = subprocess.Popen(
                command_with_progress,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 启动监控线程
            self._monitor_thread = threading.Thread(
                target=self._monitor_progress,
                daemon=True
            )
            self._monitor_thread.start()
            
            # 通知状态变化
            if self.status_callback:
                self.status_callback(self.status, f"开始{task_name}")
            
            return True
            
        except Exception as e:
            self.status = ProcessStatus.ERROR
            self.error_message = f"启动失败: {str(e)}"
            if self.status_callback:
                self.status_callback(self.status, self.error_message)
            return False
    
    def _monitor_progress(self) -> None:
        """监控处理进度"""
        if not self.process:
            return
        
        try:
            # 读取进度信息（从stderr）
            while self.process.poll() is None and not self._stop_event.is_set():
                if self.process.stderr:
                    line = self.process.stderr.readline()
                    if line:
                        line_stripped = line.strip()
                        self._parse_progress_line(line_stripped)
                
                # 检查是否需要停止
                if self._stop_event.is_set():
                    self._terminate_process()
                    break
                
                time.sleep(0.1)
            
            # 进程结束后的处理
            if not self._stop_event.is_set():
                return_code = self.process.returncode
                if return_code == 0:
                    self.status = ProcessStatus.COMPLETED
                    self.progress.percentage = 100.0
                    if self.status_callback:
                        self.status_callback(self.status, f"{self.current_task}完成")
                else:
                    self.status = ProcessStatus.ERROR
                    # 错误信息已在监控过程中收集，或使用返回码
                    if not self.error_message:
                        self.error_message = f"FFmpeg进程退出，返回码: {return_code}"
                    
                    if self.status_callback:
                        self.status_callback(self.status, f"{self.current_task}失败: {self.error_message}")
            
            # 最后一次进度回调
            if self.progress_callback:
                self.progress_callback(self.progress)
                
        except Exception as e:
            self.status = ProcessStatus.ERROR
            self.error_message = f"监控进程出错: {str(e)}"
            if self.status_callback:
                self.status_callback(self.status, self.error_message)
    
    def _parse_progress_line(self, line: str) -> None:
        """
        解析FFmpeg进度输出行
        
        Args:
            line: 输出行内容
        """
        try:
            # 检查是否是错误信息
            if any(error_keyword in line.lower() for error_keyword in ['error', 'failed', 'invalid', 'could not']):
                if not self.error_message:  # 只记录第一个错误
                    self.error_message = line
                return
            
            # FFmpeg进度输出格式示例:
            # frame=  123 fps= 25 q=28.0 size=    1024kB time=00:00:05.00 bitrate=1677.7kbits/s speed=1.23x
            
            # 只解析包含实际进度信息的行
            if not any(keyword in line for keyword in ['frame=', 'time=', 'size=', 'bitrate=']):
                return
            
            # 解析时间进度 - 处理N/A和正常时间格式
            if 'time=N/A' in line:
                # 时间未知，不更新时间
                pass
            else:
                time_match = re.search(r'time=(\d{1,2}:\d{2}:\d{2}(?:\.\d{2})?)', line)
                if time_match:
                    self.progress.time_processed = time_match.group(1)
                    # 确保时间格式标准化
                    if '.' not in self.progress.time_processed:
                        self.progress.time_processed += '.00'
            
            # 解析速度 - 处理N/A和正常速度
            if 'speed=N/A' in line:
                self.progress.speed = "N/A"
            else:
                speed_match = re.search(r'speed=\s*([0-9.]+)x', line)
                if speed_match:
                    self.progress.speed = f"{speed_match.group(1)}x"
            
            # 解析比特率 - 支持不同单位
            bitrate_match = re.search(r'bitrate=\s*([0-9.]+)(k?bits/s)', line)
            if bitrate_match:
                value = bitrate_match.group(1)
                unit = bitrate_match.group(2)
                self.progress.bitrate = f"{value} {unit}"
            
            # 解析帧率
            fps_match = re.search(r'fps=\s*([0-9.]+)', line)
            if fps_match:
                try:
                    self.progress.fps = float(fps_match.group(1))
                except ValueError:
                    pass
            
            # 解析当前帧数
            frame_match = re.search(r'frame=\s*(\d+)', line)
            if frame_match:
                try:
                    self.progress.current_frame = int(frame_match.group(1))
                except ValueError:
                    pass
            
            # 计算百分比（需要总时长信息）
            if (hasattr(self, '_total_duration_seconds') and 
                self._total_duration_seconds > 0 and 
                self.progress.time_processed):
                
                current_seconds = self._time_to_seconds(self.progress.time_processed)
                if current_seconds > 0:
                    self.progress.percentage = min(100.0, (current_seconds / self._total_duration_seconds) * 100.0)
                    
                    # 计算预计剩余时间
                    if self.progress.percentage > 0 and self.progress.speed:
                        try:
                            speed_value = float(self.progress.speed.replace('x', ''))
                            if speed_value > 0:
                                remaining_seconds = (self._total_duration_seconds - current_seconds) / speed_value
                                self.progress.eta = self._seconds_to_time(int(remaining_seconds))
                        except (ValueError, ZeroDivisionError):
                            pass
            
            # 触发进度回调（只在有实际进度更新时）
            if (self.progress_callback and 
                (self.progress.time_processed or self.progress.current_frame > 0)):
                self.progress_callback(self.progress)
                
        except Exception as e:
            # 不要因为解析错误而中断处理
            pass
    
    def _time_to_seconds(self, time_str: str) -> float:
        """
        将时间字符串转换为秒数
        
        Args:
            time_str: 时间字符串 (HH:MM:SS.ff)
            
        Returns:
            秒数
        """
        try:
            parts = time_str.split(':')
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0
    
    def _seconds_to_time(self, seconds: int) -> str:
        """
        将秒数转换为时间字符串
        
        Args:
            seconds: 秒数
            
        Returns:
            时间字符串 (HH:MM:SS)
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _extract_error_message(self, error_output: str) -> str:
        """
        从错误输出中提取有用的错误信息
        
        Args:
            error_output: 错误输出文本
            
        Returns:
            提取的错误信息
        """
        if not error_output:
            return "未知错误"
        
        # 常见错误模式
        error_patterns = [
            r"Error.*?:(.+)",
            r"Invalid.*?:(.+)",
            r"Could not.*?:(.+)",
            r"Failed.*?:(.+)",
            r"Unable.*?:(.+)"
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, error_output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配到特定模式，返回最后几行
        lines = error_output.strip().split('\n')
        if lines:
            return lines[-1]
        
        return "处理失败"
    
    def set_total_duration(self, duration_str: str) -> None:
        """
        设置总时长（用于计算进度百分比）
        
        Args:
            duration_str: 时长字符串 (HH:MM:SS.ff)
        """
        try:
            self._total_duration_seconds = self._time_to_seconds(duration_str)
        except:
            self._total_duration_seconds = 0
    
    def stop_process(self) -> bool:
        """
        停止当前处理
        
        Returns:
            停止是否成功
        """
        if self.status != ProcessStatus.RUNNING:
            return False
        
        try:
            self._stop_event.set()
            self.status = ProcessStatus.CANCELLED
            
            if self.status_callback:
                self.status_callback(self.status, f"{self.current_task}已取消")
            
            return True
            
        except Exception as e:
            print(f"停止进程失败: {e}")
            return False
    
    def _terminate_process(self) -> None:
        """强制终止进程"""
        if self.process:
            try:
                self.process.terminate()
                # 等待进程结束，如果超时则强制杀死
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            except Exception as e:
                print(f"终止进程失败: {e}")
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        等待处理完成
        
        Args:
            timeout: 超时时间（秒），None表示无超时
            
        Returns:
            是否在超时前完成
        """
        if self._monitor_thread:
            self._monitor_thread.join(timeout)
            return not self._monitor_thread.is_alive()
        return True
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        获取当前状态信息
        
        Returns:
            状态信息字典
        """
        return {
            "status": self.status.value,
            "task_name": self.current_task,
            "progress": {
                "percentage": self.progress.percentage,
                "time_processed": self.progress.time_processed,
                "speed": self.progress.speed,
                "bitrate": self.progress.bitrate,
                "fps": self.progress.fps,
                "eta": self.progress.eta,
                "current_frame": self.progress.current_frame,
                "total_frames": self.progress.total_frames
            },
            "error_message": self.error_message
        }
    
    def reset(self) -> None:
        """重置处理器状态"""
        if self.status == ProcessStatus.RUNNING:
            self.stop_process()
        
        self.status = ProcessStatus.IDLE
        self.progress = ProcessProgress()
        self.error_message = ""
        self.current_task = ""
        self.process = None
        if hasattr(self, '_total_duration_seconds'):
            delattr(self, '_total_duration_seconds')


class VideoProcessorManager:
    """视频处理器管理器 - 支持队列处理"""
    
    def __init__(self):
        self.processors: Dict[str, VideoProcessor] = {}
        self.active_processor: Optional[str] = None
    
    def create_processor(self, name: str) -> VideoProcessor:
        """
        创建新的处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            创建的处理器实例
        """
        processor = VideoProcessor()
        self.processors[name] = processor
        return processor
    
    def get_processor(self, name: str) -> Optional[VideoProcessor]:
        """
        获取指定的处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            处理器实例或None
        """
        return self.processors.get(name)
    
    def remove_processor(self, name: str) -> bool:
        """
        移除处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            移除是否成功
        """
        if name in self.processors:
            processor = self.processors[name]
            if processor.status == ProcessStatus.RUNNING:
                processor.stop_process()
            del self.processors[name]
            if self.active_processor == name:
                self.active_processor = None
            return True
        return False
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有处理器的状态
        
        Returns:
            所有处理器状态信息
        """
        return {
            name: processor.get_status_info()
            for name, processor in self.processors.items()
        }
