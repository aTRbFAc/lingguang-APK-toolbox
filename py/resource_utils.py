import os
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
