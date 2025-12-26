#!/usr/bin/env python3

import os
import math
from PIL import Image, ImageDraw, ImageOps
import numpy as np
from datetime import datetime, timezone, timedelta
import configparser
import logging

# Set up logging
logging.basicConfig(
    filename='/tmp/randall-clock/black_mode.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class BlackModeGenerator:
    def __init__(self, base_globe_path, overlay_path, temp_dir, use_red_dot=False):
        self.base_globe_path = base_globe_path
        self.overlay_path = overlay_path
        self.temp_dir = temp_dir
        self.use_red_dot = use_red_dot
        
        # Create temp directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)
        
        # Load base images
        self.globe = Image.open(base_globe_path).convert('RGBA')
        self.overlay = Image.open(overlay_path).convert('RGBA')
        
        # Create a mask for the globe (assuming the globe is the non-transparent part)
        globe_array = np.array(self.globe)
        mask_array = (globe_array[..., 3] > 0).astype(np.uint8) * 255
        self.globe_mask = Image.fromarray(mask_array, 'L')
        
        # Get globe center from config
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
        logging.info(f"Reading config from: {config_path}")
        config.read(config_path)
        self.globe_center_x = int(config['BLACK_GLOBE']['center_x'])
        self.globe_center_y = int(config['BLACK_GLOBE']['center_y'])
        
        logging.info(f"Initialized BlackModeGenerator with base_globe={base_globe_path}, overlay={overlay_path}, temp_dir={temp_dir}")
    
    def calculate_rotation(self):
        """Calculate the rotation angle based on current time."""
        # Get current UTC time
        now = datetime.now(timezone.utc)
        
        # Calculate total seconds since midnight UTC
        total_seconds = now.hour * 3600 + now.minute * 60 + now.second
        
        # Convert to degrees (360 degrees / 24 hours / 60 minutes / 60 seconds)
        # The 195-degree offset (13 hours) is a fixed correction that aligns our clock's
        # orientation with actual UTC time. This offset is independent of the current time
        # and will work correctly for any time of day.
        degrees = (total_seconds * 360 / (24 * 3600)) + 195
        
        # Ensure we're rotating clockwise and 0 is at 12 o'clock
        rotation = -degrees  # Negative for clockwise rotation
        logging.info(f"Calculated rotation angle: {rotation} degrees for time {now}")
        return rotation
    
    def generate_frame(self, hour, minute):
        """Generate a frame for the specified time."""
        logging.info(f"Generating frame for {hour:02d}:{minute:02d}")
        
        # Calculate rotation angle
        rotation = self.calculate_rotation()
        
        # Extract globe using mask
        globe_only = Image.composite(self.globe, Image.new('RGBA', self.globe.size, (0,0,0,0)), self.globe_mask)
        
        # Create a transparent background for rotation
        rotated_globe = Image.new('RGBA', self.globe.size, (0,0,0,0))
        
        # Rotate the globe with transparent background
        rotated_globe.paste(
            globe_only.rotate(rotation, resample=Image.BICUBIC, center=(self.globe.width//2, self.globe.height//2), expand=False),
            (0, 0)
        )
        
        # DEBUG: Save the rotated globe before compositing
        debug_path = os.path.join(self.temp_dir, f"debug_rotated_globe_{hour:02d}h{minute:02d}m.png")
        rotated_globe.save(debug_path)
        logging.info(f"Saved debug rotated globe to {debug_path}")
        
        # Create a transparent background
        final = Image.new('RGBA', self.overlay.size, (0,0,0,0))
        
        # Paste the rotated globe with a small vertical offset to move it down
        vertical_offset = 10  # Adjust this value to move the globe up or down
        final.paste(rotated_globe, (0, vertical_offset), rotated_globe)
        
        # Create a mask for the overlay (inverse of the globe mask)
        overlay_mask = ImageOps.invert(self.globe_mask)
        
        # Apply the overlay using the mask
        final.paste(self.overlay, (0, 0), overlay_mask)
        
        return final
    
    def generate_next_frame(self, update_interval=1):
        """Generate the next frame based on current time, aligned to the update interval."""
        # Get current local time
        now = datetime.now()
        logging.info(f"Generating frames for current time: {now} with interval: {update_interval} minutes")
        
        # Calculate the time aligned to the update interval
        # For example, if interval is 5 minutes and current time is 14:23,
        # we want to generate a frame for 14:20 (the most recent 5-minute boundary)
        aligned_minute = (now.minute // update_interval) * update_interval
        aligned_time = now.replace(minute=aligned_minute, second=0, microsecond=0)
        
        # Generate frame for the aligned time
        current_frame = self.generate_frame(aligned_time.hour, aligned_time.minute)
        
        # Generate next frame (next interval boundary)
        next_time = aligned_time + timedelta(minutes=update_interval)
        next_frame = self.generate_frame(next_time.hour, next_time.minute)
        
        # Save frames
        current_path = os.path.join(self.temp_dir, f"current_frame.png")
        next_path = os.path.join(self.temp_dir, f"next_frame.png")
        
        current_frame.save(current_path)
        next_frame.save(next_path)
        
        logging.info(f"Saved current frame (aligned to {aligned_time}) to {current_path}")
        logging.info(f"Saved next frame ({next_time}) to {next_path}")
        
        return current_path, next_path

    def add_red_dot(self, x, y, rotation_degrees=0):
        """Add a glowing red dot at the specified coordinates."""
        logging.info(f"Adding red dot at coordinates ({x}, {y})")
        # Create a new image with alpha channel for the dot
        dot_img = Image.new('RGBA', self.globe.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(dot_img)
        
        # Define the glow layers (radius, alpha)
        glow_layers = [
            (20, 40),   # Outer glow
            (15, 80),   # Middle glow
            (10, 120),  # Inner glow
            (5, 255)    # Core dot
        ]
        
        # Draw each layer of the glow
        for radius, alpha in glow_layers:
            # Create a semi-transparent red color
            color = (255, 0, 0, alpha)
            # Draw the circle
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color
            )
        
        # Composite the dot onto the globe
        self.globe = Image.alpha_composite(self.globe, dot_img)
        logging.info("Red dot added successfully")

def create_base_globe_with_dot(base_globe_path, x, y, output_path):
    """Create a base globe image with the red dot permanently placed at the specified coordinates."""
    logging.info(f"Creating base globe with red dot at ({x}, {y})")
    # Load the base globe
    base_globe = Image.open(base_globe_path).convert('RGBA')
    
    # Create a new image with alpha channel for the dot
    dot_img = Image.new('RGBA', base_globe.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(dot_img)
    
    # Define the glow layers (radius, alpha)
    glow_layers = [
        (20, 40),   # Outer glow
        (15, 80),   # Middle glow
        (10, 120),  # Inner glow
        (5, 255)    # Core dot
    ]
    
    # Draw each layer of the glow
    for radius, alpha in glow_layers:
        # Create a semi-transparent red color
        color = (255, 0, 0, alpha)
        # Draw the circle
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color
        )
    
    # Composite the dot onto the globe
    base_globe = Image.alpha_composite(base_globe, dot_img)
    
    # Save the result
    base_globe.save(output_path)
    logging.info(f"Created base globe with red dot at: {output_path}")
    print(f"Created base globe with red dot at ({x}, {y})")

def main():
    """Main function to be called from the bash script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate black mode clock frames')
    parser.add_argument('--base-globe', required=True, help='Path to base globe image')
    parser.add_argument('--overlay', required=True, help='Path to overlay image')
    parser.add_argument('--temp-dir', required=True, help='Path to temporary directory')
    parser.add_argument('--use-red-dot', action='store_true', help='Whether to use red dot')
    parser.add_argument('--create-base', action='store_true', help='Create base globe with red dot')
    parser.add_argument('--dot-x', type=int, help='X coordinate for red dot')
    parser.add_argument('--dot-y', type=int, help='Y coordinate for red dot')
    parser.add_argument('--update-interval', type=int, default=1, help='Update interval in minutes (default: 1)')
    
    args = parser.parse_args()
    logging.info(f"Starting black_mode.py with arguments: {args}")
    
    if args.create_base:
        if not args.dot_x or not args.dot_y:
            logging.error("Error: --dot-x and --dot-y are required when --create-base is used")
            print("Error: --dot-x and --dot-y are required when --create-base is used")
            return
        
        # Create the base globe with red dot
        base_with_dot = os.path.join(os.path.dirname(args.base_globe), 'base_globe_with_dot.png')
        create_base_globe_with_dot(args.base_globe, args.dot_x, args.dot_y, base_with_dot)
        print(f"Created base globe with red dot at: {base_with_dot}")
        return
    
    generator = BlackModeGenerator(
        args.base_globe,
        args.overlay,
        args.temp_dir,
        args.use_red_dot
    )
    
    current_path, next_path = generator.generate_next_frame(args.update_interval)
    print(f"Current frame: {current_path}")
    print(f"Next frame: {next_path}")

if __name__ == "__main__":
    main() 