import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = ROOT / "assets" / "brand"
MARK_BOTTOM_RATIO = 0.5805


def to_transparent(image):
    rgb = np.asarray(image.convert("RGB")).astype(np.float32) / 255.0
    alpha = rgb.max(axis=2)
    alpha = np.clip((alpha - 0.045) / 0.955, 0.0, 1.0) ** 0.85
    safe = np.where(alpha > 1e-4, alpha, 1.0)[..., None]
    color = np.clip(rgb / safe, 0.0, 1.0)
    rgba = np.dstack([color, alpha])
    return Image.fromarray((rgba * 255).astype(np.uint8))


def trim(image, padding=18, threshold=18):
    alpha = np.asarray(image)[..., 3]
    ys, xs = np.where(alpha > threshold)
    left, right = max(xs.min() - padding, 0), min(xs.max() + padding, image.width)
    top, bottom = max(ys.min() - padding, 0), min(ys.max() + padding, image.height)
    return image.crop((left, top, right, bottom))


def fit_width(image, width):
    if image.width <= width:
        return image
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.LANCZOS)


def square(image, size):
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    return canvas.resize((size, size), Image.LANCZOS)


def main():
    source = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("~/Desktop/1.png").expanduser()
    if not source.exists():
        raise SystemExit(f"Không tìm thấy tệp logo: {source}")
    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    full = to_transparent(Image.open(source))
    mark_cut = int(full.height * MARK_BOTTOM_RATIO)
    mark = full.crop((0, 0, full.width, mark_cut))

    full_logo = fit_width(trim(full), 1000)
    mark_logo = fit_width(trim(mark), 640)
    full_logo.save(BRAND_DIR / "logo-full.png", optimize=True)
    mark_logo.save(BRAND_DIR / "logo-mark.png", optimize=True)

    icon = square(mark_logo, 256)
    icon.save(BRAND_DIR / "favicon.png", optimize=True)
    icon.save(ROOT / "assets" / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Đã tạo:", *(p.relative_to(ROOT) for p in sorted(BRAND_DIR.glob("*"))), "assets/favicon.ico", sep="\n  ")


if __name__ == "__main__":
    main()