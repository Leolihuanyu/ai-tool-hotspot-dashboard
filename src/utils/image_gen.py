
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging

logger = logging.getLogger(__name__)

def create_gradient_background(width, height, start_color, end_color):
    """创建渐变背景"""
    base = Image.new('RGB', (width, height), start_color)
    top = Image.new('RGB', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def wrap_text(text, font, max_width):
    """文字换行"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def generate_tool_card(tool_name, tool_description, output_path):
    """生成工具介绍卡片"""
    try:
        # 画布尺寸 (16:9)
        width, height = 1200, 675
        
        # 创建渐变背景 (深紫到蓝)
        img = create_gradient_background(width, height, (76, 29, 149), (59, 130, 246))
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # 尝试加载字体
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
            desc_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # 绘制装饰元素 - 更精致的几何图案
        # 左上角 - 半透明圆环
        draw.ellipse([30, 30, 180, 180], outline=(255, 255, 255, 60), width=3)
        draw.ellipse([50, 50, 160, 160], outline=(255, 255, 255, 40), width=2)
        
        # 右下角 - 半透明方块
        draw.rectangle([width-250, height-250, width-50, height-50], 
                      outline=(255, 255, 255, 50), width=3)
        draw.rectangle([width-230, height-230, width-70, height-70], 
                      outline=(255, 255, 255, 30), width=2)
        
        # 添加一些小点作为装饰
        for i in range(5):
            x = 100 + i * 200
            y = height - 100
            draw.ellipse([x, y, x+8, y+8], fill=(255, 255, 255, 80))
        
        # 顶部装饰线
        draw.line([(80, 100), (width-80, 100)], fill=(255, 255, 255, 60), width=2)
        
        # 绘制标签
        label_y = 120
        draw.text((100, label_y), "🚀 AI TOOL SPOTLIGHT", font=label_font, fill=(255, 255, 255, 230))
        
        # 绘制工具名称
        title_y = 220
        draw.text((100, title_y), tool_name, font=title_font, fill=(255, 255, 255))
        
        # 绘制描述（换行）
        desc_y = 330
        max_desc_width = width - 200
        desc_lines = wrap_text(tool_description[:150], desc_font, max_desc_width)
        
        for i, line in enumerate(desc_lines[:3]):  # 最多3行
            draw.text((100, desc_y + i * 50), line, font=desc_font, fill=(255, 255, 255, 220))
        
        # 底部标签
        footer_y = height - 80
        draw.text((100, footer_y), "Daily AI Intel • Follow for more", font=label_font, fill=(255, 255, 255, 200))
        
        # 保存
        img.save(output_path, quality=95)
        logger.info(f"✨ Tool card generated: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Card generation failed: {e}")
        return False

def generate_social_image(tool_data, output_path):
    """生成社交媒体分享图
    
    Args:
        tool_data: 可以是 URL (旧方式) 或 dict (新方式，包含 name 和 description)
        output_path: 输出路径
    """
    # 兼容旧的 URL 方式
    if isinstance(tool_data, str):
        # 如果是 URL，生成简单卡片
        tool_name = "AI Tool"
        tool_desc = "Discover the latest AI tools and trends"
    else:
        # 新方式：使用工具数据
        tool_name = tool_data.get('name', 'AI Tool')
        tool_desc = tool_data.get('summary_en') or tool_data.get('description', 'Discover the latest AI tools')
    
    return generate_tool_card(tool_name, tool_desc, output_path)

