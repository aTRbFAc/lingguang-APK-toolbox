import os
import re
import urllib.parse
import requests
import html
from bs4 import BeautifulSoup
import mimetypes
import logging
import tempfile
import shutil
import atexit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量，用于跟踪临时目录以便清理
_temp_dirs = []

def cleanup_temp_dirs():
    """清理所有临时目录"""
    for temp_dir in _temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"清理临时目录: {temp_dir}")
        except Exception as e:
            logger.error(f"清理临时目录失败 {temp_dir}: {e}")

# 注册退出时的清理函数
atexit.register(cleanup_temp_dirs)

def normalize_path(path):
    """统一路径分隔符为正斜杠，用于HTML中的路径"""
    if path:
        # 将Windows反斜杠替换为正斜杠
        return path.replace('\\', '/')
    return path

def get_relative_path(html_path, resource_path):
    """获取资源相对于HTML文件的相对路径"""
    html_dir = os.path.dirname(os.path.abspath(html_path))
    resource_abs = os.path.abspath(resource_path)
    
    # 计算相对路径
    relative_path = os.path.relpath(resource_abs, html_dir)
    
    # 统一为正斜杠
    return normalize_path(relative_path)


class ResourceLocalizer:
    def __init__(self, html_content, base_url=None, offline_mode=True, output_dir=None):
        """
        初始化资源本地化器
        
        Args:
            html_content: HTML内容字符串
            base_url: 基础URL，用于解析相对路径
            offline_mode: 是否启用离线模式
            output_dir: 输出目录路径
        """
        self.html_content = html_content
        self.base_url = base_url
        self.offline_mode = offline_mode
        
        # 使用BeautifulSoup解析HTML
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.base_href = self._extract_base_href()
        
        # 存储下载的资源信息
        self.resources = []
        self.resource_map = {}  # 原始URL -> 本地路径映射
        
        # 创建资源目录
        if output_dir is None:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="lingguang_resources_")
            _temp_dirs.append(temp_dir)  # 注册以便清理
            self.output_dir = temp_dir
        else:
            self.output_dir = output_dir
        
        # 创建资源目录
        self.resource_dir = os.path.join(self.output_dir, "index_files")
        os.makedirs(self.resource_dir, exist_ok=True)
        logger.info(f"资源目录创建在: {self.resource_dir}")
    
    def is_material_icons_css(self, url):
        """检查是否是material-icons.css"""
        return "material-icons" in url.lower() and url.lower().endswith(".css")
    
    def download_resource(self, url, local_filename):
        """下载资源文件"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 添加超时和重试
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            
            with open(local_filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"下载成功: {url} -> {local_filename}")
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {e}")
            return False
    
    def get_local_path(self, url, content_type=None):
        """
        根据URL生成本地文件路径
        
        Args:
            url: 资源URL
            content_type: 内容类型，用于确定扩展名
            
        Returns:
            本地文件路径（使用正斜杠）
        """
        # 解析URL获取文件名
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            # 如果没有路径，使用默认文件名
            filename = "resource"
        else:
            # 获取路径的最后一部分
            filename = os.path.basename(path)
            
            if not filename:
                filename = "resource"
        
        # 如果没有扩展名，根据内容类型添加
        if '.' not in filename and content_type:
            ext = mimetypes.guess_extension(content_type)
            if ext:
                filename += ext
        
        # 确保文件名是安全的
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        
        # 如果文件名仍然没有扩展名，根据常见类型添加
        if '.' not in filename:
            if url.lower().endswith('.js'):
                filename += '.js'
            elif url.lower().endswith('.css'):
                filename += '.css'
            elif url.lower().endswith('.png'):
                filename += '.png'
            elif url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
                filename += '.jpg'
            elif url.lower().endswith('.gif'):
                filename += '.gif'
            elif url.lower().endswith('.svg'):
                filename += '.svg'
            elif url.lower().endswith('.woff'):
                filename += '.woff'
            elif url.lower().endswith('.woff2'):
                filename += '.woff2'
            elif url.lower().endswith('.ttf'):
                filename += '.ttf'
            elif url.lower().endswith('.eot'):
                filename += '.eot'
        
        # 确保文件名唯一
        base_name, ext = os.path.splitext(filename)
        counter = 1
        final_filename = filename
        
        while os.path.exists(os.path.join(self.resource_dir, final_filename)):
            final_filename = f"{base_name}_{counter}{ext}"
            counter += 1
        
        # 返回相对路径（使用正斜杠）
        local_path = os.path.join("index_files", final_filename)
        return normalize_path(local_path)
    
    def _extract_base_href(self):
        """提取 HTML 中的 base href，用于解析相对路径"""
        base_tag = self.soup.find('base', href=True)
        if not base_tag:
            return None

        href = base_tag['href'].strip()
        if not href:
            return None

        if href.startswith(('http://', 'https://')):
            return href

        if self.base_url:
            return urllib.parse.urljoin(self.base_url, href)

        return href

    def get_effective_base_url(self):
        """获取用于解析相对路径的实际基础 URL"""
        return self.base_href or self.base_url

    def _remove_base_href(self):
        """移除 HTML 中的 base href 标签，避免离线后路径混乱"""
        base_tag = self.soup.find('base', href=True)
        if base_tag:
            base_tag.decompose()

    def resolve_url(self, url, base_url=None):
        """解析完整的绝对URL"""
        if not url or url.startswith('data:'):
            return None
        
        # 如果是完整URL
        if url.startswith(('http://', 'https://')):
            return url

        # 协议相对 URL
        if url.startswith('//'):
            effective_base = self.get_effective_base_url()
            scheme = urllib.parse.urlparse(effective_base).scheme if effective_base else 'https'
            return f"{scheme}:{url}"
        
        # 去除开头的 ./
        if url.startswith('./'):
            url = url[2:]

        effective_base = base_url or self.get_effective_base_url()
        if effective_base:
            return urllib.parse.urljoin(effective_base, url)
        
        # 如果没有任何基础URL，返回原始 URL
        return url
    
    def process_css_content(self, css_content, css_url):
        """处理CSS文件中的资源引用（递归处理）"""
        if not css_content:
            return css_content
        
        # 查找CSS中的url()引用
        def replace_css_url(match):
            url = match.group(1).strip('"\'')
            
            # 跳过data URL
            if url.startswith('data:'):
                return match.group(0)
            
            # 去除开头的 ./
            if url.startswith('./'):
                url = url[2:]
            
            # 解析完整URL
            full_url = self.resolve_url(url, css_url)
            if not full_url:
                return match.group(0)
            
            # 如果是material-icons.css的特殊情况
            if self.is_material_icons_css(full_url):
                return f"url('./index_files/material-icons.css')"
            
            # 检查是否已经下载过
            if full_url in self.resource_map:
                local_path = self.resource_map[full_url]
                return f"url('./{local_path}')"
            
            # 下载资源
            local_path = self.get_local_path(full_url)
            actual_path = os.path.join(self.output_dir, local_path)
            
            if self.download_resource(full_url, actual_path):
                self.resource_map[full_url] = local_path
                self.resources.append({
                    'url': full_url,
                    'local_path': local_path,
                    'type': 'css_resource'
                })
                return f"url('./{local_path}')"
            else:
                return match.group(0)
        
        # 替换CSS中的url()引用
        css_pattern = r'url\s*\(\s*["\']?([^"\')]+)["\']?\s*\)'
        processed_css = re.sub(css_pattern, replace_css_url, css_content)
        
        return processed_css
    
    def process_element(self, element, tag_name, attr_name, resource_type):
        """处理HTML元素中的资源引用"""
        if not element.has_attr(attr_name):
            return
        
        url = element[attr_name]
        
        # 跳过data URL
        if url.startswith('data:'):
            return
        
        # 去除开头的 ./
        if url.startswith('./'):
            url = url[2:]
        
        # 解析完整URL 优先使用 base href
        full_url = self.resolve_url(url, self.get_effective_base_url())
        if not full_url:
            return
        
        # 处理material-icons.css的特殊情况
        if self.is_material_icons_css(full_url):
            element[attr_name] = "./index_files/material-icons.css"
            return
        
        # 检查是否已经下载过
        if full_url in self.resource_map:
            local_path = self.resource_map[full_url]
            element[attr_name] = f"./{local_path}"
            return
        
        # 下载资源
        if resource_type == 'css':
            # 对于CSS文件，需要处理其中的资源引用
            local_path = self.get_local_path(full_url, 'text/css')
            actual_path = os.path.join(self.output_dir, local_path)
            
            if self.download_resource(full_url, actual_path):
                # 读取CSS内容并处理其中的资源引用
                try:
                    with open(actual_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    
                    # 处理CSS中的资源引用
                    processed_css = self.process_css_content(css_content, full_url)
                    
                    # 保存处理后的CSS
                    with open(actual_path, 'w', encoding='utf-8') as f:
                        f.write(processed_css)
                    
                    self.resource_map[full_url] = local_path
                    self.resources.append({
                        'url': full_url,
                        'local_path': local_path,
                        'type': resource_type
                    })
                    
                    element[attr_name] = f"./{local_path}"
                    
                except Exception as e:
                    logger.error(f"处理CSS文件失败 {full_url}: {e}")
        else:
            # 其他类型资源
            local_path = self.get_local_path(full_url)
            actual_path = os.path.join(self.output_dir, local_path)
            
            if self.download_resource(full_url, actual_path):
                self.resource_map[full_url] = local_path
                self.resources.append({
                    'url': full_url,
                    'local_path': local_path,
                    'type': resource_type
                })
                
                element[attr_name] = f"./{local_path}"
    
    def process_all_resources(self):
        """处理所有外部资源"""
        if not self.offline_mode:
            return self.soup.prettify()
        
        logger.info("开始处理外部资源...")
        
        # 处理JavaScript文件
        for script in self.soup.find_all('script'):
            self.process_element(script, 'script', 'src', 'script')
        
        # 处理CSS文件
        for link in self.soup.find_all('link'):
            if link.has_attr('rel') and 'stylesheet' in link.get('rel', []):
                self.process_element(link, 'link', 'href', 'css')
        
        # 处理图片
        for img in self.soup.find_all('img'):
            self.process_element(img, 'img', 'src', 'image')
        
        # 处理其他可能包含资源的元素
        for elem in self.soup.find_all(['source', 'track', 'audio', 'video', 'embed', 'object']):
            for attr in ['src', 'data', 'poster']:
                if elem.has_attr(attr):
                    self.process_element(elem, elem.name, attr, 'media')
        
        logger.info(f"处理完成，共下载 {len(self.resources)} 个资源文件")
        
        self._remove_base_href()
        return self.soup.prettify()
    
    def get_resource_dir(self):
        """获取资源目录路径"""
        return self.resource_dir
    
    def get_output_dir(self):
        """获取输出目录路径"""
        return self.output_dir
    
    def copy_resources_to(self, target_dir):
        """
        将资源复制到目标目录
        
        Args:
            target_dir: 目标目录
        """
        if not os.path.exists(self.resource_dir):
            return

        target_resource_dir = os.path.join(target_dir, "index_files")

        # 如果目标文件夹已存在，先删除
        if os.path.exists(target_resource_dir):
            shutil.rmtree(target_resource_dir, ignore_errors=True)

        # 复制资源文件夹
        shutil.copytree(self.resource_dir, target_resource_dir)
        logger.info(f"资源已复制到: {target_resource_dir}")

        return target_resource_dir


def localize_html_resources(html_content, base_url=None, offline_mode=True, output_dir=None):
    """
    本地化HTML中的外部资源
    
    Args:
        html_content: HTML内容
        base_url: 基础URL
        offline_mode: 是否启用离线模式
        output_dir: 输出目录路径
        
    Returns:
        处理后的HTML内容、资源目录路径、ResourceLocalizer实例
    """
    localizer = ResourceLocalizer(html_content, base_url, offline_mode, output_dir)
    processed_html = localizer.process_all_resources()
    return processed_html, localizer.get_resource_dir(), localizer
