import os
import sys
from PIL import Image, ImageDraw, ImageFont

def make_oogiri_meme(image_path: str, punchline: str, output_path: str = None) -> str:
    """
    根据日式综艺大喜利排版规范，自动在图片底部压制粗黑描边纯白大字。
    - 纯白文字 (#FFFFFF)
    - 纯黑实体描边，宽度随字号缩放（约 font_size / 10）
    - 底部居中，8% 安全边距，文字宽度上限为画面宽度的 85%
    - 半透明暗条保护（防浅色背景吃字）
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_oogiri{ext}"

    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    font_candidates = [
        "C:/Windows/Fonts/msyhbd.ttc",       # 微软雅黑 Bold
        "C:/Windows/Fonts/simhei.ttf",       # 黑体
        "/System/Library/Fonts/PingFang.ttc",# macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]

    def load_font(size: int):
        for fpath in font_candidates:
            if os.path.exists(fpath):
                try:
                    return ImageFont.truetype(fpath, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    draw = ImageDraw.Draw(img)

    # 动态字号：单行文字约占画面宽度 80%~85%。
    # 超宽则逐档收字，避免长句（14 字上限）把描边顶到画面边缘。
    font_size = max(24, int(w / 14))
    min_size = max(16, int(w / 40))
    while True:
        font = load_font(font_size)
        bbox = draw.textbbox((0, 0), punchline, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        if text_w <= w * 0.85 or font_size <= min_size:
            break
        font_size -= 2

    # 位置：底部居中，距底边 8%
    x = (w - text_w) // 2
    y = h - text_h - int(h * 0.08)

    # 1. 底部渐变半透明暗条
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    bar_top = max(0, y - int(text_h * 0.4))
    overlay_draw.rectangle([0, bar_top, w, h], fill=(0, 0, 0, 75))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 2. 纯黑实体描边（根据字号缩放描边宽度）
    stroke_w = max(2, int(font_size / 10))
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), punchline, font=font, fill=(0, 0, 0, 255))

    # 3. 纯白主字
    draw.text((x, y), punchline, font=font, fill=(255, 255, 255, 255))

    # 保存：按输出扩展名决定格式，PNG 输入不会被静默转成 JPEG
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ext = os.path.splitext(output_path)[1].lower()
    rgb = img.convert("RGB")
    if ext in (".jpg", ".jpeg", ""):
        rgb.save(output_path, "JPEG", quality=95)
    else:
        rgb.save(output_path)
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python render_meme.py <image_path> <punchline> [output_path]")
        sys.exit(1)
    img_in = sys.argv[1]
    text_in = sys.argv[2]
    out_in = sys.argv[3] if len(sys.argv) > 3 else None
    result = make_oogiri_meme(img_in, text_in, out_in)
    print(f"Meme rendered successfully: {result}")
