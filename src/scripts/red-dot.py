import os
import math
import re
import subprocess
from pathlib import Path
import configparser

# --- Configuration ---
CONFIG_PATH = 'config.ini'
IMAGE_PATTERN = r'(\d{2})h(\d{2})m\.png'

# Read config
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# Get user location and mode
loc = config['LOCATION']
user_x = int(loc['x'])
user_y = int(loc['y'])
user_mode = loc['mode']

# Get globe info
xkcd_globe = config['XKCD_GLOBE']
black_globe = config['BLACK_GLOBE']

def get_config_value(section, key, default=None):
    try:
        return config[section][key]
    except Exception:
        return default

# Read style and interval from config.ini
clock_style = get_config_value('DEFAULT', 'image_style', 'black')
clock_interval = get_config_value('DEFAULT', 'interval', '1m')

# Set directories and globe info
if clock_style == 'black':
    if clock_interval == '1m':
        IMAGE_DIR = 'src/images/intervals1m/blackGreenOverlay'
        OUTPUT_DIR = 'src/images/intervals1m/blackGreenOverlayRedDot'
    else:
        IMAGE_DIR = 'src/images/intervals15m/blackGlobeGreenOverlay'
        OUTPUT_DIR = 'src/images/intervals15m/blackGlobeGreenOverlayRedDot'
    globe = black_globe
else:
    IMAGE_DIR = 'src/images/intervals15m/xkcdOriginal'
    OUTPUT_DIR = 'src/images/intervals15m/xkcdOriginalRedDot'
    globe = xkcd_globe

# Image and globe parameters
IMAGE_WIDTH = int(globe['width'])
IMAGE_HEIGHT = int(globe['height'])
CENTER_X = int(globe['center_x'])
CENTER_Y = int(globe['center_y'])
RADIUS = int(globe['radius'])

# Dot properties for ImageMagick
DOT_RADIUS = 5         # Size of the central red dot
DOT_COLOR = "red"
GLOW_SIGMA = 4         # Intensity/spread of the glow (higher = more spread)
GLOW_OPACITY = 80      # Opacity of the glow layer (0-100)

# Earth's rotation speed: 360 degrees in 24 hours = 15 degrees/hour = 0.25 degrees/minute
ROTATION_SPEED_DEG_PER_MIN = -0.25

# Reference time for calculating rotation (first image in your sequence)
REF_HOUR = 00
REF_MINUTE = 00
REF_TOTAL_MINUTES = REF_HOUR * 60 + REF_MINUTE

# --- Script Logic ---

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Gather all output paths
output_paths = []
for filename in os.listdir(IMAGE_DIR):
    match = re.match(IMAGE_PATTERN, filename)
    if match:
        output_paths.append(os.path.join(OUTPUT_DIR, filename))
existing = [p for p in output_paths if os.path.exists(p)]
overwrite = False
if existing:
    resp = input(f"Some red dot images already exist in {OUTPUT_DIR}. Overwrite all? (y/n): ").strip().lower()
    if resp == 'y':
        overwrite = True
    else:
        print("Keeping existing red dot images. Skipping existing files.")

# 1. Convert user pick to polar coordinates on the chosen globe
user_rel_x = user_x - CENTER_X
user_rel_y = user_y - CENTER_Y
user_r = math.sqrt(user_rel_x**2 + user_rel_y**2)
user_theta = math.atan2(user_rel_y, user_rel_x)

print(f"User pick ({clock_style} globe): x={user_x}, y={user_y}")
print(f"  Polar: r={user_r:.2f}, theta={user_theta:.4f} radians ({math.degrees(user_theta):.2f} deg)")

# 2. For each frame, rotate the dot and convert to (x, y) on the target globe
image_files = []
for filename in os.listdir(IMAGE_DIR):
    match = re.match(IMAGE_PATTERN, filename)
    if match:
        image_files.append(filename)

# Sort files chronologically based on their time
image_files.sort(key=lambda f: (int(re.match(IMAGE_PATTERN, f).group(1)), int(re.match(IMAGE_PATTERN, f).group(2))))

if not image_files:
    print(f"No image files matching pattern '{IMAGE_PATTERN}' found in '{IMAGE_DIR}'. Exiting.")
    exit()

for image_filename in image_files:
    input_path = os.path.join(IMAGE_DIR, image_filename)
    output_path = os.path.join(OUTPUT_DIR, image_filename)
    if os.path.exists(output_path) and not overwrite:
        continue  # skip if already exists

    match = re.match(IMAGE_PATTERN, image_filename)
    current_hour = int(match.group(1))
    current_minute = int(match.group(2))
    current_total_minutes = current_hour * 60 + current_minute

    # Calculate total minutes elapsed from the reference time
    minutes_from_base = current_total_minutes - REF_TOTAL_MINUTES

    # Calculate total rotation for this frame in degrees (clockwise)
    rotation_degrees = minutes_from_base * ROTATION_SPEED_DEG_PER_MIN
    rotation_radians = math.radians(rotation_degrees)

    # Calculate the current angle for the dot
    current_theta = user_theta - rotation_radians

    # Calculate new relative (x, y) coordinates for the dot using updated angle and original radius
    current_rel_x = user_r * math.cos(current_theta)
    current_rel_y = user_r * math.sin(current_theta)

    # Convert relative coordinates back to absolute image coordinates
    current_abs_x = int(round(CENTER_X + current_rel_x))
    current_abs_y = int(round(CENTER_Y + current_rel_y))

    # Ensure the dot is within the globe's radius
    dist_from_center = math.sqrt((current_abs_x - CENTER_X)**2 + (current_abs_y - CENTER_Y)**2)
    if dist_from_center > RADIUS:
        scale = RADIUS / dist_from_center
        current_abs_x = int(round(CENTER_X + (current_abs_x - CENTER_X) * scale))
        current_abs_y = int(round(CENTER_Y + (current_abs_y - CENTER_Y) * scale))

    print(f"Processing {image_filename} (Time: {current_hour:02d}:{current_minute:02d}):")
    print(f"  Rotation from base: {rotation_degrees:.2f} deg. Dot at ({current_abs_x}, {current_abs_y})")

    # ImageMagick command for adding the glowing dot (using 'convert' for IM6)
    temp_path = os.path.join(OUTPUT_DIR, f"temp_{image_filename}")
    magick_command = [
        "convert",
        "-size", f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}", "canvas:none",
        "-fill", f"rgba(255,255,255,{GLOW_OPACITY/100.0})",
        "-draw", f"circle {current_abs_x},{current_abs_y} {current_abs_x},{current_abs_y + DOT_RADIUS}",
        "-blur", f"0x{GLOW_SIGMA}",
        "-fill", DOT_COLOR,
        "-draw", f"circle {current_abs_x},{current_abs_y} {current_abs_x},{current_abs_y + DOT_RADIUS}",
        temp_path
    ]
    try:
        subprocess.run(magick_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating temporary image for {image_filename}: {e.stderr}")
        continue

    composite_command = [
        "convert",
        str(input_path),
        temp_path,
        "-composite",
        str(output_path)
    ]
    try:
        subprocess.run(composite_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error compositing image for {image_filename}: {e.stderr}")
        continue

    os.remove(temp_path)

print("--- Script Finished ---")
print(f"Processed images saved to '{OUTPUT_DIR}' directory.")
