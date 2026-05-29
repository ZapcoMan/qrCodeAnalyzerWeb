import re
import os
import time
from typing import Optional

def is_url(path: str) -> bool:
    url_pattern = re.compile(
        r'^https?://'
        r'(?:[\w-]+\.)+[\w-]+'
        r'(?:/\S*)?'
        r'\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?\S*)?$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(path))

def download_image(url: str, save_dir: Optional[str] = None) -> Optional[str]:
    if not is_url(url):
        from .logger import setup_logger
        logger = setup_logger()
        logger.error(f"无效的 URL: {url}")
        return None
    
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'downloads')
    
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        import requests
        from .logger import setup_logger
        logger = setup_logger()
        logger.info(f"正在下载图片: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"URL 内容不是图片类型: {content_type}")
        
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or '.' not in filename:
            filename = f"qrcode_{int(time.time())}.png"
        
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in valid_extensions:
            filename += '.png'
        
        filepath = os.path.join(save_dir, filename)
        
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(save_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(filepath)
        logger.info(f"图片下载成功: {filepath} ({file_size / 1024:.2f} KB)")
        
        return filepath
        
    except ImportError:
        from .logger import setup_logger
        logger = setup_logger()
        logger.error("缺少 requests 库，请安装: pip install requests")
        return None
    except requests.exceptions.Timeout:
        from .logger import setup_logger
        logger = setup_logger()
        logger.error(f"下载超时: {url}")
    except requests.exceptions.ConnectionError:
        from .logger import setup_logger
        logger = setup_logger()
        logger.error(f"连接错误: {url}")
    except requests.exceptions.HTTPError as e:
        from .logger import setup_logger
        logger = setup_logger()
        logger.error(f"HTTP 错误: {e}")
    except Exception as e:
        from .logger import setup_logger
        logger = setup_logger()
        logger.error(f"下载失败: {e}")
    
    return None