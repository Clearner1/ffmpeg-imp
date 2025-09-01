#!/usr/bin/env python3
"""
FFmpeg视频处理工具
主程序入口

功能特性:
- 视频切片：支持精确时间裁剪，GPU加速
- 字幕烧录：将字幕文件嵌入到视频中
- 智能检测：自动检测FFmpeg和GPU支持情况
- 用户友好：图形化界面，实时进度显示

使用方法:
    python main.py

要求:
    - Python 3.7+
    - tkinter (通常随Python一起安装)
    - FFmpeg (需要单独安装)

作者: AI Assistant
版本: 1.0.0
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 确保可以导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True


def check_tkinter():
    """检查tkinter是否可用"""
    try:
        import tkinter
        return True
    except ImportError:
        print("错误: 未找到tkinter模块")
        print("请安装tkinter: pip install tk")
        return False


def check_dependencies():
    """检查所有依赖"""
    if not check_python_version():
        return False
    
    if not check_tkinter():
        return False
    
    return True


def show_welcome_message():
    """显示欢迎信息"""
    print("=" * 50)
    print("    FFmpeg视频处理工具 v1.0.0")
    print("=" * 50)
    print("")
    print("功能特性:")
    print("  • 视频切片 - 支持精确时间裁剪")
    print("  • 字幕烧录 - 将字幕嵌入视频")
    print("  • GPU加速 - 支持NVIDIA CUDA和AMD硬件加速")
    print("  • 智能检测 - 自动检测FFmpeg和GPU支持")
    print("")
    print("正在启动GUI界面...")
    print("")


def main():
    """主函数"""
    try:
        # 检查依赖
        if not check_dependencies():
            input("按Enter键退出...")
            return 1
        
        # 显示欢迎信息
        show_welcome_message()
        
        # 导入并启动GUI
        try:
            from gui.main_window import FFmpegGUI
            
            # 创建并运行应用
            app = FFmpegGUI()
            app.run()
            
            return 0
        
        except ImportError as e:
            print(f"导入错误: {e}")
            print("请确保所有项目文件都在正确位置")
            return 1
        
        except Exception as e:
            print(f"启动失败: {e}")
            
            # 如果GUI可用，显示错误对话框
            try:
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                messagebox.showerror("启动错误", f"程序启动失败:\n\n{str(e)}")
                root.destroy()
            except:
                pass  # 如果连对话框都显示不了，就算了
            
            return 1
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        return 0
    
    except Exception as e:
        print(f"意外错误: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
