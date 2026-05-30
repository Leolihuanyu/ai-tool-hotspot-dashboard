
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

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

def add_corners(im, rad):
    """给图片添加圆角"""
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def generate_beautiful_image(screenshot_path, output_path, title=None):
    """生成精美图片"""
    try:
        # 1. 加载截图
        screenshot = Image.open(screenshot_path)

        # 调整截图大小（如果太大）
        max_w = 1200
        if screenshot.width > max_w:
            ratio = max_w / screenshot.width
            new_h = int(screenshot.height * ratio)
            screenshot = screenshot.resize((max_w, new_h), Image.Resampling.LANCZOS)

        # 2. 创建画布 (16:9 比例，适合Twitter)
        # 留出边距
        padding = 100
        canvas_w = screenshot.width + (padding * 2)
        canvas_h = screenshot.height + (padding * 2)

        # 如果高度不够16:9，增加高度
        target_ratio = 16/9
        if canvas_w / canvas_h > target_ratio:
            canvas_h = int(canvas_w / target_ratio)
        else:
            canvas_w = int(canvas_h * target_ratio)

        # 3. 绘制背景 (紫色渐变)
        # Deep Purple (#4c1d95) to Blue (#3b82f6)
        bg = create_gradient_background(canvas_w, canvas_h, (76, 29, 149), (59, 130, 246))

        # 4. 处理截图（圆角 + 阴影）
        # 圆角
        screenshot = screenshot.convert("RGBA")
        screenshot = add_corners(screenshot, 20)

        # 阴影
        shadow_offset = 30
        shadow = Image.new("RGBA", (screenshot.width + shadow_offset, screenshot.height + shadow_offset), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        # 绘制黑色矩形作为阴影
        shadow_draw.rectangle(
            [10, 10, screenshot.width - 10, screenshot.height - 10],
            fill=(0, 0, 0, 100)
        )
        # 模糊阴影
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))

        # 5. 合成
        # 计算居中位置
        x = (canvas_w - screenshot.width) // 2
        y = (canvas_h - screenshot.height) // 2

        # 先贴阴影
        bg.paste(shadow, (x + 10, y + 10), shadow)
        # 再贴截图
        bg.paste(screenshot, (x, y), screenshot)

        # 6. 保存
        bg.save(output_path)
        print(f"✨ Image generated: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return False

from playwright.sync_api import sync_playwright

def take_screenshot(url, output_path):
    """使用Playwright截图"""
    print(f"📸 Taking screenshot of {url}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(url, wait_until='domcontentloaded')
            # 稍微等待一下以确保渲染完成
            page.wait_for_timeout(2000)
            page.screenshot(path=output_path)
            browser.close()
        print(f"✅ Screenshot saved to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return False

if __name__ == "__main__":
    # 默认测试URL
    test_url = "https://www.producthunt.com/"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    temp_screenshot = "temp_screenshot.png"
    final_output = "beautiful_output.png"

    if take_screenshot(test_url, temp_screenshot):
        generate_beautiful_image(temp_screenshot, final_output)

        # 清理
        if os.path.exists(temp_screenshot):
            os.remove(temp_screenshot)

        print(f"🎉 Done! Check {final_output}")
    else:
        print("Failed to take screenshot.")
