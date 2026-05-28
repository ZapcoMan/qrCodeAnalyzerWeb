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

# 设置带颜色的日志记录
if COLOR_LOGGING_AVAILABLE:
    # 创建带颜色的日志格式
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

    # 创建控制台处理器并设置格式
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler]
    )
else:
    # 如果colorlog不可用，使用默认的日志记录
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# 初始化 pyzxing 解码器
try:
    from pyzxing import BarCodeReader
    reader = BarCodeReader()
    # logging.info("成功加载 pyzxing 解码器")
except Exception as e:
    logging.error(f"pyzxing 加载失败: {e}")
    logging.error("请安装 pyzxing: pip install pyzxing")
    reader = None

def is_url(path):
    """
    判断输入是否为 URL
    
    :param path: 输入字符串
    :return: bool
    """
    url_pattern = re.compile(
        r'^https?://'
        r'(?:[\w-]+\.)+[\w-]+'
        r'(?:/\S*)?'
        r'\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?\S*)?$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(path))

def download_image(url, save_dir=None):
    """
    从 URL 下载图片到本地
    
    :param url: 图片 URL 地址
    :param save_dir: 保存目录，默认为当前目录下的 downloads 文件夹
    :return: 下载后的图片路径，失败返回 None
    """
    if not is_url(url):
        logging.error(f"无效的 URL: {url}")
        return None
    
    # 创建保存目录
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        import requests
        logging.info(f"正在下载图片: {url}")
        
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 发送 GET 请求，超时设置为 30 秒
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 检查 Content-Type 是否为图片
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logging.warning(f"URL 内容不是图片类型: {content_type}")
        
        # 生成文件名（使用 URL 的最后一部分或时间戳）
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 如果文件名无效，使用时间戳
        if not filename or '.' not in filename:
            import time
            filename = f"qrcode_{int(time.time())}.png"
        
        # 确保文件扩展名有效
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in valid_extensions:
            filename += '.png'
        
        # 保存文件
        filepath = os.path.join(save_dir, filename)
        
        # 如果文件已存在，添加序号
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
    """
    尝试按照给定的编码格式列表解码数据。

    :param raw_data: 需要解码的原始字节数据。
    :param encoding_list: 编码格式的列表。
    :return: 解码后的字符串，如果所有格式尝试失败则返回None。
    """
    for encoding in encoding_list:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None

def decode_with_pyzxing(image_path):
    """
    使用 pyzxing 解码二维码
    
    :param image_path: 二维码图像文件的路径（字符串）
    :return: 解码结果列表，格式与 pyzbar.decode 兼容
    """
    if reader is None:
        logging.error("pyzxing 解码器未初始化")
        return []
    
    try:
        # pyzxing 只接受字符串路径，不支持列表
        results = reader.decode(image_path)
        
        if results and len(results) > 0:
            result = results[0]
            # 构造与 pyzbar 兼容的结果对象
            class DecodedObject:
                def __init__(self, data, barcode_type):
                    self.data = data.encode('utf-8') if isinstance(data, str) else data
                    self.type = str(barcode_type)  # 确保类型是字符串
            
            raw_data = result.get('raw', '')
            barcode_type = result.get('format', 'QRCODE')
            
            if raw_data:
                return [DecodedObject(raw_data, barcode_type)]
    except Exception as e:
        logging.debug(f"pyzxing 解码失败: {e}")
    
    return []

def preprocess_image(img):
    """
    预处理图像以提高二维码识别率

    :param img: 原始图像
    :return: 预处理后的图像列表（多种处理方式）
    """
    images = []

    # 原始图像
    images.append(("原始图像", img))

    # 转换为灰度图像
    gray_img = img.convert('L')
    images.append(("灰度图像", gray_img))

    # 增强对比度
    enhancer = ImageEnhance.Contrast(gray_img)
    contrast_img = enhancer.enhance(2.0)
    images.append(("高对比度图像", contrast_img))

    # 二值化处理
    threshold = 128
    binary_img = contrast_img.point(lambda x: 0 if x < threshold else 255, '1')
    images.append(("二值化图像", binary_img))

    # 尝试不同的阈值
    for threshold in [64, 192]:
        binary_img = contrast_img.point(lambda x: 0 if x < threshold else 255, '1')
        images.append((f"二值化图像(阈值{threshold})", binary_img))

    # 额外的预处理方法，专门针对Telegram二维码
    # 1. 高斯模糊去噪后再二值化
    blurred = gray_img.filter(ImageFilter.GaussianBlur(radius=1))
    blurred_binary = blurred.point(lambda x: 0 if x < 128 else 255, '1')
    images.append(("高斯模糊+二值化", blurred_binary))

    # 2. 锐化处理
    sharpened = img.filter(ImageFilter.SHARPEN)
    images.append(("锐化图像", sharpened))

    # 3. 颜色反转处理（针对反色二维码）
    inverted = Image.eval(gray_img, lambda x: 255 - x)
    images.append(("颜色反转图像", inverted))

    # 4. 尺寸放大（小尺寸二维码处理）
    large_img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    images.append(("放大图像", large_img))

    return images

def decode_qrcode(image_path):
    """
    解码给定路径下的二维码图像。

    :param image_path: 二维码图像文件的路径。
    """

    logging.info(f"开始解码二维码: {image_path}")
    # 尝试打开图像文件
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        logging.error(f"文件未找到: {image_path}")
        return
    except IOError:
        logging.error(f"无法打开文件: {image_path}")
        return

    # 使用 pyzxing 解码图像中的二维码
    try:
        # 尝试多种预处理方式（保存为临时文件）
        processed_images = preprocess_image(img)
        decoded_objects = []

        for name, processed_img in processed_images:
            # 保存预处理后的图像为临时文件
            temp_path = f"temp_{name.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')}.png"
            try:
                processed_img.save(temp_path)
                temp_objects = decode_with_pyzxing(temp_path)
                if temp_objects:
                    decoded_objects = temp_objects
                    logging.info(f"使用 {name} 成功解码")
                    # 删除临时文件
                    import os
                    os.remove(temp_path)
                    break
                else:
                    # 删除临时文件
                    import os
                    os.remove(temp_path)
            except Exception as e:
                logging.debug(f"处理 {name} 时出错: {e}")
                # 清理临时文件
                try:
                    import os
                    os.remove(temp_path)
                except:
                    pass

        # 如果所有预处理方式都失败，尝试直接解码原始图像
        if not decoded_objects:
            decoded_objects = decode_with_pyzxing(image_path)

        if decoded_objects:
            # 获取第一个解码对象的数据
            raw_data = decoded_objects[0].data
            barcode_type = decoded_objects[0].type

            # 尝试将原始数据解码为UTF-8字符串
            decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
            if decoded_data:
                logging.info(f"二维码内容: {decoded_data}")
                decoded_content = decoded_data
            else:
                # 如果文本解码失败，至少显示原始字节数据的十六进制表示
                hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                logging.info(f"二维码数据(HEX): {hex_data}")
                logging.warning("无法将二维码数据解码为文本格式")
                decoded_content = f"十六进制数据: {hex_data}"
        else:
            logging.warning("标准方法未能解码二维码，尝试额外的处理方法")

            # 针对Telegram二维码的特殊处理
            # 1. 尝试更激进的图像处理
            # 转换为RGBA模式再处理
            if img.mode != 'RGBA':
                rgba_img = img.convert('RGBA')
                rgba_temp = "temp_rgba.png"
                try:
                    rgba_img.save(rgba_temp)
                    decoded_objects = decode_with_pyzxing(rgba_temp)
                    if decoded_objects:
                        logging.info("RGBA转换后解码成功")
                    import os
                    os.remove(rgba_temp)
                except Exception as e:
                    logging.debug(f"RGBA转换处理失败: {e}")
                    try:
                        import os
                        os.remove(rgba_temp)
                    except:
                        pass

            # 2. 如果还是无法解码，输出一些诊断信息
            if not decoded_objects:
                # 检查是否包含多个二维码
                # 尝试裁剪图像的四个角分别解码
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
                            import os
                            os.remove(crop_temp)
                            break
                        else:
                            import os
                            os.remove(crop_temp)
                    except Exception as e:
                        logging.debug(f"裁剪区域 {name} 处理失败: {e}")
                        try:
                            import os
                            os.remove(crop_temp)
                        except:
                            pass

            if decoded_objects:
                # 获取解码结果
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
    """
    处理输入，自动识别是本地文件还是 URL
    
    :param input_path: 输入路径或 URL
    """
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
        # 如果是下载的图片，识别完成后删除
        if downloaded_path and os.path.exists(downloaded_path):
            try:
                os.remove(downloaded_path)
                # logging.info(f"已删除临时下载的图片: {downloaded_path}")
                
                # 尝试删除 downloads 目录（如果为空）
                downloads_dir = os.path.dirname(downloaded_path)
                if os.path.exists(downloads_dir) and not os.listdir(downloads_dir):
                    os.rmdir(downloads_dir)
                    # logging.info(f"已删除空的下载目录: {downloads_dir}")
            except Exception as e:
                logging.debug(f"清理临时文件时出错: {e}")

from flask import Flask, request, jsonify, render_template_string
import base64
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    """主页，提供一个简单的界面用于上传二维码图片"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>二维码解析器</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0; cursor: pointer; }
            .upload-area:hover { border-color: #666; }
            input[type="file"] { display: none; }
            button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #45a049; }
            .result { margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-left: 6px solid #2196F3; }
            .error { background-color: #ffebee; border-left: 6px solid #f44336; }
            .loading { display: none; text-align: center; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>二维码解析器</h1>
            <div class="upload-area" onclick="document.getElementById('fileInput').click();">
                <p>点击选择图片或拖拽图片到此处</p>
                <input type="file" id="fileInput" accept="image/*" onchange="handleFileSelect(event)">
            </div>
            <button onclick="decodeQRCode()">解析二维码</button>
            <div class="loading" id="loading">解析中...</div>
            <div id="result"></div>
        </div>

        <script>
            let selectedFile = null;

            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    document.querySelector('.upload-area p').textContent = '已选择: ' + file.name;
                }
            }

            // 也可以拖拽上传
            document.querySelector('.upload-area').addEventListener('dragover', function(e) {
                e.preventDefault();
                this.style.borderColor = '#666';
            });

            document.querySelector('.upload-area').addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.style.borderColor = '#ccc';
            });

            document.querySelector('.upload-area').addEventListener('drop', function(e) {
                e.preventDefault();
                this.style.borderColor = '#ccc';
                const file = e.dataTransfer.files[0];
                if (file && file.type.startsWith('image/')) {
                    selectedFile = file;
                    document.querySelector('.upload-area p').textContent = '已选择: ' + file.name;
                }
            });

            async function decodeQRCode() {
                if (!selectedFile) {
                    alert('请选择一张图片');
                    return;
                }

                const formData = new FormData();
                formData.append('file', selectedFile);

                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').innerHTML = '';

                try {
                    const response = await fetch('/decode', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (data.success) {
                        document.getElementById('result').innerHTML = `
                            <div class="result">
                                <h3>解析结果:</h3>
                                <p><strong>内容:</strong> ${data.result}</p>
                                <p><strong>类型:</strong> ${data.type}</p>
                            </div>
                        `;
                    } else {
                        document.getElementById('result').innerHTML = `
                            <div class="error">
                                <h3>解析失败:</h3>
                                <p>${data.error}</p>
                            </div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <div class="error">
                            <h3>请求失败:</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/decode', methods=['POST'])
def decode_qr_endpoint():
    """API接口，接收上传的图片并解析二维码"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if file:
            # 将文件保存到内存中的BytesIO对象
            img_bytes = file.read()
            img_buffer = BytesIO(img_bytes)
            
            # 打开图片
            img = Image.open(img_buffer)
            
            # 保存到临时文件进行处理
            temp_path = "temp_uploaded_qr.png"
            img.save(temp_path)
            
            # 使用现有的解码函数
            decoded_objects = decode_with_pyzxing(temp_path)
            
            # 清理临时文件
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if decoded_objects:
                # 获取第一个解码对象的数据
                raw_data = decoded_objects[0].data
                barcode_type = decoded_objects[0].type

                # 尝试将原始数据解码为UTF-8字符串
                decoded_data = decode_data(raw_data, ['utf-8', 'gbk', 'gb2312'])
                if decoded_data:
                    return jsonify({
                        'success': True,
                        'result': decoded_data,
                        'type': str(barcode_type)  # 确保barcode_type是字符串
                    })
                else:
                    # 如果文本解码失败，返回十六进制数据
                    hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                    return jsonify({
                        'success': True,
                        'result': f"十六进制数据: {hex_data}",
                        'type': str(barcode_type)  # 确保barcode_type是字符串
                    })
            else:
                # 如果标准方法失败，尝试预处理
                processed_images = preprocess_image(img)
                decoded_objects = []

                for name, processed_img in processed_images:
                    temp_path = f"temp_{name.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')}.png"
                    try:
                        processed_img.save(temp_path)
                        temp_objects = decode_with_pyzxing(temp_path)
                        if temp_objects:
                            decoded_objects = temp_objects
                            import os
                            os.remove(temp_path)
                            break
                        else:
                            import os
                            os.remove(temp_path)
                    except Exception as e:
                        logging.debug(f"处理 {name} 时出错: {e}")
                        try:
                            import os
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
    """通过URL解析二维码的API接口"""
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': '缺少URL参数'}), 400
        
        url = data['url']
        downloaded_path = download_image(url)
        
        if not downloaded_path:
            return jsonify({'success': False, 'error': '无法下载图片'}), 400
        
        try:
            # 解析二维码
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
            # 清理下载的文件
            if downloaded_path and os.path.exists(downloaded_path):
                os.remove(downloaded_path)
                
    except Exception as e:
        logging.error(f"通过URL解析二维码时发生错误: {e}")
        return jsonify({'success': False, 'error': f'解析过程中发生错误: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)