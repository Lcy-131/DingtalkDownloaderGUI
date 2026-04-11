#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import sys
import platform
import threading
import time
from pathlib import Path

# 延迟导入ExecutableDetector，避免在导入阶段就失败
def import_executable_detector():
    """延迟导入ExecutableDetector"""
    try:
        from executable_detector import ExecutableDetector
        return ExecutableDetector
    except ImportError as e:
        # 如果导入失败，返回一个占位符类
        class PlaceholderDetector:
            def __init__(self):
                self.current_system = platform.system()
                self.current_arch = platform.machine()
            
            def scan_executable_directories(self, base_dir):
                return []
            
            def is_platform_compatible(self, filepath):
                return False
            
            def is_architecture_compatible(self, filepath):
                return False
            
            def validate_executable_by_type(self, filepath):
                return False
        
        return PlaceholderDetector

# 获取ExecutableDetector类（可能是真实的或占位符）
ExecutableDetector = import_executable_detector()

# 检测是否在高分屏环境下运行
if platform.system() == "Windows":
    try:
        import ctypes
        # 获取系统DPI缩放比例
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        # 获取屏幕DPI
        dpi = user32.GetDpiForSystem()
        # 计算缩放比例（相对于96 DPI）
        scaling_factor = dpi / 96.0
    except:
        scaling_factor = 1.0
else:
    scaling_factor = 1.0


class GoDingtalkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GoDingtalk - 钉钉回放视频下载工具")
        
        # 根据DPI缩放比例调整窗口大小
        base_width = 800
        base_height = 600
        scaled_width = int(base_width * scaling_factor)
        scaled_height = int(base_height * scaling_factor)
        self.root.geometry(f"{scaled_width}x{scaled_height}")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        self.set_icon()
        
        # 初始化可执行文件检测器
        self.detector = ExecutableDetector()
        
        # 初始化变量
        self.process = None
        self.is_running = False
        
        # 创建界面
        self.create_widgets()
        
        # 检查并安装缺失的依赖（在界面创建后）
        self.check_and_install_dependencies()
        
        # 自动检测可执行文件
        self.detect_executable()
    
    def set_icon(self):
        """设置窗口图标（如果可用）"""
        try:
            # 尝试设置图标（Windows）
            if platform.system() == "Windows":
                self.root.iconbitmap("")
        except:
            pass
    
    def clear_detection_message(self):
        """清除检测提示"""
        current_status = self.status_var.get()
        # 只有当当前状态仍然是检测提示或选择提示时才清除
        if "已检测到可执行文件" in current_status or "已选择可执行文件" in current_status:
            self.status_var.set("就绪")
    
    def check_and_install_dependencies(self):
        """检查并安装缺失的依赖"""
        # 从检测器模块获取缺失的依赖列表
        from executable_detector import MISSING_DEPENDENCIES
        
        if not MISSING_DEPENDENCIES:
            return  # 没有缺失的依赖
        
        # 构建依赖描述信息
        dependency_info = self._get_dependency_info()
        missing_deps_info = []
        
        for dep in MISSING_DEPENDENCIES:
            if dep in dependency_info:
                missing_deps_info.append(f"{dep}: {dependency_info[dep]}")
            else:
                missing_deps_info.append(dep)
        
        # 询问用户是否安装
        message = "检测到以下依赖库缺失：\n\n"
        message += "\n".join(missing_deps_info)
        message += "\n\n是否立即安装这些依赖库？"
        
        response = messagebox.askyesno(
            "缺失依赖库",
            message,
            parent=self.root
        )
        
        if response:
            # 用户选择安装
            self.install_dependencies(MISSING_DEPENDENCIES)
        else:
            # 用户选择不安装，显示警告
            messagebox.showwarning(
                "功能受限",
                "部分功能可能无法正常使用。\n您可以在需要时通过菜单手动安装依赖。",
                parent=self.root
            )
    
    def _get_dependency_info(self):
        """获取依赖库的详细信息"""
        return {
            "filetype": "文件类型检测库（必需）",
            "pefile": "Windows PE文件分析库（Windows系统需要）",
            "pyelftools": "Linux ELF文件分析库（Linux系统需要）",
            "macholib": "macOS Mach-O文件分析库（macOS系统需要）"
        }
    
    def install_dependencies(self, dependencies):
        """安装指定的依赖库"""
        import subprocess
        import sys
        
        # 创建安装进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("安装依赖库")
        progress_window.geometry("400x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 居中显示
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (200 // 2)
        progress_window.geometry(f"400x200+{x}+{y}")
        
        # 创建进度界面
        progress_label = ttk.Label(progress_window, text="正在安装依赖库...", font=("Arial", 10))
        progress_label.pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, length=300, mode='indeterminate')
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        status_label = ttk.Label(progress_window, text="", font=("Arial", 9))
        status_label.pack(pady=10)
        
        # 立即显示窗口
        progress_window.update()
        
        # 安装依赖
        success_deps = []
        failed_deps = []
        
        for i, dep in enumerate(dependencies, 1):
            status_label.config(text=f"正在安装 {dep} ({i}/{len(dependencies)})")
            progress_window.update()
            
            try:
                # 映射依赖名称到pip包名
                pip_name = self._map_dependency_to_pip(dep)
                
                # 使用pip安装
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", pip_name
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    success_deps.append(dep)
                else:
                    failed_deps.append((dep, result.stderr))
                    
            except subprocess.TimeoutExpired:
                failed_deps.append((dep, "安装超时"))
            except Exception as e:
                failed_deps.append((dep, str(e)))
        
        # 停止进度条
        progress_bar.stop()
        
        # 显示安装结果
        if failed_deps:
            error_message = "以下依赖安装失败：\n\n"
            for dep, error in failed_deps:
                error_message += f"{dep}: {error}\n"
            error_message += "\n请检查网络连接或手动安装。"
            
            messagebox.showerror("安装失败", error_message, parent=progress_window)
        else:
            messagebox.showinfo("安装成功", "所有依赖库已成功安装！", parent=progress_window)
        
        # 关闭进度窗口
        progress_window.destroy()
        
        # 如果有成功安装的依赖，重新启动检测器
        if success_deps:
            # 重新加载依赖模块
            from executable_detector import reload_dependencies
            reload_dependencies()
            
            # 重新初始化检测器
            from executable_detector import ExecutableDetector
            self.detector = ExecutableDetector()
            self.detect_executable()
    
    def _map_dependency_to_pip(self, dep):
        """将依赖名称映射到pip包名"""
        mapping = {
            "filetype": "filetype",
            "pefile": "pefile",
            "pyelftools": "pyelftools",
            "macholib": "macholib"
        }
        return mapping.get(dep, dep)
    
    def select_executable(self):
        """手动选择可执行文件"""
        # 根据操作系统选择文件类型
        system = platform.system()
        if system == "Windows":
            filetypes = [("可执行文件", "*.exe"), ("所有文件", "*.*")]
        else:
            filetypes = [("可执行文件", "*"), ("所有文件", "*.*")]
        
        filename = filedialog.askopenfilename(
            title="选择GoDingtalk可执行文件",
            filetypes=filetypes
        )
        
        if filename:
            # 规范化路径格式（Windows下将/转换为\\）
            filename = os.path.normpath(filename)
            
            # 验证文件是否是可执行文件
            if self.validate_executable_by_type(filename):
                # 检查平台兼容性
                if self.is_platform_compatible(filename):
                    # 检查架构兼容性
                    if self.is_architecture_compatible(filename):
                        self.executable_path = filename
                        self.exe_path_var.set(os.path.basename(filename))
                        self.exe_status_var.set("✅ 已手动选择兼容的可执行文件")
                    else:
                        self.executable_path = filename
                        self.exe_path_var.set(os.path.basename(filename))
                        self.exe_status_var.set("⚠️  已手动选择可执行文件 (架构可能不兼容)")
                    # 5秒后清除选择提示
                    self.root.after(5000, self.clear_detection_message)
                else:
                    messagebox.showerror("错误", "选择的文件平台不兼容，请选择与当前系统匹配的可执行文件")
            else:
                messagebox.showerror("错误", "选择的文件不是有效的可执行文件")
    
    def validate_executable(self, filepath):
        """验证文件是否为有效的GoDingtalk可执行文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(filepath):
                return False
            
            # 检查文件名是否包含GoDingtalk
            filename = os.path.basename(filepath).lower()
            if "godingtalk" not in filename:
                return False
            
            # 使用filetype库检测文件真实类型
            kind = filetype.guess(filepath)
            if kind is None:
                # 如果filetype无法识别，可能是跨平台编译的文件
                # 检查文件大小作为备用验证
                file_size = os.path.getsize(filepath)
                if file_size < 1024 * 1024:  # 小于1MB
                    return False
                # 对于无法识别的文件，放宽验证条件
                return True
            
            # 根据操作系统检查MIME类型和扩展名（基于实际检测结果）
            system = platform.system()
            if system == "Windows":
                # Windows可执行文件: PE格式
                if kind.mime != "application/x-msdownload" or kind.extension != "exe":
                    return False
            elif system == "Darwin":
                # macOS可执行文件: 放宽验证条件
                # 由于跨平台编译，filetype可能无法识别Mach-O格式
                # 主要依赖文件大小和文件名验证
                pass
            elif system == "Linux":
                # Linux可执行文件: ELF格式
                if kind.mime != "application/x-executable" or kind.extension != "elf":
                    return False
            
            # 检查文件大小（GoDingtalk可执行文件通常大于1MB）
            file_size = os.path.getsize(filepath)
            if file_size < 1024 * 1024:  # 小于1MB
                return False
                
            return True
            
        except Exception as e:
            print(f"文件验证错误: {e}")
            return False
    
    def detect_executable(self):
        """自动检测可执行文件"""
        current_dir = Path(__file__).parent
        
        # 使用检测器库按照优先级顺序扫描目录
        platform_compatible_executables = self.detector.scan_executable_directories(current_dir)
        
        # 只选择平台兼容的文件
        if platform_compatible_executables:
            selected_executable = platform_compatible_executables[0]
            self.executable_path = selected_executable
            # 更新可执行文件选择区域
            self.exe_path_var.set(os.path.basename(self.executable_path))
            
            # 检查选择的文件是否架构兼容
            if self.is_architecture_compatible(selected_executable):
                self.exe_status_var.set(f"✅ 已自动选择兼容的可执行文件")
            else:
                self.exe_status_var.set(f"⚠️  已自动选择可执行文件 (架构可能不兼容)")
        else:
            self.executable_path = None
            self.exe_path_var.set("")
            self.exe_status_var.set("❌ 未找到可执行文件，请手动选择")
            return
        
        # 5秒后自动清除检测提示
        self.root.after(5000, self.clear_detection_message)
    
    def detect_executable_format(self, filepath):
        """通过魔数判断文件格式"""
        try:
            with open(filepath, 'rb') as f:
                magic = f.read(4)
            
            if magic.startswith(b'\x7fELF'):
                return 'ELF'
            elif magic.startswith(b'MZ'):
                return 'PE'
            elif magic.startswith(b'\xfe\xed\xfa') or magic.startswith(b'\xce\xfa\xed\xfe') or magic.startswith(b'\xcf\xfa\xed\xfe') or magic.startswith(b'\xfe\xed\xfa\xcf'):
                return 'Mach-O'
            else:
                return 'Unknown'
        except Exception as e:
            return f'Error: {e}'
    
    def get_file_architecture(self, filepath):
        """获取可执行文件的真实架构信息"""
        try:
            fmt = self.detect_executable_format(filepath)
            
            if fmt == 'PE':
                # Windows PE文件
                pe = pefile.PE(filepath)
                machine = pe.FILE_HEADER.Machine
                
                # PE文件机器类型映射
                if machine == 0x014c:          # IMAGE_FILE_MACHINE_I386
                    return 'x86'
                elif machine == 0x8664:       # IMAGE_FILE_MACHINE_AMD64
                    return 'x86_64'
                elif machine == 0x01c0:       # IMAGE_FILE_MACHINE_ARM
                    return 'arm'
                elif machine == 0xaa64:       # IMAGE_FILE_MACHINE_ARM64
                    return 'arm64'
                else:
                    return f'unknown_pe_{machine:04x}'
                    
            elif fmt == 'ELF':
                # Linux ELF文件
                with open(filepath, 'rb') as f:
                    elf = ELFFile(f)
                    machine = elf['e_machine']
                
                # ELF机器类型映射
                if machine == 'EM_386':        # 3
                    return 'x86'
                elif machine == 'EM_X86_64':  # 62
                    return 'x86_64'
                elif machine == 'EM_ARM':     # 40
                    return 'arm'
                elif machine == 'EM_AARCH64':  # 183
                    return 'arm64'
                else:
                    return f'unknown_elf_{machine}'
                    
            elif fmt == 'Mach-O':
                # macOS Mach-O文件
                macho = MachO(filepath)
                if not macho.headers:
                    return 'no_macho_headers'
                
                # 获取第一个header的架构信息
                header = macho.headers[0].header
                cputype = header.cputype
                
                # Mach-O CPU类型映射
                if cputype == 0x00000007:      # CPU_TYPE_X86
                    return 'x86'
                elif cputype == 0x01000007:   # CPU_TYPE_X86_64
                    return 'x86_64'
                elif cputype == 0x0000000c:   # CPU_TYPE_ARM
                    return 'arm'
                elif cputype == 0x0100000c:   # CPU_TYPE_ARM64
                    return 'arm64'
                else:
                    return f'unknown_macho_{cputype:08x}'
                    
            else:
                return 'unknown_format'
                
        except Exception as e:
            return f'error_{str(e).replace(" ", "_")}'
    
    def is_architecture_compatible(self, filepath):
        """检查文件架构是否与当前系统兼容（基于真实二进制分析）"""
        return self.detector.is_architecture_compatible(filepath)
    
    def is_platform_compatible(self, filepath):
        """检查文件平台是否与当前系统兼容"""
        return self.detector.is_platform_compatible(filepath)
    
    def _fallback_architecture_check(self, filepath, current_arch):
        """后备架构检查（基于文件名分析）"""
        try:
            filename = os.path.basename(filepath).lower()
            
            # 从文件名分析架构信息
            if "amd64" in filename or "x86_64" in filename:
                return "amd64" in current_arch or "x86_64" in current_arch
            elif "arm64" in filename or "aarch64" in filename:
                return "arm64" in current_arch or "aarch64" in current_arch
            elif "386" in filename or "i386" in filename or "x86" in filename:
                # Windows AMD64可以运行x86程序
                if platform.system() == "Windows" and "amd64" in current_arch:
                    return True
                return "i386" in current_arch or "x86" in current_arch
            elif "arm" in filename:
                return "arm" in current_arch
            
            # 如果无法从文件名确定架构，返回True（放宽验证）
            return True
            
        except Exception as e:
            print(f"后备架构检查错误: {e}")
            return True  # 最终后备：放宽验证
    
    def validate_executable_by_type(self, filepath):
        """通过文件类型验证可执行文件"""
        return self.detector.validate_executable_by_type(filepath)
    
    def create_widgets(self):
        """创建界面组件"""
        # 根据DPI缩放比例调整字体和间距
        base_font_size = 9
        title_font_size = 16
        small_font_size = 8
        base_padding = 10
        
        scaled_font_size = int(base_font_size * scaling_factor)
        scaled_title_font_size = int(title_font_size * scaling_factor)
        scaled_small_font_size = int(small_font_size * scaling_factor)
        scaled_padding = int(base_padding * scaling_factor)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=f"{scaled_padding}")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="GoDingtalk 下载工具", 
                               font=("Arial", scaled_title_font_size, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, int(20 * scaling_factor)))
        
        # 可执行文件选择区域（移动到第一栏）
        exe_frame = ttk.LabelFrame(main_frame, text="可执行文件选择", padding="10")
        exe_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        exe_frame.columnconfigure(1, weight=1)
        
        # 可执行文件路径显示和选择
        ttk.Label(exe_frame, text="可执行文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.exe_path_var = tk.StringVar(value="")
        self.exe_path_entry = ttk.Entry(exe_frame, textvariable=self.exe_path_var, state="readonly")
        self.exe_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.select_exe_btn = ttk.Button(exe_frame, text="选择文件", command=self.select_executable)
        self.select_exe_btn.grid(row=0, column=2, padx=(5, 0))
        
        # 可执行文件状态显示
        self.exe_status_var = tk.StringVar(value="未选择")
        exe_status_label = ttk.Label(exe_frame, textvariable=self.exe_status_var, font=("Arial", 9))
        exe_status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 下载模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="下载模式", padding="10")
        mode_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        mode_frame.columnconfigure(1, weight=1)
        
        self.mode_var = tk.StringVar(value="single")
        
        ttk.Radiobutton(mode_frame, text="单视频下载", variable=self.mode_var, 
                       value="single", command=self.toggle_mode).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="批量下载", variable=self.mode_var, 
                       value="batch", command=self.toggle_mode).grid(row=0, column=1, sticky=tk.W)
        
        # 单视频下载区域
        self.single_frame = ttk.Frame(main_frame)
        self.single_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.single_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.single_frame, text="视频URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_entry = ttk.Entry(self.single_frame, width=60)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 批量下载区域
        self.batch_frame = ttk.Frame(main_frame)
        self.batch_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.batch_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.batch_frame, text="URL文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_entry = ttk.Entry(self.batch_frame, width=50)
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(self.batch_frame, text="浏览", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # 初始隐藏批量下载区域
        self.batch_frame.grid_remove()
        
        # 参数设置 - 采用两列布局
        param_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        param_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 配置列权重，让两列平衡
        param_frame.columnconfigure(0, weight=1)
        param_frame.columnconfigure(1, weight=1)
        param_frame.columnconfigure(2, minsize=80)  # 浏览按钮列
        param_frame.columnconfigure(3, weight=1)
        param_frame.columnconfigure(4, weight=1)
        param_frame.columnconfigure(5, minsize=80)  # 浏览按钮列
        
        # 第一列（左侧）
        # 第一行：下载线程数
        ttk.Label(param_frame, text="下载线程数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.thread_var = tk.StringVar(value="10")
        thread_spin = ttk.Spinbox(param_frame, from_=1, to=100, textvariable=self.thread_var, width=12)
        thread_spin.grid(row=0, column=1, sticky=tk.W)
        
        # 第二行：保存目录
        ttk.Label(param_frame, text="保存目录:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        # 根据操作系统设置默认保存目录格式
        if platform.system() == "Windows":
            default_save_dir = "Videos\\"
        else:
            default_save_dir = "Videos/"
        self.save_dir_var = tk.StringVar(value=default_save_dir)
        save_dir_entry = ttk.Entry(param_frame, textvariable=self.save_dir_var)
        save_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        browse_dir_btn = ttk.Button(param_frame, text="浏览", command=self.browse_directory)
        browse_dir_btn.grid(row=1, column=2, padx=(5, 0))
        
        # 第三行：Cookies文件
        ttk.Label(param_frame, text="Cookies文件:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.cookies_file_var = tk.StringVar(value="")
        cookies_file_entry = ttk.Entry(param_frame, textvariable=self.cookies_file_var)
        cookies_file_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        browse_cookies_btn = ttk.Button(param_frame, text="浏览", command=self.browse_cookies_file)
        browse_cookies_btn.grid(row=2, column=2, padx=(5, 0))
        
        # 第四行：配置文件
        ttk.Label(param_frame, text="配置文件:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.config_file_var = tk.StringVar(value="")
        config_file_entry = ttk.Entry(param_frame, textvariable=self.config_file_var)
        config_file_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))
        
        browse_config_btn = ttk.Button(param_frame, text="浏览", command=self.browse_config_file)
        browse_config_btn.grid(row=3, column=2, padx=(5, 0))
        
        # 第二列（右侧）
        # 第一行：HTTP超时
        ttk.Label(param_frame, text="HTTP超时(秒):").grid(row=0, column=3, sticky=tk.W, padx=(20, 5))
        self.http_timeout_var = tk.StringVar(value="30")
        http_timeout_spin = ttk.Spinbox(param_frame, from_=10, to=300, textvariable=self.http_timeout_var, width=12)
        http_timeout_spin.grid(row=0, column=4, sticky=tk.W)
        
        # 第二行：Chrome超时
        ttk.Label(param_frame, text="Chrome超时(分):").grid(row=1, column=3, sticky=tk.W, padx=(20, 5))
        self.chrome_timeout_var = tk.StringVar(value="20")
        chrome_timeout_spin = ttk.Spinbox(param_frame, from_=5, to=60, textvariable=self.chrome_timeout_var, width=12)
        chrome_timeout_spin.grid(row=1, column=4, sticky=tk.W)
        
        # 第三行：视频列表文件（放在第二列）
        ttk.Label(param_frame, text="视频列表文件:").grid(row=2, column=3, sticky=tk.W, padx=(20, 5))
        self.video_list_var = tk.StringVar(value="")
        video_list_entry = ttk.Entry(param_frame, textvariable=self.video_list_var)
        video_list_entry.grid(row=2, column=4, sticky=(tk.W, tk.E))
        
        browse_video_list_btn = ttk.Button(param_frame, text="浏览", command=self.browse_video_list_file)
        browse_video_list_btn.grid(row=2, column=5, padx=(5, 0))
        
        # 第四行：强制重新登录
        self.force_login_var = tk.BooleanVar(value=False)
        force_login_check = ttk.Checkbutton(param_frame, text="强制重新登录", variable=self.force_login_var)
        force_login_check.grid(row=3, column=3, columnspan=3, sticky=tk.W, padx=(20, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        
        # 配置按钮区域的列权重
        button_frame.columnconfigure(0, weight=0)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        button_frame.columnconfigure(3, weight=0)
        button_frame.columnconfigure(4, weight=0)
        button_frame.columnconfigure(5, weight=1)  # 最后一个按钮占据剩余空间
        
        self.start_btn = ttk.Button(button_frame, text="开始下载", command=self.start_download)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="停止下载", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="清空日志", command=self.clear_log)
        clear_btn.grid(row=0, column=2, padx=(0, 10))
        
        copy_log_btn = ttk.Button(button_frame, text="复制日志", command=self.copy_log)
        copy_log_btn.grid(row=0, column=3, padx=(0, 10))
        
        save_log_btn = ttk.Button(button_frame, text="保存日志", command=self.save_log)
        save_log_btn.grid(row=0, column=4)
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="下载日志", padding="10")
        log_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # 配置状态栏的列权重
        status_frame.columnconfigure(0, weight=0)  # 视频序号标签
        status_frame.columnconfigure(1, weight=0)  # 状态标签
        status_frame.columnconfigure(2, weight=1)  # 进度条（占据剩余空间）
        status_frame.columnconfigure(3, weight=0)  # 进度标签
        
        # 视频序号标签（左下角小字）
        self.video_index_var = tk.StringVar(value="")
        video_index_label = ttk.Label(status_frame, textvariable=self.video_index_var, font=("Arial", 8))
        video_index_label.grid(row=0, column=0, sticky=tk.W)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(status_frame, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(10, 5))
        
        # 进度标签
        self.progress_label = ttk.Label(status_frame, text="0.00%")
        self.progress_label.grid(row=0, column=3, sticky=tk.E)
    
    def toggle_mode(self):
        """切换下载模式"""
        if self.mode_var.get() == "single":
            self.single_frame.grid()
            self.batch_frame.grid_remove()
        else:
            self.single_frame.grid_remove()
            self.batch_frame.grid()
    
    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择URL文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            # 规范化路径格式（Windows下将/转换为\\）
            filename = os.path.normpath(filename)
            
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            
            # 自动设置保存目录为URL文件所在文件夹
            url_file_dir = os.path.dirname(filename)
            current_save_dir = self.save_dir_var.get().strip()
            
            # 规范化路径格式
            url_file_dir = os.path.normpath(url_file_dir)
            # 规范化当前保存目录
            current_save_dir = os.path.normpath(current_save_dir)
            
            # 根据操作系统设置默认目录路径用于比较
            if platform.system() == "Windows":
                default_save_dir_norm = "Videos\\"
            else:
                default_save_dir_norm = "Videos/"
            
            # 如果当前保存目录不是URL文件所在目录，询问用户是否切换
            if current_save_dir != url_file_dir and current_save_dir != default_save_dir_norm:
                response = messagebox.askyesno(
                    "自动设置保存目录",
                    f"检测到URL文件在目录: {url_file_dir}\n"
                    f"当前保存目录: {current_save_dir}\n\n"
                    "是否将保存目录自动设置为URL文件所在目录？\n"
                    "（选择'否'将保持当前目录）"
                )
                if response:
                    self.save_dir_var.set(url_file_dir)
            elif current_save_dir == default_save_dir_norm:
                # 如果使用默认目录，直接设置为URL文件所在目录
                self.save_dir_var.set(url_file_dir)
    
    def browse_directory(self):
        """浏览目录"""
        directory = filedialog.askdirectory(title="选择保存目录")
        if directory:
            # 规范化路径格式（Windows下将/转换为\\）
            directory = os.path.normpath(directory)
            self.save_dir_var.set(directory)
    
    def browse_cookies_file(self):
        """浏览Cookies文件"""
        filename = filedialog.askopenfilename(
            title="选择Cookies文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            # 规范化路径格式（Windows下将/转换为\\）
            filename = os.path.normpath(filename)
            self.cookies_file_var.set(filename)
    
    def browse_video_list_file(self):
        """浏览视频列表文件"""
        filename = filedialog.asksaveasfilename(
            title="选择或创建视频列表文件",
            filetypes=[
                ("DPL播放列表", "*.dpl"),
                ("M3U播放列表", "*.m3u"),
                ("M3U8播放列表", "*.m3u8"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ],
            defaultextension=".dpl"
        )
        if filename:
            self.video_list_var.set(filename)
    
    def browse_config_file(self):
        """浏览配置文件"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            # 规范化路径格式（Windows下将/转换为\\）
            filename = os.path.normpath(filename)
            self.config_file_var.set(filename)
    
    def log_message(self, message):
        """在日志区域显示消息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def copy_log(self):
        """复制日志到剪贴板"""
        try:
            # 获取所有日志内容
            log_content = self.log_text.get(1.0, tk.END)
            if log_content.strip():
                # 复制到剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(log_content)
                self.log_message("日志已复制到剪贴板")
                self.status_var.set("日志已复制")
            else:
                self.log_message("日志为空，无需复制")
                self.status_var.set("日志为空")
        except Exception as e:
            self.log_message(f"复制日志失败: {str(e)}")
            self.status_var.set("复制失败")
    
    def save_log(self):
        """保存日志到文件"""
        try:
            # 获取所有日志内容
            log_content = self.log_text.get(1.0, tk.END)
            if not log_content.strip():
                self.log_message("日志为空，无需保存")
                self.status_var.set("日志为空")
                return
            
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if filename:
                # 保存文件
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                self.log_message(f"日志已保存到: {filename}")
                self.status_var.set("日志已保存")
                
        except Exception as e:
            self.log_message(f"保存日志失败: {str(e)}")
            self.status_var.set("保存失败")
    
    def parse_progress(self, line):
        """解析进度信息"""
        try:
            # 查找进度百分比
            if "Progress:" in line and "%" in line:
                # 提取百分比数字
                import re
                # 匹配格式: Progress:[...] 12.34% Completed:[...]
                match = re.search(r'(\d+\.\d+)%', line)
                if match:
                    progress = float(match.group(1))
                    # 更新进度条和标签
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"{progress:.2f}%")
                    return True
            
            # 查找完成数量信息
            elif "Completed:" in line and "Total:" in line:
                # 匹配格式: Completed:[ 15] Total:[158]
                match_completed = re.search(r'Completed:\s*\[\s*(\d+)\]', line)
                match_total = re.search(r'Total:\s*\[\s*(\d+)\]', line)
                
                if match_completed and match_total:
                    completed = int(match_completed.group(1))
                    total = int(match_total.group(1))
                    
                    if total > 0:
                        progress = (completed / total) * 100
                        # 更新进度条和标签
                        self.progress_var.set(progress)
                        self.progress_label.config(text=f"{progress:.2f}% ({completed}/{total})")
                        return True
            
            # 解析视频序号（处理URL的行）
            elif "处理 URL:" in line or re.search(r'\[\d+\] 处理 URL:', line):
                import re
                # 匹配格式: [1] 处理 URL: `https://...`
                match_index = re.search(r'\[(\d+)\]', line)
                if match_index:
                    current_index = int(match_index.group(1))
                    # 查找总视频数（从之前的日志中获取）
                    total_videos = self.get_total_videos_from_log()
                    if total_videos > 0:
                        self.video_index_var.set(f"正在下载第 {current_index}/{total_videos} 个视频")
                    else:
                        self.video_index_var.set(f"正在下载第 {current_index} 个视频")
                    return True
            
            # 下载完成时重置进度和视频序号
            elif "下载完成" in line or "下载失败" in line or "下载已停止" in line:
                self.progress_var.set(100.0)
                self.progress_label.config(text="100.00%")
                self.video_index_var.set("")
                return True
                
        except Exception as e:
            # 解析失败不影响主要功能
            pass
        
        return False
    
    def get_total_videos_from_log(self):
        """从日志中获取总视频数"""
        try:
            # 获取当前日志内容
            log_content = self.log_text.get(1.0, tk.END)
            import re
            # 查找批量下载的总数信息
            match = re.search(r'批量下载.*?(\d+).*?个视频', log_content)
            if match:
                return int(match.group(1))
            
            # 查找URL文件中的行数
            if self.mode_var.get() == "batch" and self.file_entry.get():
                try:
                    with open(self.file_entry.get(), 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 统计非空行和非注释行
                        count = 0
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                count += 1
                        return count
                except:
                    pass
            
            # 单视频下载
            if self.mode_var.get() == "single" and self.url_entry.get():
                return 1
                
        except:
            pass
        
        return 0
    
    def start_download(self):
        """开始下载"""
        if not self.executable_path:
            messagebox.showerror("错误", "未找到GoDingtalk可执行文件！")
            return
        
        if self.is_running:
            messagebox.showwarning("警告", "下载任务正在进行中！")
            return
        
        # 验证输入
        if self.mode_var.get() == "single":
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入视频URL！")
                return
            if not url.startswith("http"):
                messagebox.showerror("错误", "请输入有效的URL！")
                return
        else:
            file_path = self.file_entry.get().strip()
            if not file_path:
                messagebox.showerror("错误", "请选择URL文件！")
                return
            if not os.path.exists(file_path):
                messagebox.showerror("错误", "URL文件不存在！")
                return
        
        # 创建保存目录
        save_dir = self.save_dir_var.get().strip()
        if save_dir:
            try:
                os.makedirs(save_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建保存目录: {e}")
                return
        
        # 开始下载线程
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # 重置状态栏、进度条和视频序号
        self.status_var.set("就绪")
        self.progress_var.set(0.0)
        self.progress_label.config(text="0.00%")
        self.video_index_var.set("")
        
        thread = threading.Thread(target=self.run_download)
        thread.daemon = True
        thread.start()
    
    def stop_download(self, user_stopped=True):
        """停止下载
        
        Args:
            user_stopped: 是否为用户主动停止（True）还是下载完成（False）
        """
        if self.process and self.is_running and user_stopped:
            try:
                self.process.terminate()
                self.log_message("下载任务已停止")
            except:
                pass
        
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        # 停止时保持当前进度
        if user_stopped:
            self.status_var.set("下载已停止")
        # 下载完成时状态已经在run_download中设置
    
    def run_download(self):
        """运行下载任务"""
        try:
            # 构建命令
            cmd = [self.executable_path]
            
            # 添加参数
            cmd.append(f"-thread={self.thread_var.get()}")
            
            # 添加HTTP超时参数
            http_timeout = self.http_timeout_var.get().strip()
            if http_timeout and http_timeout != "30":
                cmd.append(f"-httpTimeout={http_timeout}")
            
            # 添加Chrome超时参数
            chrome_timeout = self.chrome_timeout_var.get().strip()
            if chrome_timeout and chrome_timeout != "20":
                cmd.append(f"-chromeTimeout={chrome_timeout}")
            
            # 添加保存目录参数
            save_dir = self.save_dir_var.get().strip()
            # 根据操作系统设置默认目录路径
            if platform.system() == "Windows":
                default_save_dir = "Videos\\"
            else:
                default_save_dir = "Videos/"
            if save_dir and save_dir != default_save_dir:
                # 确保路径格式正确
                normalized_save_dir = os.path.normpath(save_dir)
                cmd.append(f"-saveDir={normalized_save_dir}")
            
            # 添加Cookies文件参数
            cookies_file = self.cookies_file_var.get().strip()
            if cookies_file:
                cmd.append(f"-cookies={cookies_file}")
            
            # 添加强制登录参数
            if self.force_login_var.get():
                cmd.append("-login")
            
            # 添加视频列表文件参数
            video_list_file = self.video_list_var.get().strip()
            if video_list_file:
                cmd.append(f"-videoList={video_list_file}")
            
            # 添加配置文件参数
            config_file = self.config_file_var.get().strip()
            if config_file:
                cmd.append(f"-config={config_file}")
            
            if self.mode_var.get() == "single":
                cmd.append(f"-url={self.url_entry.get()}")
                self.log_message(f"开始下载单个视频: {self.url_entry.get()}")
            else:
                cmd.append(f"-urlFile={self.file_entry.get()}")
                self.log_message(f"开始批量下载，URL文件: {self.file_entry.get()}")
            
            self.log_message(f"执行命令: {' '.join(cmd)}")
            self.log_message(f"保存目录: {save_dir}")
            self.log_message(f"HTTP超时: {http_timeout}秒")
            self.log_message(f"Chrome超时: {chrome_timeout}分钟")
            if video_list_file:
                self.log_message(f"视频列表文件: {video_list_file}")
            
            # 运行进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                encoding='utf-8',
                errors='replace'  # 用?替换无法解码的字符
            )
            
            # 实时读取输出
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running:
                    break
                if line.strip():
                    # 清理输出中的特殊字符
                    cleaned_line = line.strip().replace('\x00', '').replace('\r', '')
                    # 显示日志
                    self.root.after(0, self.log_message, cleaned_line)
                    # 解析进度信息
                    self.root.after(0, self.parse_progress, cleaned_line)
            
            # 等待进程结束
            return_code = self.process.wait()
            
            if self.is_running:
                if return_code == 0:
                    self.root.after(0, self.log_message, "下载完成！")
                    self.root.after(0, lambda: self.status_var.set("下载完成"))
                else:
                    self.root.after(0, self.log_message, f"下载失败，返回码: {return_code}")
                    self.root.after(0, lambda: self.status_var.set("下载失败"))
            
        except UnicodeDecodeError as e:
            # 处理编码错误
            self.root.after(0, self.log_message, f"编码错误，尝试使用GBK解码...")
            try:
                # 重新运行进程，使用GBK编码
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    encoding='gbk',
                    errors='replace'
                )
                
                for line in iter(self.process.stdout.readline, ''):
                    if not self.is_running:
                        break
                    if line.strip():
                        cleaned_line = line.strip().replace('\x00', '').replace('\r', '')
                        self.root.after(0, self.log_message, cleaned_line)
                
                return_code = self.process.wait()
                
                if self.is_running:
                    if return_code == 0:
                        self.root.after(0, self.log_message, "下载完成！")
                        self.root.after(0, lambda: self.status_var.set("下载完成"))
                    else:
                        self.root.after(0, self.log_message, f"下载失败，返回码: {return_code}")
                        self.root.after(0, lambda: self.status_var.set("下载失败"))
                        
            except Exception as e2:
                self.root.after(0, self.log_message, f"最终错误: {str(e2)}")
                self.root.after(0, lambda: self.status_var.set("发生错误"))
                
        except Exception as e:
            self.root.after(0, self.log_message, f"错误: {str(e)}")
            self.root.after(0, lambda: self.status_var.set("发生错误"))
        finally:
            if self.is_running:
                # 下载完成时调用stop_download，但不显示"下载已停止"
                self.root.after(0, lambda: self.stop_download(user_stopped=False))


def main():
    """主函数"""
    # 创建主窗口
    root = tk.Tk()
    app = GoDingtalkGUI(root)
    
    # 运行主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
