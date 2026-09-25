import os
import shutil
import sys


def get_resource_path(relative_path):
    """
    获取资源的绝对路径
    支持开发环境和PyInstaller打包后环境
    
    Args:
        relative_path: 相对路径，如 "images/icon.png"
        
    Returns:
        资源的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹存储资源
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境：使用项目根目录
        base_path = os.path.dirname(os.path.dirname(__file__))
    
    # 调试信息
    # print(f"资源路径: {relative_path}")
    # print(f"基础路径: {base_path}")
    # print(f"完整路径: {os.path.join(base_path, relative_path)}")
    
    return os.path.join(base_path, relative_path)


def _find_in_android_sdk(tool_name):
    """在本机 Android SDK 的最新 Build-Tools 版本中查找工具。"""
    sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not sdk_root:
        return None

    build_tools_dir = os.path.join(sdk_root, "build-tools")
    if not os.path.isdir(build_tools_dir):
        return None

    versions = sorted(
        (
            name for name in os.listdir(build_tools_dir)
            if os.path.isdir(os.path.join(build_tools_dir, name))
        ),
        reverse=True
    )
    executable_names = [tool_name]
    if os.name == "nt":
        executable_names.extend((f"{tool_name}.bat", f"{tool_name}.exe"))

    for version in versions:
        for executable_name in executable_names:
            path = os.path.join(build_tools_dir, version, executable_name)
            if os.path.isfile(path):
                return path
    return None


def get_local_tool_path(tool_name, environment_variable=None, android_sdk=False):
    """
    查找本地安装的开发工具，不使用 resources 中捆绑的第三方工具。

    查找顺序：指定环境变量、Android SDK Build-Tools、系统 PATH。
    """
    if environment_variable:
        configured_path = os.environ.get(environment_variable)
        if configured_path:
            if os.path.isdir(configured_path):
                executable_name = tool_name
                if os.name == "nt":
                    executable_name += ".exe"
                configured_path = os.path.join(
                    configured_path, "bin", executable_name
                )
            if os.path.isfile(configured_path):
                return configured_path
            raise FileNotFoundError(
                f"{environment_variable} 指向的文件不存在: {configured_path}"
            )

    if android_sdk:
        sdk_path = _find_in_android_sdk(tool_name)
        if sdk_path:
            return sdk_path

    path = shutil.which(tool_name)
    if path:
        return path

    if os.name == "nt":
        for candidate in (f"{tool_name}.bat", f"{tool_name}.exe"):
            path = shutil.which(candidate)
            if path:
                return path

    return None
