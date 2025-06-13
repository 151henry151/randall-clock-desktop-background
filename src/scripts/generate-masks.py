import os
import re
import sys
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import binary_dilation

IMAGE_DIR = 'src/images/intervals15m/blackGlobeGreenOverlay'
MASKS_DIR = 'src/images/masks'
OVERLAY_DIR = 'src/images/overlays'
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


def create_stationary_overlay(frames, overwrite=False):
    overlay_path = os.path.join(OVERLAY_DIR, 'stationary_overlay.png')
    if os.path.exists(overlay_path) and not overwrite:
        print(f"Overlay already exists at {overlay_path}.")
        return None
    imgs = [np.array(Image.open(os.path.join(IMAGE_DIR, f)).convert('RGBA')) for f in frames]
    imgs_stack = np.stack(imgs, axis=0)
    median_img = np.median(imgs_stack, axis=0).astype(np.uint8)
    overlay_img = Image.fromarray(median_img, 'RGBA')
    Path(OVERLAY_DIR).mkdir(parents=True, exist_ok=True)
    overlay_img.save(overlay_path)
    print(f"Saved overlay to {overlay_path}")
    return overlay_img


def create_globe_mask(overlay_img, source_frame, mask_path, overwrite=False):
    if os.path.exists(mask_path) and not overwrite:
        return None
    sample_img = Image.open(os.path.join(IMAGE_DIR, source_frame)).convert('RGBA')
    overlay_arr = np.array(overlay_img)
    sample_arr = np.array(sample_img)
    diff = np.abs(sample_arr[..., :3].astype(np.int16) - overlay_arr[..., :3].astype(np.int16)).sum(axis=2)
    mask = (diff > 30).astype(np.uint8) * 255
    mask_img = Image.fromarray(mask, 'L')
    Path(MASKS_DIR).mkdir(parents=True, exist_ok=True)
    mask_img.save(mask_path)
    print(f"Saved globe mask for {source_frame} as {mask_path}")
    return mask_img


def main():
    do_overlay = '--overlay' in sys.argv or len(sys.argv) == 1
    do_masks = '--masks' in sys.argv or len(sys.argv) == 1
    overwrite_overlay = '--overwrite' in sys.argv
    overwrite_masks = '--overwrite' in sys.argv
    frames = get_all_frames()
    overlay_img = None
    # Overlay prompt
    if do_overlay:
        overlay_path = os.path.join(OVERLAY_DIR, 'stationary_overlay.png')
        if os.path.exists(overlay_path) and not overwrite_overlay:
            resp = input(f"Overlay already exists at {overlay_path}. Overwrite? (y/n): ").strip().lower()
            if resp == 'y':
                overwrite_overlay = True
            else:
                print("Keeping existing overlay.")
        if not os.path.exists(overlay_path) or overwrite_overlay:
            overlay_img = create_stationary_overlay(frames, overwrite=True)
        else:
            overlay_img = Image.open(overlay_path).convert('RGBA')
    # Masks prompt
    if do_masks:
        mask_paths = [os.path.join(MASKS_DIR, f"{hour:02d}h{q:02d}m.png")
                      for hour in range(24) for q in range(0, 60, 15)
                      if os.path.exists(os.path.join(IMAGE_DIR, f"{hour:02d}h{q:02d}m.png"))]
        existing_masks = [p for p in mask_paths if os.path.exists(p)]
        if existing_masks and not overwrite_masks:
            resp = input(f"Some mask files already exist in {MASKS_DIR}. Overwrite all? (y/n): ").strip().lower()
            if resp == 'y':
                overwrite_masks = True
            else:
                print("Keeping existing masks.")
        if not existing_masks or overwrite_masks:
            if overlay_img is None:
                overlay_path = os.path.join(OVERLAY_DIR, 'stationary_overlay.png')
                if not os.path.exists(overlay_path):
                    print("Overlay not found. Please generate overlay first.")
                    return
                overlay_img = Image.open(overlay_path).convert('RGBA')
            for hour in range(24):
                for q in range(0, 60, 15):
                    source_name = f"{hour:02d}h{q:02d}m.png"
                    mask_path = os.path.join(MASKS_DIR, source_name)
                    if not os.path.exists(os.path.join(IMAGE_DIR, source_name)):
                        continue
                    create_globe_mask(overlay_img, source_name, mask_path, overwrite=overwrite_masks)

if __name__ == "__main__":
    main() 