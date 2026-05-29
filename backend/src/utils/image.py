from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Tuple

def preprocess_image(img: Image.Image) -> List[Tuple[str, Image.Image]]:
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

def decode_data(raw_data, encoding_list: List[str]) -> str:
    for encoding in encoding_list:
        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None