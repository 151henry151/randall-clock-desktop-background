#!/usr/bin/env python3

import os
import math
import re
from pathlib import Path
from PIL import Image
import numpy as np

# Configuration
IMAGE_DIR = 'src/images/intervals15m/blackGlobeGreenOverlay'
OUTPUT_DIR = 'src/images/intervals1m/blackGreenOverlay'
MASKS_DIR = 'src/images/masks'
OVERLAY_DIR = 'src/images/overlays'
IMAGE_PATTERN = r'(\d{2})h(\d{2})m\.png'

# Earth's rotation speed: 360 degrees in 24 hours = 15 degrees/hour = 0.25 degrees/minute
ROTATION_SPEED_DEG_PER_MIN = -0.25


def generate_minute_frames():
    overlay_img = Image.open(os.path.join(OVERLAY_DIR, 'stationary_overlay.png')).convert('RGBA')
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(MASKS_DIR).mkdir(parents=True, exist_ok=True)

    # Gather all output paths
    output_paths = []
    for hour in range(24):
        for q in range(0, 60, 15):
            for minute in range(q, q+15):
                outname = f"{hour:02d}h{minute:02d}m.png"
                outpath = os.path.join(OUTPUT_DIR, outname)
                output_paths.append(outpath)
    existing = [p for p in output_paths if os.path.exists(p)]
    overwrite = False
    if existing:
        resp = input(f"Some frame images already exist in {OUTPUT_DIR}. Overwrite all? (y/n): ").strip().lower()
        if resp == 'y':
            overwrite = True
        else:
            print("Keeping existing frames. Skipping existing files.")
    for hour in range(24):
        for q in range(0, 60, 15):
            source_name = f"{hour:02d}h{q:02d}m.png"
            source_path = os.path.join(IMAGE_DIR, source_name)
            mask_path = os.path.join(MASKS_DIR, source_name)
            if not os.path.exists(source_path) or not os.path.exists(mask_path):
                continue
            source_img = Image.open(source_path).convert('RGBA')
            globe_mask = Image.open(mask_path).convert('L')
            for minute in range(q, q+15):
                outname = f"{hour:02d}h{minute:02d}m.png"
                outpath = os.path.join(OUTPUT_DIR, outname)
                if os.path.exists(outpath) and not overwrite:
                    continue  # skip if already exists
                total_minutes = hour * 60 + minute
                source_minutes = hour * 60 + q
                rotation = (total_minutes - source_minutes) * ROTATION_SPEED_DEG_PER_MIN
                # Extract globe
                globe_only = Image.composite(source_img, Image.new('RGBA', source_img.size, (0,0,0,0)), globe_mask)
                # Rotate globe (about center)
                rotated_globe = globe_only.rotate(rotation, resample=Image.BICUBIC, center=(source_img.width//2, source_img.height//2))
                # Composite onto overlay
                final = overlay_img.copy()
                final.alpha_composite(rotated_globe)
                final.save(outpath)
                print(f"Saved {outname} (source: {source_name}, rotation: {rotation:.2f} deg, mask: {mask_path})")


def main():
    generate_minute_frames()

if __name__ == "__main__":
    main() 