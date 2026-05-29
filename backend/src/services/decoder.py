import os
from typing import Optional, Dict, Any, List
from PIL import Image

try:
    from pyzxing import BarCodeReader
    READER_AVAILABLE = True
except ImportError:
    READER_AVAILABLE = False

from src.utils.logger import setup_logger
from src.utils.image import preprocess_image, decode_data

logger = setup_logger()

class QRCodeDecoder:
    def __init__(self):
        self.reader = BarCodeReader() if READER_AVAILABLE else None
        self.encodings = ['utf-8', 'gbk', 'gb2312']
    
    def decode(self, image_path: str) -> Optional[Dict[str, Any]]:
        if self.reader is None:
            logger.error("pyzxing 解码器未初始化")
            return None
        
        try:
            results = self.reader.decode(image_path)
            
            if results and len(results) > 0:
                result = results[0]
                raw_data = result.get('raw', '')
                barcode_type = result.get('format', 'QRCODE')
                
                decoded_data = self._try_decode(raw_data)
                if decoded_data:
                    return {
                        'data': decoded_data,
                        'type': str(barcode_type)
                    }
                else:
                    hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
                    return {
                        'data': f"十六进制数据: {hex_data}",
                        'type': str(barcode_type)
                    }
        except Exception as e:
            logger.debug(f"pyzxing 解码失败: {e}")
        
        return None
    
    def decode_with_preprocessing(self, image_path: str) -> Optional[Dict[str, Any]]:
        try:
            img = Image.open(image_path)
        except (FileNotFoundError, IOError) as e:
            logger.error(f"无法打开图片: {e}")
            return None
        
        processed_images = preprocess_image(img)
        
        for name, processed_img in processed_images:
            temp_path = f"temp_{name.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')}.png"
            try:
                processed_img.save(temp_path)
                result = self.decode(temp_path)
                os.remove(temp_path)
                if result:
                    logger.info(f"使用 {name} 成功解码")
                    return result
            except Exception as e:
                logger.debug(f"处理 {name} 时出错: {e}")
                try:
                    os.remove(temp_path)
                except:
                    pass
        
        return None
    
    def decode_full(self, image_path: str) -> Optional[Dict[str, Any]]:
        result = self.decode(image_path)
        if result:
            return result
        
        logger.info("标准方法未能解码，尝试图像预处理")
        result = self.decode_with_preprocessing(image_path)
        if result:
            return result
        
        logger.info("尝试额外处理方法")
        result = self._try_additional_methods(image_path)
        if result:
            return result
        
        return None
    
    def _try_additional_methods(self, image_path: str) -> Optional[Dict[str, Any]]:
        try:
            img = Image.open(image_path)
            
            if img.mode != 'RGBA':
                rgba_img = img.convert('RGBA')
                rgba_temp = "temp_rgba.png"
                try:
                    rgba_img.save(rgba_temp)
                    result = self.decode(rgba_temp)
                    if result:
                        logger.info("RGBA转换后解码成功")
                        return result
                finally:
                    if os.path.exists(rgba_temp):
                        os.remove(rgba_temp)
            
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
                    result = self.decode(crop_temp)
                    if result:
                        logger.info(f"在裁剪区域 {name} 中成功解码")
                        return result
                finally:
                    if os.path.exists(crop_temp):
                        os.remove(crop_temp)
        except Exception as e:
            logger.debug(f"额外处理方法失败: {e}")
        
        return None
    
    def _try_decode(self, raw_data) -> str:
        return decode_data(raw_data, self.encodings)