import os
import math
import re
import subprocess
from pathlib import Path
import configparser

# --- Configuration ---
IMAGE_DIR = 'src/images/intervals1m/blackGreenOverlay'  # Directory where your input images are located
OUTPUT_DIR = 'src/images/intervals1m/blackGreenOverlayRedDot' # Directory where processed images will be saved
IMAGE_PATTERN = r'(\d{2})h(\d{2})m\.png' # Regex to parse filenames like 21h30m.png
CONFIG_PATH = 'config.ini'

# Image dimensions (assuming all your images are 1980x1977 pixels)
IMAGE_WIDTH = 1980
IMAGE_HEIGHT = 1977
CENTER_X = IMAGE_WIDTH / 2
CENTER_Y = IMAGE_HEIGHT / 2

# Load red dot location from config.ini if available
config = configparser.ConfigParser()
if os.path.exists(CONFIG_PATH):
    config.read(CONFIG_PATH)
    try:
        INITIAL_VT_ABS_X = int(config['LOCATION']['x'])
        INITIAL_VT_ABS_Y = int(config['LOCATION']['y'])
    except Exception:
        INITIAL_VT_ABS_X = 638
        INITIAL_VT_ABS_Y = 873
else:
    INITIAL_VT_ABS_X = 638
    INITIAL_VT_ABS_Y = 873

# Dot properties for ImageMagick
DOT_RADIUS = 5         # Size of the central red dot
DOT_COLOR = "red"
GLOW_SIGMA = 4         # Intensity/spread of the glow (higher = more spread)
GLOW_OPACITY = 60      # Opacity of the glow layer (0-100)

# Earth's rotation speed: 360 degrees in 24 hours = 15 degrees/hour = 0.25 degrees/minute
ROTATION_SPEED_DEG_PER_MIN = -0.25

# Reference time for calculating rotation (first image in your sequence)
REF_HOUR = 00
REF_MINUTE = 00
REF_TOTAL_MINUTES = REF_HOUR * 60 + REF_MINUTE

# --- Script Logic ---

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# 1. Calculate Vermont's initial polar coordinates relative to the globe's center
#    Y-axis in image coordinates increases downwards.
INITIAL_VT_REL_X = INITIAL_VT_ABS_X - CENTER_X
INITIAL_VT_REL_Y = INITIAL_VT_ABS_Y - CENTER_Y

# Radial distance from the center (will remain constant)
R = math.sqrt(INITIAL_VT_REL_X**2 + INITIAL_VT_REL_Y**2)

# Initial angle (in radians) from the positive X-axis (standard math quadrant)
# atan2(y, x) returns angle in radians between -pi and pi.
INITIAL_ANGLE_RAD = math.atan2(INITIAL_VT_REL_Y, INITIAL_VT_REL_X)

print(f"Calculated initial polar coordinates for Vermont (relative to center):")
print(f"  Radius (R): {R:.2f} pixels")
print(f"  Initial Angle (radians): {INITIAL_ANGLE_RAD:.2f} (approx {math.degrees(INITIAL_ANGLE_RAD):.2f} degrees)")
print(f"  (Relative X: {INITIAL_VT_REL_X}, Relative Y: {INITIAL_VT_REL_Y})")
print(f"Processing images. Output will be in '{OUTPUT_DIR}' directory.")

# Get all relevant image files, sorted by time
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
    # CHANGED: Output filename now matches original, but goes into OUTPUT_DIR
    output_path = os.path.join(OUTPUT_DIR, image_filename)

    match = re.match(IMAGE_PATTERN, image_filename)
    current_hour = int(match.group(1))
    current_minute = int(match.group(2))
    current_total_minutes = current_hour * 60 + current_minute

    # Calculate total minutes elapsed from the reference time
    minutes_from_base = current_total_minutes - REF_TOTAL_MINUTES

    # Calculate total rotation for this frame in degrees (clockwise)
    # Clockwise rotation means we SUBTRACT from the initial angle.
    rotation_degrees = minutes_from_base * ROTATION_SPEED_DEG_PER_MIN
    rotation_radians = math.radians(rotation_degrees)

    # Calculate the current angle for Vermont
    current_angle_rad = INITIAL_ANGLE_RAD - rotation_radians

    # Calculate new relative (x, y) coordinates for Vermont using updated angle
    current_vt_rel_x = R * math.cos(current_angle_rad)
    current_vt_rel_y = R * math.sin(current_angle_rad)

    # Convert relative coordinates back to absolute image coordinates
    # (Y-axis increases downwards in image coordinate system)
    current_vt_abs_x = int(round(CENTER_X + current_vt_rel_x))
    current_vt_abs_y = int(round(CENTER_Y + current_vt_rel_y))

    print(f"Processing {image_filename} (Time: {current_hour:02d}:{current_minute:02d}):")
    print(f"  Rotation from base: {rotation_degrees:.2f} deg. Current Vermont at ({current_vt_abs_x}, {current_vt_abs_y})")

    # ImageMagick command for adding the glowing dot (using 'convert' and mpr: for IM6)
    magick_command = [
        "convert",
        str(input_path), # Load the original image FIRST to operate on it

        # Create glow layer (transparent background) and store in memory register 'mpr:glow'
        "(",
            "-size", f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}", "canvas:none", # Transparent canvas for glow
            "-fill", f"rgba(255,255,255,{GLOW_OPACITY/100.0})", # Use RGBA for transparency
            "-draw", f"circle {current_vt_abs_x},{current_vt_abs_y} {current_vt_abs_x},{current_vt_abs_y + DOT_RADIUS}",
            "-blur", f"0x{GLOW_SIGMA}", # Apply blur
            "+write", "mpr:glow", # Write to memory register 'glow'
            "+delete", # Delete this temporary image from the current pipeline
        ")",

        # Now, composite the original image with the glow layer
        "mpr:glow", # Recall glow from memory
        "-composite", # Composite glow onto the original image (which is the current image in the pipeline)

        # Create solid red dot layer (transparent background) and store in memory register 'mpr:dot'
        "(",
            "-size", f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}", "canvas:none", # Transparent canvas for the dot
            "-fill", DOT_COLOR, # Solid red
            "-draw", f"circle {current_vt_abs_x},{current_vt_abs_y} {current_vt_abs_x},{current_vt_abs_y + DOT_RADIUS}",
            "+write", "mpr:dot", # Write to memory register 'dot'
            "+delete", # Delete this temporary image from the current pipeline
        ")",

        # Finally, composite the red dot onto the result (original + glow)
        "mpr:dot", # Recall dot from memory
        "-composite", # Composite dot onto the combined original+glow image

        str(output_path) # Save final output
    ]

    try:
        # Execute the ImageMagick command
        subprocess.run(magick_command, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: 'convert' command not found. Please ensure ImageMagick is installed and in your system's PATH.")
        break
    except subprocess.CalledProcessError as e:
        print(f"Error processing {image_filename}:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        break
    except Exception as e:
        print(f"An unexpected error occurred for {image_filename}: {e}")
        break

print("--- Script Finished ---")
print(f"Processed images saved to '{OUTPUT_DIR}' directory.")
print("Please check the 'INITIAL_VT_ABS_X' and 'INITIAL_VT_ABS_Y' in the script if the dot position is off.")
