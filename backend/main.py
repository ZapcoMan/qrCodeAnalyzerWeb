from PIL import Image, ImageEnhance, ImageFilter
import sys
import logging
import numpy as np
import os
import re
try:
    import colorlog
    COLOR_LOGGING_AVAILABLE = True
except ImportError:
    COLOR_LOGGING_AVAILABLE = False

if COLOR_LOGGING_AVAILABLE:
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'blue',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

try:
    from pyzxing import BarCodeReader
    reader = BarCodeReader()
except Exception as e:
    logging.error(f"pyzxing 加载失败: {e}")
    logging.error("请安装 pyzxing: pip install pyzxing")
    reader = None

def is_url(path):
    url_pattern = re.compile(
        r'^https?://'
        r'(?:[\w-]+\.)+[\w-]+'
        r'(?:/\S*)?'
        r'\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?\S*)?$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(path))

def download_image(url, save_dir=None):
    if not is_url(url):
        logging.error(f"无效的 URL: {url}")
        return None
    
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        import requests
        logging.info(f"正在下载图片: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logging.warning(f"URL 内容不是图片类型: {content_type}")
        
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or '.' not in filename:
            import time
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
        logging.info(f"图片下载成功: {filepath} ({file_size / 1024:.2f} KB)")
        
        return filepath
        
    except ImportError:
        logging.error("缺少 requests 库，请安装: pip install requests")
        return None
    except requests.exceptions.Timeout:
        logging.error(f"下载超时: {url}")
    except requests.exceptions.ConnectionError:
        logging.error(f"连接错误: {url}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP 错误: {e}")
    except Exception as e:
        logging.error(f"下载失败: {e}")
    
    return None

def decode_data(raw_data, encoding_list):
    for encoding in encoding_list:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None

def decode_with_pyzxing(image_path):
    if reader is None:
        logging.error("pyzxing 解码器未初始化")
        return []
    
    try:
        results = reader.decode(image_path)
        
        if results and len(results) > 0:
            result = results[0]
            
            class DecodedObject:
                def __init__(self, data, barcode_type):
                    self.data = data.encode('utf-8') if isinstance(data, str) else data
                    self.type = str(barcode_type)
            
            raw_data = result.get('raw', '')
            barcode_type = result.get('format', 'QRCODE')
            
            if raw_data:
                return [DecodedObject(raw_data, barcode_type)]
    except Exception as e:
        logging.debug(f"pyzxing 解码失败: {e}")
    
    return []

def preprocess_image(img):
    images = []
    images.append(("原始图像", img))
    
    gray_img = img.convert('L')
    images.append(("灰度图像", gray_img))
    
    enhancer = ImageEnhance.Contrast(gray_img)
    contrast_img = enhancer.enhance(2.0)
    images.append(("高对比度图像", contrast_img))
    
    threshold = 128
    binary_img = contrast_img.point(lambda x: 0 if x < threshold else 255, '1')
    images.append(("二值化图像", binary_img))
    
    for threshold in [64, 192]:
        binary_img = contrast_img.point(lambda x: 0 if x < threshold else 255, '1')
        images.append((f"二值化图像(阈值{threshold})", binary_img))
    
    blurred = gray_img.filter(ImageFilter.GaussianBlur(radius=1))
    blurred_binary = blurred.point(lambda x: 0 if x < 128 else 255, '1')
    images.append(("高斯模糊+二值化", blurred_binary))
    
    sharpened = img.filter(ImageFilter.SHARPEN)
    images.append(("锐化图像", sharpened))
    
    inverted = Image.eval(gray_img, lambda x: 255 - x)
    images.append(("颜色反转图像", inverted))
    
    large_img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    images.append(("放大图像", large_img))
    
    return images

def decode_qrcode(image_path):
    logging.info(f"开始解码二维码: {image_path}")
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        logging.error(f"文件未找到: {image_path}")
        return
    except IOError:
        logging.error(f"无法打开文件: {image_path}")
        return

    try:
        processed_images = preprocess_image(img)
        decoded_objects = []

        for name, processed_img in processed_images:
            temp_path = f"temp_{name.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')}.png"
            try:
                processed_img.save(temp_path)
                temp_objects = decode_with_pyzxing(temp_path)
                if temp_objects:
                    decoded_objects = temp_objects
                    logging.info(f"使用 {name} 成功解码")
                    os.remove(temp_path)
                    break
                else:
                    os.remove(temp_path)
            except Exception as e:
                logging.debug(f"处理 {name} 时出错: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass

        if not decoded_objects:
            decoded_objects = decode_with_pyzxing(image_path)

        if decoded_objects:
            raw_data = decoded_objects[0].data
            barcode_type = decoded_objects[0].type

            decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
            if decoded_data:
                logging.info(f"二维码内容: {decoded_data}")
                decoded_content = decoded_data
            else:
                hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                logging.info(f"二维码数据(HEX): {hex_data}")
                logging.warning("无法将二维码数据解码为文本格式")
                decoded_content = f"十六进制数据: {hex_data}"
        else:
            logging.warning("标准方法未能解码二维码，尝试额外的处理方法")

            if img.mode != 'RGBA':
                rgba_img = img.convert('RGBA')
                rgba_temp = "temp_rgba.png"
                try:
                    rgba_img.save(rgba_temp)
                    decoded_objects = decode_with_pyzxing(rgba_temp)
                    if decoded_objects:
                        logging.info("RGBA转换后解码成功")
                    os.remove(rgba_temp)
                except Exception as e:
                    logging.debug(f"RGBA转换处理失败: {e}")
                    try:
                        os.remove(rgba_temp)
                    except:
                        pass

            if not decoded_objects:
                width, height = img.size
                crops = [
                    ("左上角", (0, 0, width//2, height//2)),
                    ("右上角", (width//2, 0, width, height//2)),
                    ("左下角", (0, height//2, width//2, height)),
                    ("右下角", (width//2, height//2, width, height))
                ]

                for name, box in crops:
                    cropped_img = img.crop(box)
                    crop_temp = f"temp_crop_{name}.png"
                    try:
                        cropped_img.save(crop_temp)
                        temp_objects = decode_with_pyzxing(crop_temp)
                        if temp_objects:
                            decoded_objects = temp_objects
                            logging.info(f"在裁剪区域 {name} 中成功解码")
                            os.remove(crop_temp)
                            break
                        else:
                            os.remove(crop_temp)
                    except Exception as e:
                        logging.debug(f"裁剪区域 {name} 处理失败: {e}")
                        try:
                            os.remove(crop_temp)
                        except:
                            pass

            if decoded_objects:
                raw_data = decoded_objects[0].data
                decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
                if decoded_data:
                    logging.info(f"二维码内容: {decoded_data}")
                else:
                    hex_data = raw_data.hex()
                    logging.info(f"二维码数据(HEX): {hex_data}")
                    logging.warning("无法将二维码数据解码为文本格式")
            else:
                logging.error("经过所有尝试后仍然无法解码二维码")
                logging.info("建议：确保二维码清晰完整，或尝试使用专门的二维码应用扫描")
    except Exception as e:
        logging.error(f"解码过程中发生错误: {e}")
        return

def process_input(input_path):
    downloaded_path = None
    try:
        if is_url(input_path):
            logging.info(f"检测到 URL，开始下载图片...")
            downloaded_path = download_image(input_path)
            if downloaded_path:
                decode_qrcode(downloaded_path)
            else:
                logging.error("图片下载失败")
        else:
            decode_qrcode(input_path)
    finally:
        if downloaded_path and os.path.exists(downloaded_path):
            try:
                os.remove(downloaded_path)
                
                downloads_dir = os.path.dirname(downloaded_path)
                if os.path.exists(downloads_dir) and not os.listdir(downloads_dir):
                    os.rmdir(downloads_dir)
            except Exception as e:
                logging.debug(f"清理临时文件时出错: {e}")

from flask import Flask, request, jsonify
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({'message': 'QR Code Analyzer API', 'endpoints': {
        '/decode': 'POST - 上传图片解析二维码',
        '/decode_url': 'POST - 通过URL解析二维码'
    }})

@app.route('/decode', methods=['POST'])
def decode_qr_endpoint():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if file:
            img_bytes = file.read()
            img_buffer = BytesIO(img_bytes)
            
            img = Image.open(img_buffer)
            
            temp_path = "temp_uploaded_qr.png"
            img.save(temp_path)
            
            decoded_objects = decode_with_pyzxing(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if decoded_objects:
                raw_data = decoded_objects[0].data
                barcode_type = decoded_objects[0].type

                decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
                if decoded_data:
                    return jsonify({
                        'success': True,
                        'result': decoded_data,
                        'type': str(barcode_type)
                    })
                else:
                    hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                    return jsonify({
                        'success': True,
                        'result': f"十六进制数据: {hex_data}",
                        'type': str(barcode_type)
                    })
            else:
                processed_images = preprocess_image(img)
                decoded_objects = []

                for name, processed_img in processed_images:
                    temp_path = f"temp_{name.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')}.png"
                    try:
                        processed_img.save(temp_path)
                        temp_objects = decode_with_pyzxing(temp_path)
                        if temp_objects:
                            decoded_objects = temp_objects
                            os.remove(temp_path)
                            break
                        else:
                            os.remove(temp_path)
                    except Exception as e:
                        logging.debug(f"处理 {name} 时出错: {e}")
                        try:
                            os.remove(temp_path)
                        except:
                            pass

                if decoded_objects:
                    raw_data = decoded_objects[0].data
                    barcode_type = decoded_objects[0].type
                    decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
                    if decoded_data:
                        return jsonify({
                            'success': True,
                            'result': decoded_data,
                            'type': str(barcode_type)
                        })
                
                return jsonify({'success': False, 'error': '无法解析二维码，请确保图片清晰且包含有效的二维码'}), 400
                
    except Exception as e:
        logging.error(f"解析二维码时发生错误: {e}")
        return jsonify({'success': False, 'error': f'解析过程中发生错误: {str(e)}'}), 500

@app.route('/decode_url', methods=['POST'])
def decode_qr_from_url():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '缺少URL参数'}), 400
        
        url = data['url']
        downloaded_path = download_image(url)
        
        if not downloaded_path:
            return jsonify({'success': False, 'error': '无法下载图片'}), 400
        
        try:
            decoded_objects = decode_with_pyzxing(downloaded_path)
            
            if decoded_objects:
                raw_data = decoded_objects[0].data
                barcode_type = decoded_objects[0].type
                decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
                
                if decoded_data:
                    return jsonify({
                        'success': True,
                        'result': decoded_data,
                        'type': str(barcode_type)
                    })
                else:
                    hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                    return jsonify({
                        'success': True,
                        'result': f"十六进制数据: {hex_data}",
                        'type': str(barcode_type)
                    })
            else:
                return jsonify({'success': False, 'error': '无法从URL中的图片解析二维码'}), 400
        finally:
            if downloaded_path and os.path.exists(downloaded_path):
                os.remove(downloaded_path)
                
    except Exception as e:
        logging.error(f"通过URL解析二维码时发生错误: {e}")
        return jsonify({'success': False, 'error': f'解析过程中发生错误: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
