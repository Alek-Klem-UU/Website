"""
Photo Collage Generator - Glass Style
======================================
Edit the IMAGES list below to change which photos appear in the collage.
The order maps to the grid left-to-right, top-to-bottom.

Usage:  python make_collage.py
Output: collage_glass.jpg
"""

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
import cv2
import numpy as np

# ===== CONFIGURATION - EDIT THIS =====

IMAGES = [
    "boulder.png",   # row 1, left
    "friend2.jpg",   # row 1, right
    "main.JPG",      # row 2, left
    "vacation.jpg",  # row 2, right
    "travel2.jpg",   # row 3, left
    "friends.jpg",   # row 3, right
]

COLS = 2
ROWS = 3
CELL_W = 620
CELL_H = 500
GAP = 4
PADDING = 4
RADIUS = 0
BORDER_W = 0
OUTPUT = "collage_glass.jpg"

# ======================================


def smart_crop(img_pil, target_w, target_h):
    img_cv = cv2.cvtColor(np.array(img_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w = img_cv.shape[:2]
    target_ratio = target_w / target_h
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
    if len(faces) > 0:
        cx = int(np.mean([x + fw / 2 for x, y, fw, fh in faces]))
        cy = int(np.mean([y + fh / 2 for x, y, fw, fh in faces]))
    else:
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.GaussianBlur(edges, (51, 51), 0)
        cy_grid, cx_grid = np.mgrid[0:h, 0:w]
        center_weight = 1.0 - 0.3 * np.sqrt(
            ((cx_grid - w / 2) / (w / 2)) ** 2 + ((cy_grid - h / 2) / (h / 2)) ** 2
        )
        saliency = edges.astype(np.float32) * center_weight
        total = saliency.sum()
        if total > 0:
            cx = int((saliency * cx_grid).sum() / total)
            cy = int((saliency * cy_grid).sum() / total)
        else:
            cx, cy = w // 2, h // 2
    current_ratio = w / h
    if current_ratio > target_ratio:
        crop_h = h
        crop_w = int(h * target_ratio)
    else:
        crop_w = w
        crop_h = int(w / target_ratio)
    left = max(0, min(cx - crop_w // 2, w - crop_w))
    top = max(0, min(cy - crop_h // 2, h - crop_h))
    return img_pil.crop((left, top, left + crop_w, top + crop_h))


def round_corners(img, radius):
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
    result = img.copy().convert("RGBA")
    result.putalpha(mask)
    return result


def add_shadow(canvas, pos, size, radius=24, offset=8, blur=20, opacity=50):
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    x, y = pos
    draw.rounded_rectangle(
        [x + offset, y + offset, x + size[0] + offset, y + size[1] + offset],
        radius=radius,
        fill=(0, 0, 0, opacity),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(canvas, shadow)


def load_image(path):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGBA")


def generate_texture(w, h, seed=42):
    rng = np.random.RandomState(seed)
    texture = np.zeros((h, w), dtype=np.float32)
    for scale in [4, 8, 16, 32]:
        small = rng.randn(h // scale + 1, w // scale + 1).astype(np.float32)
        small_img = Image.fromarray((small * 127 + 128).clip(0, 255).astype(np.uint8))
        upscaled = small_img.resize((w, h), Image.BILINEAR)
        texture += np.array(upscaled).astype(np.float32) * (scale / 32.0)
    texture = (texture - texture.min()) / (texture.max() - texture.min())
    return texture


def main():
    cw = COLS * CELL_W + (COLS - 1) * GAP + 2 * PADDING
    ch = ROWS * CELL_H + (ROWS - 1) * GAP + 2 * PADDING

    # Load and smart-crop all images
    cropped_images = []
    for f in IMAGES:
        img = load_image(f)
        cropped = smart_crop(img, CELL_W, CELL_H)
        cropped = cropped.resize((CELL_W, CELL_H), Image.LANCZOS)
        cropped_images.append(cropped)

    # Calculate grid positions
    positions = []
    for i in range(len(IMAGES)):
        row, col = divmod(i, COLS)
        positions.append(
            (PADDING + col * (CELL_W + GAP), PADDING + row * (CELL_H + GAP))
        )

    # Build blurred glass background
    bg = Image.new("RGB", (cw, ch), (60, 60, 65))
    for img, (x, y) in zip(cropped_images, positions):
        bg.paste(img.convert("RGB"), (x, y))
    bg = bg.filter(ImageFilter.GaussianBlur(80))
    bg_arr = np.array(bg).astype(np.float32)
    bg_arr = bg_arr * 0.7 + 0.3 * 60
    bg = Image.fromarray(bg_arr.clip(0, 255).astype(np.uint8))
    bg = ImageEnhance.Color(bg).enhance(1.2)
    bg = ImageEnhance.Brightness(bg).enhance(1.3)

    # Add texture overlay
    texture = generate_texture(cw, ch)
    bg_arr = np.array(bg).astype(np.float32)
    texture_3d = np.stack([texture] * 3, axis=-1)
    bg_arr = bg_arr * (0.92 + 0.16 * texture_3d)
    canvas = Image.fromarray(bg_arr.clip(0, 255).astype(np.uint8)).convert("RGBA")

    # Place photos with borders and shadows
    for i, cropped in enumerate(cropped_images):
        x, y = positions[i]
        bordered_w = CELL_W + BORDER_W * 2
        bordered_h = CELL_H + BORDER_W * 2
        border_layer = Image.new("RGBA", (bordered_w, bordered_h), (255, 255, 255, 180))
        border_layer = round_corners(border_layer, RADIUS + BORDER_W)
        rc = round_corners(cropped, RADIUS)
        border_layer.paste(rc, (BORDER_W, BORDER_W), rc)
        bx, by = x - BORDER_W, y - BORDER_W
        canvas = add_shadow(
            canvas, (bx, by), (bordered_w, bordered_h), RADIUS + BORDER_W, 8, 20, 50
        )
        canvas.paste(border_layer, (bx, by), border_layer)

    canvas.convert("RGB").save(OUTPUT, quality=95)
    print(f"Saved {OUTPUT}: {cw}x{ch}")


if __name__ == "__main__":
    main()
