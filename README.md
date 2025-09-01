# FFmpeg视频处理工具

一个基于Python和tkinter的图形化FFmpeg视频处理工具，支持视频切片和字幕烧录功能，并提供GPU硬件加速支持。

## 功能特性

### 🎬 视频切片
- 精确的时间区间裁剪
- 支持多种视频格式 (MP4, AVI, MKV, MOV等)
- 可调节输出质量 (低/中/高)
- GPU硬件加速支持

### 📝 字幕烧录
- 支持多种字幕格式 (SRT, ASS, VTT等)
- 可自定义字体大小和颜色
- 字幕样式设置
- GPU硬件加速支持

### ⚡ GPU加速
- **NVIDIA CUDA**: 支持NVIDIA显卡硬件编码
- **AMD AMF/OpenCL**: 支持AMD显卡硬件编码  
- **智能检测**: 自动检测GPU支持情况
- **CPU后备**: 不支持GPU时自动使用CPU编码

### 🖥️ 用户界面
- 直观的图形化界面
- 实时处理进度显示
- 详细的日志输出
- 配置自动保存

## 系统要求

### 基本要求
- **Python**: 3.7 或更高版本
- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **FFmpeg**: 需要单独安装

### GPU加速要求 (可选)
- **NVIDIA GPU**: 
  - 支持CUDA的显卡
  - 安装最新NVIDIA驱动
  - FFmpeg需要CUDA支持编译
- **AMD GPU**:
  - 支持AMF的显卡 
  - 安装最新AMD驱动
  - FFmpeg需要AMF/OpenCL支持编译

## 安装说明

### 1. 克隆项目
```bash
git clone https://github.com/your-username/ffmpeg-imp.git
cd ffmpeg-imp
```

### 2. 安装Python依赖
```bash
# 项目主要使用Python标准库，通常无需额外安装依赖
# 如果缺少tkinter，根据系统安装:

# Windows: 重新安装Python时勾选"tcl/tk and IDLE"
# Ubuntu/Debian:
sudo apt-get install python3-tk

# CentOS/RHEL:
sudo yum install tkinter

# macOS: 通常已包含
```

### 3. 安装FFmpeg

#### Windows
1. 从 [FFmpeg官网](https://ffmpeg.org/download.html) 下载预编译版本
2. 解压到 `C:\\ffmpeg\\` 目录
3. 将 `C:\\ffmpeg\\bin` 添加到系统PATH环境变量

#### macOS
```bash
# 使用Homebrew
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### 4. GPU支持配置 (可选)

#### NVIDIA CUDA支持
```bash
# 下载支持CUDA的FFmpeg版本
# 或自己编译: ./configure --enable-cuda --enable-nvenc
```

#### AMD支持
```bash
# 下载支持AMF的FFmpeg版本  
# 或自己编译: ./configure --enable-amf --enable-opencl
```

## 使用方法

### 启动程序
```bash
python main.py
```

### 基本使用流程

1. **设置FFmpeg路径**
   - 点击"自动查找"让程序自动检测
   - 或手动选择FFmpeg可执行文件

2. **选择视频文件**
   - 点击"浏览"选择要处理的视频文件
   - 程序会自动显示视频信息

3. **选择处理模式**
   - **视频切片**: 输入开始和结束时间
   - **字幕烧录**: 选择字幕文件和样式设置

4. **GPU加速设置**
   - 点击"检测GPU支持"
   - 选择CUDA、AMD或CPU模式

5. **设置输出目录**
   - 选择处理后文件的保存位置

6. **开始处理**
   - 点击"开始处理"开始转换
   - 实时查看进度和日志

## 项目结构

```
ffmpeg-imp/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖配置
├── README.md              # 项目说明
├── config.json           # 配置文件(运行时生成)
├── gui/                  # GUI界面模块
│   ├── __init__.py
│   ├── main_window.py    # 主窗口
│   └── widgets.py        # 自定义控件
├── core/                 # 核心功能模块
│   ├── __init__.py
│   ├── ffmpeg_manager.py # FFmpeg管理
│   ├── gpu_detector.py   # GPU检测
│   └── video_processor.py# 视频处理
└── utils/                # 工具模块
    ├── __init__.py
    └── config.py         # 配置管理
```

## 配置说明

程序会自动创建 `config.json` 文件保存用户设置:

```json
{
    \"ffmpeg_path\": \"C:\\\\ffmpeg\\\\bin\\\\ffmpeg.exe\",
    \"default_gpu_mode\": \"cuda\",
    \"last_video_directory\": \"C:\\\\Users\\\\...\",
    \"last_output_directory\": \"C:\\\\Users\\\\...\",
    \"recent_files\": [...],
    \"window_geometry\": \"800x600+100+100\"
}
```

## 故障排除

### 常见问题

1. **找不到FFmpeg**
   - 确保FFmpeg已正确安装并添加到PATH
   - 或者手动指定FFmpeg可执行文件路径

2. **GPU加速不可用**
   - 检查显卡驱动是否最新
   - 确认FFmpeg版本支持对应的GPU编码器
   - 查看"检测GPU支持"的日志输出

3. **处理失败**
   - 检查输入文件是否损坏
   - 确认输出目录有写入权限
   - 查看详细日志了解错误信息

4. **界面显示异常**
   - 确认tkinter已正确安装
   - 尝试更新Python版本

### 性能优化建议

- 使用GPU加速可显著提升处理速度
- 对于大文件，建议选择"快速"预设
- 切片操作比重新编码速度更快
- SSD硬盘可提升IO性能

## 开发信息

- **语言**: Python 3.7+
- **GUI框架**: tkinter
- **架构**: 模块化设计，支持扩展
- **许可证**: MIT License

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone https://github.com/your-username/ffmpeg-imp.git
cd ffmpeg-imp

# 安装开发依赖
pip install pytest flake8 black

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8 .
```

## 更新日志

### v1.0.0 (2024-XX-XX)
- 初始版本发布
- 支持视频切片功能
- 支持字幕烧录功能
- GPU硬件加速支持
- 图形化用户界面

## 致谢

- [FFmpeg](https://ffmpeg.org/) - 强大的多媒体处理工具
- Python社区 - 优秀的开发生态

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
