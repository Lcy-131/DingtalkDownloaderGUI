import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import json
import sys
import tempfile
import shutil
import re
import platform

class DingTalkDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("钉钉回放下载工具 (GoDingtalk GUI)")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # 配置文件路径
        self.config_file = "gui_config.json"
        self.config = self.load_config()

        # 子进程对象
        self.process = None
        self.running = False

        self.create_widgets()
        self.load_last_settings()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 可执行文件路径
        frame_exe = ttk.LabelFrame(main_frame, text="可执行文件路径", padding="5")
        frame_exe.pack(fill=tk.X, pady=5)

        self.exe_path = tk.StringVar()
        ttk.Entry(frame_exe, textvariable=self.exe_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(frame_exe, text="浏览", command=self.browse_exe).pack(side=tk.RIGHT)

        # 下载选项
        frame_options = ttk.LabelFrame(main_frame, text="下载选项", padding="5")
        frame_options.pack(fill=tk.X, pady=5)

        # URL 输入
        ttk.Label(frame_options, text="视频URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_var = tk.StringVar()
        ttk.Entry(frame_options, textvariable=self.url_var).grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))

        # URL 文件选择
        ttk.Label(frame_options, text="批量URL文件:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.url_file_var = tk.StringVar()
        ttk.Entry(frame_options, textvariable=self.url_file_var).grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        ttk.Button(frame_options, text="选择文件", command=self.browse_url_file).grid(row=1, column=2, padx=(5,0))

        # 线程数
        ttk.Label(frame_options, text="并发线程数:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.thread_var = tk.IntVar(value=10)
        ttk.Spinbox(frame_options, from_=1, to=100, textvariable=self.thread_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5,0))

        # 保存目录
        ttk.Label(frame_options, text="保存目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.save_dir_var = tk.StringVar()
        ttk.Entry(frame_options, textvariable=self.save_dir_var).grid(row=3, column=1, sticky=tk.W+tk.E, pady=2, padx=(5,0))
        ttk.Button(frame_options, text="选择目录", command=self.browse_save_dir).grid(row=3, column=2, padx=(5,0))

        # 让第二列自适应
        frame_options.columnconfigure(1, weight=1)

        # 控制按钮
        frame_buttons = ttk.Frame(main_frame)
        frame_buttons.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(frame_buttons, text="开始下载", command=self.start_download)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(frame_buttons, text="停止", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(frame_buttons, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        # 进度条框架
        frame_progress = ttk.LabelFrame(main_frame, text="下载进度", padding="5")
        frame_progress.pack(fill=tk.X, pady=5)

        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            frame_progress, orient=tk.HORIZONTAL,
            length=400, mode='determinate', variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, expand=True, pady=(0,5))

        self.status_label = ttk.Label(frame_progress, text="就绪", anchor=tk.CENTER)
        self.status_label.pack(fill=tk.X)
        
        # 日志显示区域
        frame_log = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        frame_log.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.Frame(frame_log)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=15, bg='black', fg='lime', insertbackground='white')
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_exe(self):
        filename = filedialog.askopenfilename(
            title="选择 GoDingtalk 可执行文件",
            filetypes=[("可执行文件", "*.exe;*.bin;*"), ("所有文件", "*.*")]
        )
        if filename:
            self.exe_path.set(filename)

    def browse_url_file(self):
        filename = filedialog.askopenfilename(
            title="选择包含URL的文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.url_file_var.set(filename)

    def browse_save_dir(self):
        directory = filedialog.askdirectory(title="选择视频保存目录")
        if directory:
            self.save_dir_var.set(directory)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        config = {
            'exe_path': self.exe_path.get(),
            'thread': self.thread_var.get(),
            'save_dir': self.save_dir_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def load_last_settings(self):
        if 'exe_path' in self.config:
            self.exe_path.set(self.config['exe_path'])
        if 'thread' in self.config:
            self.thread_var.set(self.config['thread'])
        if 'save_dir' in self.config:
            self.save_dir_var.set(self.config['save_dir'])

    def log(self, message):
        """向日志文本框添加消息（线程安全）"""
        def append():
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.see(tk.END)
        self.root.after(0, append)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def build_command(self):
        exe = self.exe_path.get().strip()
        if not exe:
            if sys.platform == "win32":
                candidates = ["GoDingtalk.exe", "GoDingtalk"]
            else:
                candidates = ["./GoDingtalk", "GoDingtalk"]
            for cand in candidates:
                if os.path.exists(cand):
                    exe = cand
                    break
        if not exe or not os.path.exists(exe):
            messagebox.showerror("错误", "请选择有效的 GoDingtalk 可执行文件")
            return None

        cmd = [exe]

        url = self.url_var.get().strip()
        url_file = self.url_file_var.get().strip()

        if url and url_file:
            messagebox.showerror("错误", "不能同时指定单个URL和批量URL文件，请只填写一个")
            return None
        if not url and not url_file:
            messagebox.showerror("错误", "请填写视频URL或选择批量URL文件")
            return None

        if url:
            cmd.append(f'-url={url}')          # 修改处：去掉引号
        if url_file:
            cmd.append(f'-urlFile={url_file}')  # 修改处：去掉引号

        thread = self.thread_var.get()
        if thread != 10:
            cmd.append(f'-thread={thread}')

        return cmd

    def run_process(self, cmd, temp_dir):
        self.running = True
        self.root.after(0, self.reset_progress)  # 重置进度条为不确定模式，显示“等待登录”
        try:
            self.log(f"执行命令: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                bufsize=1,
                cwd=temp_dir
            )

            percent_pattern = re.compile(r'(\d+(?:\.\d+)?)%')

            for line in iter(self.process.stdout.readline, ''):
                if not self.running:                # 用户点击停止
                    self.process.terminate()
                    break
                if line:
                    self.log(line.rstrip())
                    match = percent_pattern.search(line)
                    if match:
                        percent_float = float(match.group(1))   # 转为浮点数
                        percent = int(round(percent_float))     # 四舍五入取整
                        percent = max(0, min(100, percent))     # 限制在0-100
                        self.root.after(0, self.update_progress, percent)

            self.process.stdout.close()
            return_code = self.process.wait()        # 等待进程自然结束
            self.log(f"子进程退出，返回码: {return_code}")

        except Exception as e:
            self.log(f"发生异常: {str(e)}")
            # 异常发生时，确保子进程被终止
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()

        finally:
            self.running = False
            # 确保所有 UI 更新在主线程执行
            self.root.after(0, self.download_finished, temp_dir)

    def reset_progress(self):
        self.progress_var.set(0)
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        self.status_label.config(text="正在启动或等待登录...")

    def update_progress(self, value):
        # 如果进度条当前为不确定模式，则切换为确定模式
        if self.progress_bar.cget('mode') == 'indeterminate':
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
        self.progress_var.set(value)
        if value >= 100:
            # 下载完成，可能进入合并/转换阶段，切换回不确定模式
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
            self.status_label.config(text="处理中（合并/转换）...")
        else:
            self.status_label.config(text=f"下载中 {value}%")

    def download_finished(self, temp_dir):
        """下载结束后的UI恢复和文件移动"""
        # 先恢复UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(0)
        self.status_label.config(text="处理中（移动文件）...")
        self.log("下载任务结束，开始移动文件至目标目录...")

        # 目标目录
        target_dir = self.save_dir_var.get().strip()
        if not target_dir:
            target_dir = os.getcwd()
            self.log(f"未指定保存目录，将使用当前目录: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)

        try:
            exclude_files = {'cookies.json', 'config.json'}  # 不移动的文件

            # 递归遍历临时目录，移动所有非排除文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file in exclude_files:
                        continue  # 稍后单独处理
                    src = os.path.join(root, file)
                    # 计算相对路径（用于重命名前缀）
                    rel_path = os.path.relpath(root, temp_dir)
                    if rel_path == '.':
                        base_name = file
                    else:
                        # 将子目录路径转换为前缀（例如 video/xxx.mp4 -> video_xxx.mp4）
                        prefix = rel_path.replace(os.sep, '_')
                        base_name = f"{prefix}_{file}"
                    dst = os.path.join(target_dir, base_name)

                    # 处理目标文件已存在
                    if os.path.exists(dst):
                        name, ext = os.path.splitext(base_name)
                        counter = 1
                        while os.path.exists(os.path.join(target_dir, f"{name}_{counter}{ext}")):
                            counter += 1
                        dst = os.path.join(target_dir, f"{name}_{counter}{ext}")

                    shutil.move(src, dst)
                    self.log(f"已移动: {os.path.join(rel_path, file)} -> {dst}")

            # 复制 cookies/config 回程序目录
            if hasattr(self, 'exe_dir') and self.exe_dir:
                for filename in ['cookies.json', 'config.json']:
                    src_json = os.path.join(temp_dir, filename)
                    if os.path.exists(src_json):
                        dst_json = os.path.join(self.exe_dir, filename)
                        shutil.copy2(src_json, dst_json)
                        self.log(f"已更新 {filename} 到程序目录: {dst_json}")
            else:
                self.log("未找到程序目录，无法保存 cookies/config")

            # 删除临时目录
            shutil.rmtree(temp_dir)
            self.log(f"临时目录已清理: {temp_dir}")
            self.status_label.config(text="下载完成，文件已移至目标目录")

        except Exception as e:
            self.log(f"移动文件时出错: {str(e)}")
            self.status_label.config(text="移动文件失败，请手动处理临时文件")
            messagebox.showerror("移动文件错误", f"无法移动文件到目标目录：{e}\n临时文件位于：{temp_dir}")

        self.process = None
        self.save_config()

    def start_download(self):
        cmd = self.build_command()
        if cmd is None:
            return

        exe_path = cmd[0]                     # 获取实际的可执行文件路径
        self.exe_dir = os.path.dirname(exe_path)  # 保存程序目录供后续使用

        # 创建临时工作目录
        self.temp_dir = tempfile.mkdtemp(prefix="GoDingtalk_")
        self.log(f"临时工作目录: {self.temp_dir}")

        # 将程序目录下的 cookies.json 和 config.json 复制到临时目录（如果存在）
        for filename in ['cookies.json', 'config.json']:
            src = os.path.join(self.exe_dir, filename)
            if os.path.exists(src):
                dst = os.path.join(self.temp_dir, filename)
                shutil.copy2(src, dst)
                self.log(f"已复制 {filename} 到临时目录")

        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 在新线程中运行下载
        thread = threading.Thread(target=self.run_process, args=(cmd, self.temp_dir), daemon=True)
        thread.start()

    def stop_download(self):
        if self.process and self.running:
            self.running = False
            self.process.terminate()
            self.log("用户请求停止下载...")
        self.stop_btn.config(state=tk.DISABLED)

    def on_closing(self):
        """窗口关闭时尝试终止子进程"""
        if self.process and self.running:
            self.process.terminate()
        self.root.destroy()

if __name__ == "__main__":
    if platform.system() == "Windows":
        # 设置 DPI 感知
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass

        root = tk.Tk()
        
        # 设置 tkinter 缩放因子
        try:
            dpi = ctypes.windll.shcore.GetDpiForWindow(ctypes.windll.user32.GetDesktopWindow())
            scaling = dpi / 72.0
            root.tk.call('tk', 'scaling', scaling)
        except:
            pass

    app = DingTalkDownloaderGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()