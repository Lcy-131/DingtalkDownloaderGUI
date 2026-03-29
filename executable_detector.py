#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可执行文件检测库
专门用于检测和验证GoDingtalk可执行文件
"""

import os
import platform
from pathlib import Path

# 根据当前系统动态导入架构检测库
CURRENT_SYSTEM = platform.system()
HAVE_FILETYPE = False
HAVE_PEFILE = False
HAVE_ELFTOOLS = False
HAVE_MACHOLIB = False
MISSING_DEPENDENCIES = []  # 记录缺失的依赖

# filetype, pefile, elftools, macholib = None, None, None, None

# 延迟导入依赖库，避免在导入阶段就失败
def _import_dependencies():
    """延迟导入依赖库"""
    global HAVE_FILETYPE, HAVE_PEFILE, HAVE_ELFTOOLS, HAVE_MACHOLIB, MISSING_DEPENDENCIES
    
    # 清空缺失依赖列表
    MISSING_DEPENDENCIES.clear()
    
    # 检查基础依赖 filetype
    try:
        global filetype
        import filetype
        HAVE_FILETYPE = True
    except ImportError:
        MISSING_DEPENDENCIES.append("filetype")
        HAVE_FILETYPE = False
    
    if CURRENT_SYSTEM == "Windows":
        try:
            global pefile
            import pefile
            HAVE_PEFILE = True
        except ImportError:
            MISSING_DEPENDENCIES.append("pefile")
            HAVE_PEFILE = False

    elif CURRENT_SYSTEM == "Linux":
        try:
            global elftools
            from elftools.elf.elffile import ELFFile
            HAVE_ELFTOOLS = True
        except ImportError:
            MISSING_DEPENDENCIES.append("pyelftools")
            HAVE_ELFTOOLS = False

    elif CURRENT_SYSTEM == "Darwin":
        try:
            global macholib
            import macholib
            from macholib.MachO import MachO
            HAVE_MACHOLIB = True
        except ImportError:
            MISSING_DEPENDENCIES.append("macholib")
            HAVE_MACHOLIB = False

# 在类初始化时导入依赖
_import_dependencies()

def reload_dependencies():
    """重新加载依赖库（安装后调用）"""
    global HAVE_FILETYPE, HAVE_PEFILE, HAVE_ELFTOOLS, HAVE_MACHOLIB, MISSING_DEPENDENCIES
    
    # 清空缺失依赖列表
    MISSING_DEPENDENCIES.clear()
    
    # 重新导入sys模块以确保路径更新
    import sys
    
    # 强制重新导入依赖模块
    modules_to_reload = ['filetype', 'pefile', 'elftools', 'macholib']
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    # 重新导入依赖
    _import_dependencies()


class ExecutableDetector:
    """可执行文件检测器"""
    
    def __init__(self):
        self.current_system = platform.system()
        self.current_arch = platform.machine().lower()
    
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
        """获取可执行文件的CPU架构"""
        try:
            fmt = self.detect_executable_format(filepath)
            
            if fmt == 'PE' and self.current_system == "Windows":
                # Windows PE文件架构检测
                if not HAVE_PEFILE:
                    return "fallback"  # 需要检测但库不可用，使用后备检测
                
                pe = pefile.PE(filepath)
                machine = pe.FILE_HEADER.Machine
                
                if machine == 0x014c:  # IMAGE_FILE_MACHINE_I386
                    return 'x86'
                elif machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
                    return 'x86_64'
                elif machine == 0xaa64:  # IMAGE_FILE_MACHINE_ARM64
                    return 'arm64'
                else:
                    return 'unknown'
                    
            elif fmt == 'ELF' and self.current_system == "Linux":
                # Linux ELF文件架构检测
                if not HAVE_ELFTOOLS:
                    return "fallback"  # 需要检测但库不可用，使用后备检测
                
                with open(filepath, 'rb') as f:
                    elf = ELFFile(f)
                    machine = elf.header['e_machine']
                    
                    if machine == 0x03:  # EM_386
                        return 'x86'
                    elif machine == 0x3e:  # EM_X86_64
                        return 'x86_64'
                    elif machine == 0xb7:  # EM_AARCH64
                        return 'arm64'
                    else:
                        return 'unknown'
                        
            elif fmt == 'Mach-O' and self.current_system == "Darwin":
                # macOS Mach-O文件架构检测
                if not HAVE_MACHOLIB:
                    return "fallback"  # 需要检测但库不可用，使用后备检测
                
                macho = MachO(filepath)
                for header in macho.headers:
                    if header.header.cputype == 0x01000000:  # CPU_TYPE_X86
                        return 'x86'
                    elif header.header.cputype == 0x01000007:  # CPU_TYPE_X86_64
                        return 'x86_64'
                    elif header.header.cputype == 0x0100000c:  # CPU_TYPE_ARM64
                        return 'arm64'
                return 'unknown'
                
            else:
                # 其他系统的文件，不需要检测架构
                return "error"
                
        except Exception as e:
            print(f"架构检测错误: {e}")
            return "fallback"  # 检测出错，使用后备检测
    
    def is_architecture_compatible(self, filepath):
        """检查文件架构是否与当前系统兼容（基于真实二进制分析）"""
        # 首先检查平台兼容性
        if not self.is_platform_compatible(filepath):
            return False
        
        # 获取文件架构
        file_arch = self.get_file_architecture(filepath)
        
        # 如果返回"fallback"，说明需要检测但库不可用或检测出错
        if file_arch == "fallback":
            # 使用后备检查
            return self._fallback_architecture_check(filepath, self.current_arch)
        
        # 如果返回"error"，说明不需要检测（其他系统的文件）
        if file_arch == "error":
            # 对于其他系统的文件，直接返回False
            return False
        
        # 如果架构未知，使用后备检查
        if file_arch == 'unknown':
            return self._fallback_architecture_check(filepath, self.current_arch)
        
        # 定义架构兼容性映射
        arch_compatibility = {
            'x86': ['x86', 'i386', 'i686'],
            'x86_64': ['x86_64', 'amd64', 'x64'],
            'arm64': ['arm64', 'aarch64']
        }
        
        # 检查架构兼容性
        if file_arch in arch_compatibility:
            compatible_archs = arch_compatibility[file_arch]
            for compatible_arch in compatible_archs:
                if compatible_arch in self.current_arch:
                    return True
        
        # 特殊兼容性处理
        # Windows AMD64可以运行x86程序
        if self.current_system == "Windows" and file_arch == "x86" and "amd64" in self.current_arch:
            return True
        
        return False
    
    def is_platform_compatible(self, filepath):
        """检查文件平台是否与当前系统兼容（基于文件类型检测）"""
        try:
            # 使用filetype库检测文件真实类型
            kind = filetype.guess(filepath)
            
            if self.current_system == "Windows":
                # Windows系统：只接受Windows可执行文件
                if kind is None:
                    # 如果无法检测文件类型，在Windows上不兼容
                    return False
                
                # 基于文件扩展名检测平台兼容性
                extension = kind.extension.lower()
                if extension == 'exe':
                    return True
                # 其他平台的文件在Windows上不兼容
                return False
                
            elif self.current_system == "Darwin":
                # macOS系统：只接受macOS可执行文件
                if kind is None:
                    # 如果无法检测文件类型，检查是否为Mach-O格式
                    file_format = self.detect_executable_format(filepath)
                    if file_format == 'Mach-O':
                        return True
                    # 如果不是Mach-O格式，不兼容
                    return False
                
                # 基于文件扩展名检测平台兼容性
                extension = kind.extension.lower()
                # macOS可执行文件通常没有特定扩展名，但可以检查MIME类型
                if kind.mime == 'application/x-mach-binary':
                    return True
                # 其他平台的文件在macOS上不兼容
                return False
                
            elif self.current_system == "Linux":
                # Linux系统：只接受Linux可执行文件
                if kind is None:
                    # 如果无法检测文件类型，在Linux上不兼容
                    return False
                
                # 基于文件扩展名检测平台兼容性
                extension = kind.extension.lower()
                if extension == 'elf':
                    return True
                # 其他平台的文件在Linux上不兼容
                return False
            
            # 如果无法确定平台，放宽验证
            return True
            
        except Exception as e:
            print(f"平台兼容性检测错误: {e}")
            return True  # 出错时放宽验证
    
    def _fallback_architecture_check(self, filepath, current_arch):
        """后备架构检查（基于文件大小和格式）"""
        try:
            # 检查文件大小作为基本验证
            file_size = os.path.getsize(filepath)
            
            # 如果文件太小，可能不是有效的可执行文件
            if file_size < 100 * 1024:  # 小于100KB
                return False
            
            # 尝试通过文件格式进行基本判断
            file_format = self.detect_executable_format(filepath)
            
            if file_format == 'PE':
                # Windows PE文件：在Windows系统上放宽验证
                if self.current_system == "Windows":
                    return True
            elif file_format == 'ELF':
                # Linux ELF文件：在Linux系统上放宽验证
                if self.current_system == "Linux":
                    return True
            elif file_format == 'Mach-O':
                # macOS Mach-O文件：在macOS系统上放宽验证
                if self.current_system == "Darwin":
                    return True
            
            # 如果无法确定架构，返回True（放宽验证）
            return True
            
        except Exception as e:
            print(f"后备架构检查错误: {e}")
            return True  # 最终后备：放宽验证
    
    def validate_executable_by_type(self, filepath):
        """通过文件类型验证可执行文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(filepath):
                return False
            
            # 使用filetype库检测文件真实类型
            kind = filetype.guess(filepath)
            if kind is None:
                # 如果filetype无法识别，可能是跨平台编译的文件
                # 检查文件大小作为备用验证
                file_size = os.path.getsize(filepath)
                if file_size < 100 * 1024:  # 小于100KB
                    return False
                # 对于无法识别的文件，放宽验证条件
                return True
            
            # 根据操作系统检查MIME类型和扩展名（基于实际检测结果）
            if self.current_system == "Windows":
                # Windows可执行文件: PE格式
                if kind.mime != "application/x-msdownload" or kind.extension != "exe":
                    return False
            elif self.current_system == "Darwin":
                # macOS可执行文件: 放宽验证条件
                # 由于跨平台编译，filetype可能无法识别Mach-O格式
                # 主要依赖文件大小和文件名验证
                pass
            elif self.current_system == "Linux":
                # Linux可执行文件: ELF格式
                if kind.mime != "application/x-executable" or kind.extension != "elf":
                    return False
            
            # 检查文件大小（可执行文件通常大于100KB）
            file_size = os.path.getsize(filepath)
            if file_size < 100 * 1024:  # 小于100KB
                return False
                
            return True
            
        except Exception as e:
            print(f"文件类型验证错误: {e}")
            return False
    
    def scan_executable_directories(self, base_dir):
        """按照优先级顺序扫描不同目录，返回最合适的可执行文件列表"""
        base_path = Path(base_dir)
        
        # 定义检测目录的优先级顺序
        search_directories = [
            base_path,                    # 1. py文件同目录
            base_path / "src",            # 2. .\src目录
            base_path / "build"           # 3. .\build目录
        ]
        
        # 分类存储找到的可执行文件
        fully_compatible_files = []  # 架构和平台都匹配
        platform_only_files = []     # 仅平台匹配
        
        for search_dir in search_directories:
            if not search_dir.exists():
                continue
                
            print(f"🔍 扫描目录: {search_dir}")
            
            for file_path in search_dir.iterdir():
                if file_path.is_file():
                    # 检查文件名是否包含GoDingtalk
                    if "godingtalk" not in file_path.name.lower():
                        continue  # 跳过不包含GoDingtalk的文件
                    
                    # 使用filetype库验证文件类型
                    if self.validate_executable_by_type(str(file_path)):
                        # 检查平台兼容性
                        if self.is_platform_compatible(str(file_path)):
                            file_info = {
                                'path': str(file_path),
                                'directory': search_dir,
                                'platform_compatible': True,
                                'architecture_compatible': self.is_architecture_compatible(str(file_path))
                            }
                            
                            # 根据兼容性分类
                            if file_info['architecture_compatible']:
                                fully_compatible_files.append(file_info)
                                print(f"✅ 找到完全兼容文件: {file_path.name}")
                            else:
                                platform_only_files.append(file_info)
                                print(f"⚠️  找到平台兼容文件: {file_path.name}")
        
        # 按照优先级选择最合适的文件
        selected_files = []
        
        # 优先选择完全兼容的文件
        if fully_compatible_files:
            # 按照目录优先级排序：同目录 > src > build
            fully_compatible_files.sort(key=lambda x: self._get_directory_priority(x['directory'], search_directories))
            selected_files = [file['path'] for file in fully_compatible_files]
            print(f"🎯 选择完全兼容文件: {selected_files[0]}")
        elif platform_only_files:
            # 如果没有完全兼容的文件，选择平台兼容的文件
            platform_only_files.sort(key=lambda x: self._get_directory_priority(x['directory'], search_directories))
            selected_files = [file['path'] for file in platform_only_files]
            print(f"🎯 选择平台兼容文件: {selected_files[0]}")
        else:
            print("❌ 未找到任何兼容的可执行文件")
        
        return selected_files
    
    def _get_directory_priority(self, directory, search_directories):
        """获取目录的优先级（数值越小优先级越高）"""
        try:
            return search_directories.index(directory)
        except ValueError:
            return len(search_directories)  # 不在优先级列表中的目录优先级最低
    
    def get_executable_info(self, filepath):
        """获取可执行文件的详细信息"""
        info = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'file_format': self.detect_executable_format(filepath),
            'architecture': self.get_file_architecture(filepath),
            'platform_compatible': self.is_platform_compatible(filepath),
            'architecture_compatible': self.is_architecture_compatible(filepath),
            'file_type_valid': self.validate_executable_by_type(filepath)
        }
        
        # 生成状态描述
        if info['platform_compatible']:
            if info['architecture_compatible']:
                info['status'] = '✅ 完全兼容'
            else:
                info['status'] = '⚠️  平台兼容但架构可能不兼容'
        else:
            info['status'] = '❌ 平台不兼容'
        
        return info


def main():
    """测试函数"""
    detector = ExecutableDetector()
    
    print(f"当前系统: {detector.current_system}")
    print(f"当前架构: {detector.current_arch}")
    print()
    
    # 测试扫描build目录
    current_dir = Path(__file__).parent
    build_dir = current_dir / "build"
    
    executables = detector.scan_build_directory(build_dir)
    print(f"找到 {len(executables)} 个平台兼容的可执行文件:")
    
    for exe_path in executables:
        info = detector.get_executable_info(exe_path)
        print(f"\n文件: {info['filename']}")
        print(f"格式: {info['file_format']}")
        print(f"架构: {info['architecture']}")
        print(f"状态: {info['status']}")


if __name__ == "__main__":
    main()
