import os
import re
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import binary_dilation

IMAGE_DIR = 'src/images/intervals15m/blackGlobeGreenOverlay'
MASKS_DIR = 'src/images/masks'
OUTPUT_DIR = 'src/images/overlays'
IMAGE_PATTERN = r'(\d{2})h(\d{2})m\.png'


def get_all_frames():
    frames = []
    for filename in os.listdir(IMAGE_DIR):
        match = re.match(IMAGE_PATTERN, filename)
        if match:
            frames.append(filename)
    return sorted(frames, key=lambda f: (
        int(re.match(IMAGE_PATTERN, f).group(1)),
        int(re.match(IMAGE_PATTERN, f).group(2))
    ))


def create_stationary_overlay(frames):
    imgs = [np.array(Image.open(os.path.join(IMAGE_DIR, f)).convert('RGBA')) for f in frames]
    imgs_stack = np.stack(imgs, axis=0)
    median_img = np.median(imgs_stack, axis=0).astype(np.uint8)
    overlay_img = Image.fromarray(median_img, 'RGBA')
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    overlay_img.save(os.path.join(OUTPUT_DIR, 'stationary_overlay.png'))
    return overlay_img


def create_globe_mask(overlay_img, source_frame, mask_path):
    sample_img = Image.open(os.path.join(IMAGE_DIR, source_frame)).convert('RGBA')
    overlay_arr = np.array(overlay_img)
    sample_arr = np.array(sample_img)
    diff = np.abs(sample_arr[..., :3].astype(np.int16) - overlay_arr[..., :3].astype(np.int16)).sum(axis=2)
    mask = (diff > 30).astype(np.uint8) * 255
    # No dilation (lines as thin as original)
    # mask = binary_dilation(mask, iterations=0).astype(np.uint8) * 255
    mask_img = Image.fromarray(mask, 'L')
    Path(MASKS_DIR).mkdir(parents=True, exist_ok=True)
    mask_img.save(mask_path)
    print("Saved globe mask for {} as {}".format(source_frame, mask_path))
    return mask_img


def main():
    frames = get_all_frames()
    overlay_img = create_stationary_overlay(frames)
    for hour in range(24):
        for q in range(0, 60, 15):
            source_name = f"{hour:02d}h{q:02d}m.png"
            mask_path = os.path.join(MASKS_DIR, source_name)
            if not os.path.exists(os.path.join(IMAGE_DIR, source_name)):
                continue
            create_globe_mask(overlay_img, source_name, mask_path)

if __name__ == "__main__":
    main() 