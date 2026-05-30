#!/usr/bin/env python3
"""
Dashboard自动截图脚本
自动截取Dashboard的三个核心区域并保存为图片
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
import io

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DashboardCapture:
    """Dashboard截图工具"""

    def __init__(self, dashboard_url: str = None):
        """初始化截图工具"""
        self.dashboard_url = dashboard_url or os.getenv('DASHBOARD_URL', 'http://localhost:3000')
        self.output_dir = Path('screenshots/dashboard')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None

        # 定义要截取的区域
        self.capture_regions = {
            'overview': {
                'selector': '.dashboard-overview',  # 顶部统计卡片
                'filename': 'dashboard_overview.png',
                'description': 'Daily statistics overview'
            },
            'top_tools': {
                'selector': '.ai-tools-section',  # AI工具列表
                'filename': 'dashboard_tools.png',
                'description': 'Top AI Tools'
            },
            'trending': {
                'selector': '.trending-section',  # 热门话题
                'filename': 'dashboard_trending.png',
                'description': 'Trending Topics'
            },
            'opportunity': {
                'selector': '.featured-opportunity',  # 特色机会
                'filename': 'dashboard_opportunity.png',
                'description': 'Featured Opportunity'
            }
        }

    def setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """设置Chrome驱动"""
        options = Options()

        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        # 设置窗口大小以确保截图质量
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--force-device-scale-factor=2')  # 2x DPI for retina quality

        # 禁用GPU加速（在headless模式下可能有问题）
        options.add_argument('--disable-gpu')

        # 设置User-Agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=options)
            logger.info("Chrome driver initialized successfully")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

    def wait_for_dashboard_load(self, timeout: int = 30):
        """等待Dashboard完全加载"""
        try:
            # 等待主要元素加载
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard-container"))
            )

            # 等待数据加载（检查是否有数据显示）
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script(
                    "return document.querySelectorAll('.ai-tool-card').length > 0"
                )
            )

            # 额外等待以确保动画完成
            time.sleep(2)

            logger.info("Dashboard loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Dashboard failed to load: {e}")
            return False

    def capture_element(self, selector: str, filename: str) -> str:
        """截取指定元素"""
        try:
            # 查找元素
            element = self.driver.find_element(By.CSS_SELECTOR, selector)

            # 滚动到元素位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # 等待滚动完成

            # 获取元素位置和大小
            location = element.location
            size = element.size

            # 截取整个页面
            png = self.driver.get_screenshot_as_png()

            # 使用PIL裁剪出元素区域
            image = Image.open(io.BytesIO(png))

            # 计算裁剪区域（考虑2x DPI）
            left = location['x'] * 2
            top = location['y'] * 2
            right = left + size['width'] * 2
            bottom = top + size['height'] * 2

            # 裁剪图片
            cropped = image.crop((left, top, right, bottom))

            # 保存图片
            output_path = self.output_dir / filename
            cropped.save(output_path, 'PNG', quality=95)

            logger.info(f"Captured element to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to capture element {selector}: {e}")
            return None

    def capture_full_dashboard(self) -> str:
        """截取整个Dashboard页面"""
        try:
            # 设置页面高度以包含所有内容
            total_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            self.driver.set_window_size(1920, total_height)
            time.sleep(1)

            # 截图
            output_path = self.output_dir / f"dashboard_full_{datetime.now().strftime('%Y%m%d')}.png"
            self.driver.save_screenshot(str(output_path))

            logger.info(f"Captured full dashboard to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to capture full dashboard: {e}")
            return None

    def add_watermark(self, image_path: str, date_str: str = None) -> str:
        """添加水印和日期标记"""
        try:
            # 打开图片
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)

            # 准备日期文本
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d')

            # 尝试加载字体（如果失败则使用默认字体）
            try:
                font = ImageFont.truetype("Arial.ttf", 24)
                small_font = ImageFont.truetype("Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
                small_font = font

            # 添加日期标记（右上角）
            date_text = f"📅 {date_str}"
            text_bbox = draw.textbbox((0, 0), date_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = img.width - text_width - 20
            y = 20

            # 添加半透明背景
            draw.rectangle(
                [(x - 10, y - 5), (x + text_width + 10, y + text_height + 5)],
                fill=(0, 0, 0, 128)
            )

            # 绘制日期文本
            draw.text((x, y), date_text, fill=(255, 255, 255), font=font)

            # 添加品牌标记（左下角）
            brand_text = "AI Tool Hotspot"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=small_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_height = brand_bbox[3] - brand_bbox[1]

            x = 20
            y = img.height - brand_height - 20

            draw.text((x, y), brand_text, fill=(255, 255, 255, 200), font=small_font)

            # 保存带水印的图片
            watermarked_path = image_path.replace('.png', '_watermarked.png')
            img.save(watermarked_path, 'PNG', quality=95)

            logger.info(f"Added watermark to {watermarked_path}")
            return watermarked_path

        except Exception as e:
            logger.error(f"Failed to add watermark: {e}")
            return image_path

    def capture_dashboard_sections(self, add_watermark: bool = True) -> List[str]:
        """截取Dashboard的所有区域"""
        captured_files = []

        try:
            # 设置驱动
            self.setup_driver(headless=True)

            # 访问Dashboard
            logger.info(f"Navigating to {self.dashboard_url}")
            self.driver.get(self.dashboard_url)

            # 等待加载
            if not self.wait_for_dashboard_load():
                raise Exception("Dashboard failed to load")

            # 截取各个区域
            for region_name, region_config in self.capture_regions.items():
                logger.info(f"Capturing {region_name}: {region_config['description']}")

                # 生成文件名（包含日期）
                date_str = datetime.now().strftime('%Y%m%d')
                filename = region_config['filename'].replace('.png', f'_{date_str}.png')

                # 截图
                image_path = self.capture_element(
                    region_config['selector'],
                    filename
                )

                if image_path and add_watermark:
                    # 添加水印
                    image_path = self.add_watermark(image_path)

                if image_path:
                    captured_files.append({
                        'region': region_name,
                        'path': image_path,
                        'description': region_config['description']
                    })

            # 也截取一张完整的Dashboard
            full_path = self.capture_full_dashboard()
            if full_path and add_watermark:
                full_path = self.add_watermark(full_path)

            if full_path:
                captured_files.append({
                    'region': 'full',
                    'path': full_path,
                    'description': 'Full Dashboard'
                })

            logger.info(f"Successfully captured {len(captured_files)} screenshots")

        except Exception as e:
            logger.error(f"Error during capture: {e}")

        finally:
            if self.driver:
                self.driver.quit()

        return captured_files

    def capture_for_twitter(self) -> List[str]:
        """截取适合Twitter发布的三张图片"""
        twitter_images = []

        try:
            # 设置驱动
            self.setup_driver(headless=True)

            # 设置Twitter最佳尺寸
            self.driver.set_window_size(1200, 675)

            # 访问Dashboard
            self.driver.get(self.dashboard_url)

            # 等待加载
            if not self.wait_for_dashboard_load():
                raise Exception("Dashboard failed to load")

            # 定义Twitter需要的三个视图
            twitter_views = [
                {
                    'name': 'overview_stats',
                    'script': '''
                        // 滚动到顶部统计区域
                        document.querySelector('.dashboard-overview').scrollIntoView();
                    ''',
                    'filename': 'twitter_1_overview.png'
                },
                {
                    'name': 'top_tools',
                    'script': '''
                        // 滚动到AI工具区域
                        document.querySelector('.ai-tools-section').scrollIntoView();
                    ''',
                    'filename': 'twitter_2_tools.png'
                },
                {
                    'name': 'featured_opportunity',
                    'script': '''
                        // 滚动到特色机会区域
                        document.querySelector('.featured-opportunity').scrollIntoView();
                    ''',
                    'filename': 'twitter_3_opportunity.png'
                }
            ]

            date_str = datetime.now().strftime('%Y%m%d')

            for view in twitter_views:
                # 执行滚动脚本
                self.driver.execute_script(view['script'])
                time.sleep(1)  # 等待滚动和渲染

                # 截图
                filename = view['filename'].replace('.png', f'_{date_str}.png')
                output_path = self.output_dir / filename
                self.driver.save_screenshot(str(output_path))

                # 添加水印
                watermarked_path = self.add_watermark(str(output_path))
                twitter_images.append(watermarked_path)

                logger.info(f"Captured Twitter image: {watermarked_path}")

        except Exception as e:
            logger.error(f"Error capturing Twitter images: {e}")

        finally:
            if self.driver:
                self.driver.quit()

        return twitter_images

    def generate_metadata(self, captured_files: List[Dict]) -> Dict:
        """生成截图元数据"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'dashboard_url': self.dashboard_url,
            'captures': captured_files,
            'stats': {
                'total_captures': len(captured_files),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        }

        # 保存元数据
        metadata_path = self.output_dir / f"metadata_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {metadata_path}")
        return metadata


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dashboard自动截图工具')
    parser.add_argument(
        '--url',
        default=None,
        help='Dashboard URL (默认使用环境变量DASHBOARD_URL)'
    )
    parser.add_argument(
        '--mode',
        choices=['full', 'twitter', 'all'],
        default='twitter',
        help='截图模式'
    )
    parser.add_argument(
        '--no-watermark',
        action='store_true',
        help='不添加水印'
    )

    args = parser.parse_args()

    # 创建截图工具实例
    capture = DashboardCapture(dashboard_url=args.url)

    try:
        if args.mode == 'twitter':
            # Twitter专用截图
            images = capture.capture_for_twitter()
            print(f"✅ Captured {len(images)} Twitter images:")
            for img in images:
                print(f"  - {img}")

        elif args.mode == 'full':
            # 截取所有区域
            captured = capture.capture_dashboard_sections(
                add_watermark=not args.no_watermark
            )
            metadata = capture.generate_metadata(captured)
            print(f"✅ Captured {len(captured)} dashboard sections")
            print(f"📋 Metadata saved to: {capture.output_dir}/metadata_*.json")

        else:  # all
            # 两种模式都执行
            twitter_images = capture.capture_for_twitter()
            captured = capture.capture_dashboard_sections(
                add_watermark=not args.no_watermark
            )
            print(f"✅ Captured {len(twitter_images)} Twitter images")
            print(f"✅ Captured {len(captured)} dashboard sections")

    except Exception as e:
        logger.error(f"Capture failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()