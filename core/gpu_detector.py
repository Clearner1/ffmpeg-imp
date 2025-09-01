"""
GPU检测模块
检测系统中可用的GPU并确定FFmpeg硬件加速支持
"""
import subprocess
import platform
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """GPU信息数据类"""
    name: str
    vendor: str  # nvidia, amd, intel
    memory: Optional[str] = None
    driver_version: Optional[str] = None


class GPUDetector:
    """GPU检测器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.available_gpus: List[GPUInfo] = []
        self.ffmpeg_gpu_support: Dict[str, bool] = {
            "cuda": False,
            "nvenc": False,
            "amf": False,
            "opencl": False,
            "dxva2": False,
            "d3d11va": False
        }
    
    def detect_gpus(self) -> List[GPUInfo]:
        """
        检测系统中的GPU
        
        Returns:
            GPU信息列表
        """
        self.available_gpus = []
        
        try:
            if self.system == "windows":
                self._detect_gpus_windows()
            elif self.system == "linux":
                self._detect_gpus_linux()
            else:
                print(f"不支持的操作系统: {self.system}")
        except Exception as e:
            print(f"GPU检测失败: {e}")
        
        return self.available_gpus
    
    def _detect_gpus_windows(self) -> None:
        """检测Windows系统中的GPU"""
        try:
            # 使用wmic命令检测显卡
            cmd = [
                "wmic", "path", "win32_VideoController",
                "get", "name,AdapterRAM,DriverVersion", "/format:csv"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 4:
                            # 修复: 在Windows wmic输出中，驱动名称可能包含实际的GPU名称
                            name = parts[2].strip()
                            memory = parts[1].strip() if parts[1].strip() else None
                            driver = parts[3].strip() if parts[3].strip() else None
                            
                            # 如果name不是真正的GPU名称，尝试从driver字段获取
                            if name and name != "Name":
                                # 检查name是否看起来像版本号而不是GPU名称
                                if name.replace('.', '').replace('_', '').isdigit():
                                    # name看起来像版本号，使用driver作为GPU名称
                                    if driver and any(keyword in driver.lower() for keyword in ['nvidia', 'geforce', 'radeon', 'amd', 'intel']):
                                        actual_name = driver
                                        vendor = self._get_vendor_from_name(driver)
                                    else:
                                        actual_name = name
                                        vendor = "unknown"
                                else:
                                    actual_name = name
                                    vendor = self._get_vendor_from_name(name)
                                
                                gpu_info = GPUInfo(
                                    name=actual_name,
                                    vendor=vendor,
                                    memory=self._format_memory(memory),
                                    driver_version=driver if driver != actual_name else None
                                )
                                self.available_gpus.append(gpu_info)
        except Exception as e:
            print(f"Windows GPU检测失败: {e}")
            # 备选方案：尝试检测NVIDIA和AMD GPU
            self._detect_nvidia_gpu_fallback()
            self._detect_amd_gpu_fallback()
    
    def _detect_gpus_linux(self) -> None:
        """检测Linux系统中的GPU"""
        try:
            # 使用lspci检测GPU
            result = subprocess.run(
                ["lspci", "-nn"], 
                capture_output=True, 
                text=True, 
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'VGA compatible controller' in line or 'Display controller' in line:
                        name = line.split(': ')[-1] if ': ' in line else line
                        vendor = self._get_vendor_from_name(name)
                        
                        gpu_info = GPUInfo(name=name, vendor=vendor)
                        self.available_gpus.append(gpu_info)
        except Exception as e:
            print(f"Linux GPU检测失败: {e}")
    
    def _detect_nvidia_gpu_fallback(self) -> None:
        """备选方案：检测NVIDIA GPU"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", 
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 3:
                            gpu_info = GPUInfo(
                                name=parts[0],
                                vendor="nvidia",
                                memory=f"{parts[1]} MB",
                                driver_version=parts[2]
                            )
                            self.available_gpus.append(gpu_info)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # nvidia-smi不可用
    
    def _detect_amd_gpu_fallback(self) -> None:
        """备选方案：检测AMD GPU"""
        try:
            # 在Windows上尝试检测AMD GPU
            if self.system == "windows":
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", 
                     "where", "name like '%AMD%' or name like '%Radeon%'",
                     "get", "name", "/format:list"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if line.startswith('Name=') and ('AMD' in line or 'Radeon' in line):
                            name = line.split('=', 1)[1].strip()
                            gpu_info = GPUInfo(name=name, vendor="amd")
                            self.available_gpus.append(gpu_info)
        except Exception:
            pass
    
    def _get_vendor_from_name(self, name: str) -> str:
        """从GPU名称推断厂商"""
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in ['nvidia', 'geforce', 'quadro', 'tesla']):
            return "nvidia"
        elif any(keyword in name_lower for keyword in ['amd', 'radeon', 'rx ', 'vega']):
            return "amd"
        elif any(keyword in name_lower for keyword in ['intel', 'uhd', 'iris']):
            return "intel"
        else:
            return "unknown"
    
    def _format_memory(self, memory_str: Optional[str]) -> Optional[str]:
        """格式化显存大小"""
        if not memory_str or memory_str == "":
            return None
        
        try:
            memory_bytes = int(memory_str)
            if memory_bytes > 0:
                memory_gb = memory_bytes / (1024 ** 3)
                return f"{memory_gb:.1f} GB"
        except (ValueError, TypeError):
            pass
        
        return memory_str
    
    def check_ffmpeg_gpu_support(self, ffmpeg_path: str) -> Dict[str, bool]:
        """
        检查FFmpeg的GPU加速支持
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
            
        Returns:
            各种GPU加速的支持情况
        """
        if not ffmpeg_path:
            return self.ffmpeg_gpu_support
        
        try:
            # 获取FFmpeg编译信息
            result = subprocess.run(
                [ffmpeg_path, "-hwaccels"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # 检查硬件加速器支持
                self.ffmpeg_gpu_support["cuda"] = "cuda" in output
                self.ffmpeg_gpu_support["opencl"] = "opencl" in output
                self.ffmpeg_gpu_support["dxva2"] = "dxva2" in output
                self.ffmpeg_gpu_support["d3d11va"] = "d3d11va" in output
            
            # 检查编码器支持
            result = subprocess.run(
                [ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # 检查NVIDIA编码器
                self.ffmpeg_gpu_support["nvenc"] = any(
                    encoder in output for encoder in 
                    ["h264_nvenc", "hevc_nvenc", "av1_nvenc"]
                )
                
                # 检查AMD编码器
                self.ffmpeg_gpu_support["amf"] = any(
                    encoder in output for encoder in 
                    ["h264_amf", "hevc_amf", "av1_amf"]
                )
        
        except Exception as e:
            print(f"FFmpeg GPU支持检查失败: {e}")
        
        return self.ffmpeg_gpu_support
    
    def get_recommended_gpu_mode(self) -> str:
        """
        根据检测结果推荐GPU模式
        
        Returns:
            推荐的GPU模式 (cuda, amd, cpu)
        """
        # 优先级：NVIDIA CUDA > AMD > CPU
        nvidia_gpus = [gpu for gpu in self.available_gpus if gpu.vendor == "nvidia"]
        amd_gpus = [gpu for gpu in self.available_gpus if gpu.vendor == "amd"]
        
        if nvidia_gpus and self.ffmpeg_gpu_support.get("cuda", False):
            return "cuda"
        elif amd_gpus and (self.ffmpeg_gpu_support.get("amf", False) or 
                          self.ffmpeg_gpu_support.get("opencl", False)):
            return "amd"
        else:
            return "cpu"
    
    def get_gpu_acceleration_args(self, mode: str) -> List[str]:
        """
        获取GPU加速参数
        
        Args:
            mode: GPU模式 (cuda, amd, cpu)
            
        Returns:
            FFmpeg参数列表
        """
        if mode == "cuda" and self.ffmpeg_gpu_support.get("cuda", False):
            return ["-hwaccel", "cuda"]
        elif mode == "amd":
            if self.ffmpeg_gpu_support.get("opencl", False):
                return ["-hwaccel", "opencl"]
            elif self.system == "windows" and self.ffmpeg_gpu_support.get("d3d11va", False):
                return ["-hwaccel", "d3d11va"]
        
        return []  # CPU模式或不支持GPU加速
    
    def get_gpu_encoder(self, mode: str, codec: str = "h264") -> Optional[str]:
        """
        获取GPU编码器名称
        
        Args:
            mode: GPU模式 (cuda, amd, cpu)
            codec: 编码格式 (h264, hevc)
            
        Returns:
            编码器名称
        """
        if mode == "cuda" and self.ffmpeg_gpu_support.get("nvenc", False):
            return f"{codec}_nvenc"
        elif mode == "amd" and self.ffmpeg_gpu_support.get("amf", False):
            return f"{codec}_amf"
        
        return None  # 使用软件编码器
    
    def get_gpu_summary(self) -> Dict[str, any]:
        """
        获取GPU检测摘要
        
        Returns:
            GPU信息摘要
        """
        return {
            "detected_gpus": [
                {
                    "name": gpu.name,
                    "vendor": gpu.vendor,
                    "memory": gpu.memory,
                    "driver_version": gpu.driver_version
                }
                for gpu in self.available_gpus
            ],
            "ffmpeg_support": self.ffmpeg_gpu_support,
            "recommended_mode": self.get_recommended_gpu_mode(),
            "system": self.system
        }
