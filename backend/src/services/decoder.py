import os
import uuid
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image

try:
    from pyzxing import BarCodeReader
    READER_AVAILABLE = True
except ImportError:
    READER_AVAILABLE = False

from src.utils.logger import setup_logger
from src.utils.image import preprocess_image, decode_data

logger = setup_logger()

class DecodeResult:
    """解码结果数据类"""
    def __init__(self, data: str, barcode_type: str):
        self.data = data
        self.type = barcode_type
    
    def to_dict(self) -> Dict[str, str]:
        return {'data': self.data, 'type': self.type}

class QRCodeDecoderError(Exception):
    """解码器异常类"""
    pass

class QRCodeDecoder:
    """二维码解码器类"""
    
    DEFAULT_ENCODINGS = ['utf-8', 'gbk', 'gb2312']
    
    def __init__(self, encodings: Optional[List[str]] = None):
        self._reader = BarCodeReader() if READER_AVAILABLE else None
        self._encodings = encodings or self.DEFAULT_ENCODINGS
        self._validate_reader()
    
    def _validate_reader(self) -> None:
        """验证解码器是否可用"""
        if not READER_AVAILABLE:
            logger.warning("pyzxing 未安装，解码器功能受限")
    
    @property
    def is_available(self) -> bool:
        """检查解码器是否可用"""
        return self._reader is not None
    
    def decode(self, image_path: str) -> Optional[DecodeResult]:
        """
        使用 pyzxing 解码二维码
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            DecodeResult 对象，解码失败返回 None
        """
        if not self.is_available:
            logger.error("解码器不可用")
            return None
        
        if not os.path.exists(image_path):
            logger.error(f"文件不存在: {image_path}")
            return None
        
        try:
            results = self._reader.decode(image_path)
            
            if results and len(results) > 0:
                return self._parse_result(results[0])
                
        except Exception as e:
            logger.debug(f"pyzxing 解码失败: {e}")
        
        return None
    
    def _parse_result(self, result: Dict[str, Any]) -> Optional[DecodeResult]:
        """解析 pyzxing 返回的结果"""
        raw_data = result.get('raw', '')
        barcode_type = result.get('format', 'QRCODE')
        
        if not raw_data:
            return None
        
        decoded_data = self._try_decode(raw_data)
        if decoded_data:
            return DecodeResult(data=decoded_data, barcode_type=str(barcode_type))
        
        hex_data = raw_data.hex() if isinstance(raw_data, bytes) else raw_data.encode('utf-8').hex()
        return DecodeResult(data=f"十六进制数据: {hex_data}", barcode_type=str(barcode_type))
    
    def _try_decode(self, raw_data) -> Optional[str]:
        """尝试多种编码格式解码"""
        return decode_data(raw_data, self._encodings)
    
    def decode_with_preprocessing(self, image_path: str) -> Optional[DecodeResult]:
        """
        使用图像预处理技术尝试解码
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            DecodeResult 对象，解码失败返回 None
        """
        try:
            img = Image.open(image_path)
        except (FileNotFoundError, IOError) as e:
            logger.error(f"无法打开图片: {e}")
            return None
        
        processed_images = preprocess_image(img)
        
        for name, processed_img in processed_images:
            temp_path = self._generate_temp_path(name)
            try:
                processed_img.save(temp_path)
                result = self.decode(temp_path)
                if result:
                    logger.info(f"使用 {name} 成功解码")
                    return result
            except Exception as e:
                logger.debug(f"处理 {name} 时出错: {e}")
            finally:
                self._cleanup_temp_file(temp_path)
        
        return None
    
    def decode_full(self, image_path: str) -> Optional[Dict[str, str]]:
        """
        完整解码流程：尝试多种方法直到成功
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            包含 data 和 type 的字典，解码失败返回 None
        """
        methods = [
            ("标准解码", self.decode),
            ("图像预处理", self.decode_with_preprocessing),
            ("额外方法", self._try_additional_methods)
        ]
        
        for method_name, method in methods:
            result = method(image_path)
            if result:
                return result.to_dict() if isinstance(result, DecodeResult) else result
        
        logger.error("所有解码方法均失败")
        return None
    
    def _try_additional_methods(self, image_path: str) -> Optional[DecodeResult]:
        """尝试额外的图像处理方法"""
        try:
            img = Image.open(image_path)
            
            rgba_result = self._try_rgba_conversion(img)
            if rgba_result:
                return rgba_result
            
            crop_result = self._try_cropping(img)
            if crop_result:
                return crop_result
                
        except Exception as e:
            logger.debug(f"额外处理方法失败: {e}")
        
        return None
    
    def _try_rgba_conversion(self, img: Image.Image) -> Optional[DecodeResult]:
        """尝试 RGBA 格式转换"""
        if img.mode != 'RGBA':
            rgba_img = img.convert('RGBA')
            temp_path = self._generate_temp_path("rgba")
            try:
                rgba_img.save(temp_path)
                result = self.decode(temp_path)
                if result:
                    logger.info("RGBA转换后解码成功")
                    return result
            finally:
                self._cleanup_temp_file(temp_path)
        return None
    
    def _try_cropping(self, img: Image.Image) -> Optional[DecodeResult]:
        """尝试裁剪图片的四个角落"""
        width, height = img.size
        crops = [
            ("左上角", (0, 0, width//2, height//2)),
            ("右上角", (width//2, 0, width, height//2)),
            ("左下角", (0, height//2, width//2, height)),
            ("右下角", (width//2, height//2, width, height))
        ]
        
        for name, box in crops:
            cropped_img = img.crop(box)
            temp_path = self._generate_temp_path(f"crop_{name}")
            try:
                cropped_img.save(temp_path)
                result = self.decode(temp_path)
                if result:
                    logger.info(f"在裁剪区域 {name} 中成功解码")
                    return result
            finally:
                self._cleanup_temp_file(temp_path)
        
        return None
    
    def _generate_temp_path(self, suffix: str) -> str:
        """生成唯一的临时文件路径"""
        safe_suffix = suffix.replace('(', '').replace(')', '').replace(' ', '_').replace(',', '')
        return f"temp_{uuid.uuid4().hex[:12]}_{safe_suffix}.png"
    
    def _cleanup_temp_file(self, file_path: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.debug(f"清理临时文件失败: {e}")