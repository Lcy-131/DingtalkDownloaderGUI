# GoDingtalk GUI - 钉钉回放视频下载工具

## 项目简介

GoDingtalk GUI 是一个基于 Python tkinter 开发的图形界面工具，用于配合 GoDingtalk 命令行工具下载钉钉回放视频。本程序独立于 GoDingtalk 项目，需使用编译后的可执行文件才可运行。

**原项目链接**: [NAXG/GoDingtalk](https://github.com/NAXG/GoDingtalk)  
**可执行文件下载**: [Releases](https://github.com/NAXG/GoDingtalk/releases/)

---

## 功能特性 Features

### 🎯 核心功能
- **单视频下载**：支持单个视频URL下载
- **批量下载**：支持URL列表文件批量下载
- **智能检测**：自动检测并选择兼容的可执行文件
- **跨平台支持**：支持 Windows、macOS、Linux 系统
- **自动安装依赖**：程序会自动询问安装依赖，无需手动安装

### 🛠️ 高级功能
- **参数配置**：支持所有 GoDingtalk 命令行参数
- **进度跟踪**：实时显示下载进度和状态
- **日志管理**：支持日志复制和保存
- **高分屏适配**：自动适配高DPI显示器

## 系统要求

### 操作系统
- **Windows** 7/8/10/11 (推荐 Windows 10+)
- **macOS** 10.14+ (推荐 macOS 12+)
- **Linux** Ubuntu 18.04+, CentOS 7+, 其他主流发行版

### Python 环境
- **Python** 3.7+ (推荐 Python 3.9+)
- **pip**

### 依赖
```bash
# 依赖程序会自动询问安装，此处可以选择不安装

# 带 pip 的 Windows / macOS / Linux 系统上
pip install filetype pefile pyelftools macholib

# 不带 pip 或系统范围 shell 的 Linux 上

# apt 包管理器 (Ubuntu, Debian 等发行版)
sudo apt install python3-tk python3-filetype python3-pefile python3-pyelftools python3-macholib
# 或者
sudo apt install python3-tk python3-filetype python3-pefile python3-pyelftools python3-macholib

# dnt 包管理器 (CentOS, Fedora 等发行版)
sudo dnf install python3-tkinter python3-filetype python3-pefile python3-pyelftools
# 需要手动使用 pip 安装 macholib 库

# yum 包管理器 (CentOS, Fedora 等发行版)
sudo yum install python3-tkinter python3-filetype python3-pefile python3-pyelftools
# 需要手动使用 pip 安装 macholib 库
```

## 使用 Usage

### 1. 下载项目
```bash
git clone https://github.com/Lcy-131/DingtalkDownloaderGUI.git
cd GoDingtalk
```

### 2. 安装依赖

依赖程序会自动询问安装，此处可以选择不安装

### 3. 获取 GoDingtalk 可执行文件
从 [Releases](https://github.com/NAXG/GoDingtalk/releases/) 下载对应平台的可执行文件，放置在以下任一目录：

- 项目根目录（推荐）
- `src/` 目录
- `build/` 目录

或者放置在任意目录，但需要手动选择。

### 4. 运行程序
```bash
python DingtalkDownloaderGUI.py
```

## 界面说明

### 主界面布局

#### 1. 可执行文件选择区域（第一栏）
- **自动检测**：程序自动扫描并选择兼容的可执行文件
- **手动选择**：支持手动选择可执行文件
- **兼容性提示**：显示文件平台和架构兼容性状态

#### 2. 下载模式选择
- **单视频模式**：输入单个视频URL
- **批量模式**：选择URL列表文件（支持.txt、.dpl、.m3u、.m3u8格式）

#### 3. 参数配置区域
- **基本参数**：URL、保存目录、配置文件、Cookies文件
- **高级参数**：HTTP超时、Chrome超时、并发数等

#### 4. 控制区域
- **开始/停止**：控制下载过程
- **日志管理**：复制日志、保存日志文件
- **状态显示**：实时显示下载进度和状态

## 使用指南

### 单视频下载

1. 选择"单视频"模式
2. 在URL输入框中粘贴钉钉回放视频链接
3. 设置保存目录（可选，默认：`Videos/`）
4. 配置其他参数（可选）
5. 点击"开始下载"

### 批量下载

1. 选择"批量"模式
2. 点击"选择文件"选择URL列表文件
3. 程序自动设置保存目录为URL文件同级目录
4. 配置其他参数（可选）
5. 点击"开始下载"

### URL列表文件格式

支持以下格式的URL列表文件：

#### 文本文件 (.txt)
```
title1
title2
```

#### DPL播放列表 (.dpl)
```
DAUMPLAYLIST
...
1*file*title1.mp4
2*file*title2.mp4
```

#### M3U播放列表 (.m3u/.m3u8)
```
#EXTM3U
title1.mp4
title2.mp4
```

## 参数说明

### 基本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 视频URL | 单个视频的下载链接 | - |
| URL文件 | 批量下载的URL列表文件 | - |
| 保存目录 | 视频保存路径 | `Videos/` |
| Cookies文件 | 浏览器Cookies文件路径 | - |
| 配置文件 | GoDingtalk配置文件路径 | - |

### 高级参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| HTTP超时 | HTTP请求超时时间（秒） | 20 |
| Chrome超时 | Chrome浏览器超时时间（秒） | 30 |
| 并发数 | 同时下载的视频数量 | 10 |

## 可执行文件检测机制

### 检测优先级

程序按照以下优先级顺序检测可执行文件：

1. **项目根目录**（最高优先级）
2. **src/ 目录**
3. **build/ 目录**（最低优先级）

## 常见问题

### Q: 程序无法启动
**A:** 检查Python版本和依赖库是否安装正确：
```bash
python --version
pip list | grep filetype
```

### Q: 无法检测到可执行文件
**A:** 确保：
1. 可执行文件包含"GoDingtalk"关键字
2. 文件放置在正确目录（根目录/src/build）
3. 文件具有可执行权限（Linux/macOS）

### Q: 下载速度慢
**A:** 尝试：
1. 增加并发数
2. 检查网络连接
3. 调整超时参数

### Q: 视频无法播放
**A:** 可能原因：
1. 视频链接已失效
2. 需要有效的Cookies
3. 网络限制或地区限制

### Q: 程序在高分屏上显示模糊
**A:** 程序已支持高分屏适配，如果仍有问题：
1. 确保使用最新版本
2. 检查系统DPI设置
3. 重启程序

## 故障排除

### 日志分析
程序会生成详细的日志信息，可以帮助诊断问题：

- **INFO级别**：正常操作信息
- **WARNING级别**：警告信息，不影响运行
- **ERROR级别**：错误信息，需要处理

### 手动选择可执行文件
如果自动检测失败，可以手动选择：
1. 点击"选择可执行文件"按钮
2. 浏览并选择正确的可执行文件

### 参数调试
如果下载失败，可以尝试：
1. 增加超时时间
2. 减少并发数
3. 添加有效的Cookies文件

## 开发说明

### 项目结构
```
GoDingtalk/
├── DingtalkDownloaderGUI.py          # 主程序文件
├── executable_detector.py     # 可执行文件检测库
├── README_py.md              # 本文档
└-- [可执行文件放置目录]
    ├── GoDingtalk_*.exe      # Windows可执行文件
    ├── GoDingtalk_*          # Linux/macOS可执行文件
    └── ...
```

### 核心模块

#### DingtalkDownloaderGUI.py
- 主界面
- 参数配置和验证
- 下载过程控制

#### executable_detector.py
- 可执行文件检测
- 平台和架构兼容性验证
- 智能文件选择

### 扩展开发
如需扩展功能，可以修改：

1. **界面布局**：调整`create_widgets()`方法
2. **参数支持**：在`build_command()`方法中添加新参数
3. **文件检测**：修改`executable_detector.py`中的检测逻辑

## 版本历史

### v1.1.0 (Latest)
- [x] **跨平台支持**：Windows、macOS、Linux全平台兼容
- [x] **智能文件检测**：基于文件格式而非文件名的检测机制
- [x] **架构兼容性检测**：自动检测CPU架构匹配度
- [x] **高分屏适配**：自动适配高DPI显示器
- [x] **智能文件选择**：按兼容性和目录优先级自动选择最优文件
- [x] **完整参数支持**：支持所有GoDingtalk命令行参数
- [x] **进度跟踪和日志管理**：实时显示下载状态
- [x] **自动下载依赖**：自动安装缺失的依赖库

### v1.0.0
- [x] 基础GUI界面
- [x] Windows平台适配
- [x] 基本下载功能
- [x] 参数配置界面

## 注意事项

- 请确保有足够的磁盘空间存储视频文件
- 下载线程数不宜过高，建议 10-20 之间
- 首次使用需要登录钉钉账号
- 请勿用于商业用途或侵犯他人版权

## 免责声明

本工具仅供学习和研究目的，请勿用于非法用途。用户因使用本工具产生的一切后果，本项目开发者不承担任何责任。

下载的视频仅供个人学习使用，请勿传播或用于商业用途。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

---
