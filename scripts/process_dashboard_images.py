#!/usr/bin/env python3
"""
Dashboard图片处理和优化脚本
优化截图质量并生成适合各平台的版本
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/image_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DashboardImageProcessor:
    """Dashboard图片处理器"""

    def __init__(self):
        """初始化处理器"""
        self.input_dir = Path('screenshots/dashboard')
        self.output_dir = Path('screenshots/optimized')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 各平台最佳尺寸
        self.platform_sizes = {
            'twitter': {
                'single': (1200, 675),      # 16:9 单图
                'multi': (1200, 675),        # 多图时每张的尺寸
                'aspect_ratio': 16/9
            },
            'linkedin': {
                'single': (1200, 627),       # LinkedIn 推荐
                'article': (1200, 1200),     # 正方形文章配图
                'aspect_ratio': 1.91
            },
            'instagram': {
                'square': (1080, 1080),      # 正方形
                'portrait': (1080, 1350),    # 4:5 纵向
                'story': (1080, 1920),       # 9:16 Story
                'aspect_ratio': 1
            },
            'facebook': {
                'single': (1200, 630),       # Facebook 推荐
                'aspect_ratio': 1.9
            },
            'reddit': {
                'single': (1200, 800),       # Reddit 较灵活
                'aspect_ratio': 1.5
            }
        }

        # 品牌颜色
        self.brand_colors = {
            'primary': '#6B46C1',    # 紫色
            'secondary': '#EC4899',  # 粉色
            'background': '#1a1a2e', # 深蓝
            'text': '#FFFFFF',       # 白色
            'accent': '#10B981'      # 绿色
        }

    def load_image(self, image_path: str) -> Image.Image:
        """加载图片"""
        try:
            img = Image.open(image_path)
            logger.info(f"Loaded image: {image_path} ({img.size})")
            return img
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

    def resize_image(self, img: Image.Image, target_size: Tuple[int, int],
                    maintain_aspect: bool = True) -> Image.Image:
        """调整图片大小"""
        if maintain_aspect:
            # 保持宽高比
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # 创建目标大小的新图片（带背景）
            new_img = Image.new('RGB', target_size, self.brand_colors['background'])

            # 将原图居中粘贴
            x = (target_size[0] - img.size[0]) // 2
            y = (target_size[1] - img.size[1]) // 2
            new_img.paste(img, (x, y))

            return new_img
        else:
            # 直接缩放到目标大小
            return img.resize(target_size, Image.Resampling.LANCZOS)

    def add_branding(self, img: Image.Image, platform: str = 'twitter') -> Image.Image:
        """添加品牌元素"""
        draw = ImageDraw.Draw(img, 'RGBA')

        # 尝试加载字体
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 36)
            subtitle_font = ImageFont.truetype("Arial.ttf", 24)
            small_font = ImageFont.truetype("Arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = title_font
            small_font = title_font

        # 添加顶部标题栏
        if platform in ['twitter', 'linkedin']:
            # 半透明背景条
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            # 顶部渐变条
            for i in range(80):
                alpha = int(200 * (1 - i/80))
                overlay_draw.rectangle(
                    [(0, i), (img.width, i+1)],
                    fill=(26, 26, 46, alpha)
                )

            # 合并overlay
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

            # 添加标题
            title = "AI Tool Hotspot"
            draw.text((30, 20), title, fill=(255, 255, 255), font=title_font)

            # 添加日期
            date_str = datetime.now().strftime('%B %d, %Y')
            date_bbox = draw.textbbox((0, 0), date_str, font=subtitle_font)
            date_width = date_bbox[2] - date_bbox[0]
            draw.text(
                (img.width - date_width - 30, 25),
                date_str,
                fill=(255, 255, 255, 230),
                font=subtitle_font
            )

        # 添加底部Call-to-Action
        if platform == 'twitter':
            # 底部渐变
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            for i in range(60):
                alpha = int(180 * (i/60))
                y = img.height - 60 + i
                overlay_draw.rectangle(
                    [(0, y), (img.width, y+1)],
                    fill=(26, 26, 46, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

            # CTA文本
            cta_text = "🔗 Full Dashboard: ai-hotspot.com"
            draw.text(
                (30, img.height - 35),
                cta_text,
                fill=(255, 255, 255),
                font=small_font
            )

        return img

    def enhance_image(self, img: Image.Image) -> Image.Image:
        """增强图片质量"""
        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)

        # 增强颜色饱和度
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)

        # 增强锐度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)

        return img

    def create_twitter_carousel(self, images: List[str]) -> List[str]:
        """创建Twitter轮播图（最多4张）"""
        processed = []

        for i, img_path in enumerate(images[:4]):
            img = self.load_image(img_path)
            if img:
                # 调整大小
                img = self.resize_image(img, self.platform_sizes['twitter']['multi'])

                # 添加页码标记
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("Arial Bold.ttf", 48)
                except:
                    font = ImageFont.load_default()

                # 页码圆圈
                circle_size = 80
                circle_pos = (img.width - 100, 50)
                draw.ellipse(
                    [circle_pos, (circle_pos[0] + circle_size, circle_pos[1] + circle_size)],
                    fill=(107, 70, 193),  # 品牌紫色
                    outline=(255, 255, 255),
                    width=3
                )

                # 页码数字
                page_text = f"{i+1}"
                text_bbox = draw.textbbox((0, 0), page_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                draw.text(
                    (circle_pos[0] + circle_size//2 - text_width//2,
                     circle_pos[1] + circle_size//2 - text_height//2),
                    page_text,
                    fill=(255, 255, 255),
                    font=font
                )

                # 添加品牌元素
                img = self.add_branding(img, 'twitter')

                # 增强图片
                img = self.enhance_image(img)

                # 保存
                output_path = self.output_dir / f"twitter_carousel_{i+1}.png"
                img.save(output_path, 'PNG', quality=95, optimize=True)
                processed.append(str(output_path))

                logger.info(f"Created Twitter carousel image {i+1}: {output_path}")

        return processed

    def create_linkedin_long_image(self, images: List[str]) -> str:
        """创建LinkedIn长图（拼接多张图）"""
        loaded_images = []

        for img_path in images[:3]:  # 最多拼接3张
            img = self.load_image(img_path)
            if img:
                # 统一宽度
                img = self.resize_image(img, (1200, 800))
                loaded_images.append(img)

        if not loaded_images:
            return None

        # 计算总高度
        total_height = sum(img.height for img in loaded_images) + 50 * (len(loaded_images) - 1)

        # 创建长图
        long_image = Image.new('RGB', (1200, total_height), self.brand_colors['background'])

        # 拼接图片
        y_offset = 0
        for i, img in enumerate(loaded_images):
            long_image.paste(img, (0, y_offset))
            y_offset += img.height + 50  # 50px间隔

        # 添加品牌元素
        long_image = self.add_branding(long_image, 'linkedin')

        # 保存
        output_path = self.output_dir / f"linkedin_long_{datetime.now().strftime('%Y%m%d')}.png"
        long_image.save(output_path, 'PNG', quality=95, optimize=True)

        logger.info(f"Created LinkedIn long image: {output_path}")
        return str(output_path)

    def create_instagram_story(self, image_path: str) -> str:
        """创建Instagram Story格式（9:16）"""
        img = self.load_image(image_path)
        if not img:
            return None

        # Story尺寸
        story_size = self.platform_sizes['instagram']['story']

        # 创建Story背景（渐变）
        story = Image.new('RGB', story_size)
        draw = ImageDraw.Draw(story)

        # 绘制渐变背景
        for i in range(story_size[1]):
            # 紫色到粉色渐变
            r = int(107 + (236 - 107) * i / story_size[1])
            g = int(70 + (72 - 70) * i / story_size[1])
            b = int(193 + (153 - 193) * i / story_size[1])
            draw.rectangle([(0, i), (story_size[0], i+1)], fill=(r, g, b))

        # 调整原图大小以适应Story
        img_ratio = img.width / img.height
        if img_ratio > 0.7:  # 横向图片
            new_width = int(story_size[0] * 0.9)
            new_height = int(new_width / img_ratio)
        else:  # 纵向图片
            new_height = int(story_size[1] * 0.5)
            new_width = int(new_height * img_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 将图片居中放置
        x = (story_size[0] - new_width) // 2
        y = int(story_size[1] * 0.25)  # 放在上部1/4位置

        # 添加白色边框
        img_with_border = ImageOps.expand(img, border=10, fill='white')
        story.paste(img_with_border, (x-10, y-10))

        # 添加文字
        draw = ImageDraw.Draw(story)
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 48)
            subtitle_font = ImageFont.truetype("Arial.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = title_font

        # 标题
        title = "AI Tool\nHotspot"
        draw.multiline_text(
            (story_size[0]//2, y + new_height + 100),
            title,
            fill=(255, 255, 255),
            font=title_font,
            anchor="mm",
            align="center"
        )

        # 副标题
        subtitle = "Daily AI Insights"
        draw.text(
            (story_size[0]//2, y + new_height + 200),
            subtitle,
            fill=(255, 255, 255, 230),
            font=subtitle_font,
            anchor="mm"
        )

        # CTA按钮
        button_y = story_size[1] - 150
        draw.rectangle(
            [(100, button_y), (story_size[0]-100, button_y+80)],
            fill=(255, 255, 255),
            outline=None
        )
        draw.text(
            (story_size[0]//2, button_y+40),
            "View Full Dashboard",
            fill=(107, 70, 193),
            font=subtitle_font,
            anchor="mm"
        )

        # 保存
        output_path = self.output_dir / f"instagram_story_{datetime.now().strftime('%Y%m%d')}.png"
        story.save(output_path, 'PNG', quality=95, optimize=True)

        logger.info(f"Created Instagram Story: {output_path}")
        return str(output_path)

    def batch_process(self, images: List[str], platforms: List[str]) -> Dict:
        """批量处理图片为多平台版本"""
        results = {
            'processed': {},
            'stats': {
                'total_input': len(images),
                'platforms': platforms,
                'timestamp': datetime.now().isoformat()
            }
        }

        for platform in platforms:
            logger.info(f"Processing for {platform}")

            if platform == 'twitter':
                # Twitter轮播图
                twitter_images = self.create_twitter_carousel(images)
                results['processed']['twitter'] = twitter_images

            elif platform == 'linkedin':
                # LinkedIn长图
                linkedin_image = self.create_linkedin_long_image(images)
                results['processed']['linkedin'] = [linkedin_image] if linkedin_image else []

            elif platform == 'instagram':
                # Instagram Story
                if images:
                    story = self.create_instagram_story(images[0])
                    results['processed']['instagram'] = [story] if story else []

            else:
                # 其他平台，使用默认处理
                processed = []
                for img_path in images:
                    img = self.load_image(img_path)
                    if img:
                        # 获取平台尺寸
                        if platform in self.platform_sizes:
                            target_size = self.platform_sizes[platform]['single']
                        else:
                            target_size = (1200, 675)  # 默认尺寸

                        # 调整大小
                        img = self.resize_image(img, target_size)

                        # 添加品牌
                        img = self.add_branding(img, platform)

                        # 增强
                        img = self.enhance_image(img)

                        # 保存
                        output_path = self.output_dir / f"{platform}_{Path(img_path).stem}_optimized.png"
                        img.save(output_path, 'PNG', quality=95, optimize=True)
                        processed.append(str(output_path))

                results['processed'][platform] = processed

        # 保存处理结果
        metadata_path = self.output_dir / f"processing_metadata_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metadata_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Processing complete. Metadata: {metadata_path}")
        return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dashboard图片处理工具')
    parser.add_argument(
        '--input',
        nargs='+',
        required=True,
        help='输入图片路径'
    )
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['twitter', 'linkedin', 'instagram', 'facebook', 'reddit', 'all'],
        default=['twitter'],
        help='目标平台'
    )
    parser.add_argument(
        '--mode',
        choices=['single', 'carousel', 'story', 'long'],
        default='single',
        help='处理模式'
    )

    args = parser.parse_args()

    # 如果选择all，处理所有平台
    if 'all' in args.platforms:
        args.platforms = ['twitter', 'linkedin', 'instagram', 'facebook', 'reddit']

    # 创建处理器
    processor = DashboardImageProcessor()

    try:
        if args.mode == 'carousel':
            # Twitter轮播模式
            results = processor.create_twitter_carousel(args.input)
            print(f"✅ Created {len(results)} carousel images")

        elif args.mode == 'story':
            # Instagram Story模式
            if args.input:
                result = processor.create_instagram_story(args.input[0])
                print(f"✅ Created Instagram Story: {result}")

        elif args.mode == 'long':
            # LinkedIn长图模式
            result = processor.create_linkedin_long_image(args.input)
            print(f"✅ Created LinkedIn long image: {result}")

        else:
            # 批量处理模式
            results = processor.batch_process(args.input, args.platforms)

            print("\n✅ Processing complete!")
            print(f"📊 Results:")
            for platform, images in results['processed'].items():
                print(f"  {platform}: {len(images)} images")
                for img in images:
                    print(f"    - {img}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()