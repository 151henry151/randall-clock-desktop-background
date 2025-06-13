import os
from PIL import Image

def extract_base_globe(input_image_path, output_image_path, center_x, center_y, radius):
    """Extract a properly sized base globe image from an existing frame."""
    # Load the input image
    img = Image.open(input_image_path)
    
    # Calculate the bounding box for the globe
    left = center_x - radius
    top = center_y - radius
    right = center_x + radius
    bottom = center_y + radius
    
    # Crop the image to the globe
    globe = img.crop((left, top, right, bottom))
    
    # Save the extracted globe
    globe.save(output_image_path)
    print(f"Base globe extracted and saved to {output_image_path}")

if __name__ == "__main__":
    # Example usage
    input_image = "globe_black00h00.png"  # Use the existing frame
    output_image = "src/images/base_globe.png"  # Save to the correct location
    center_x = 990  # from config.ini
    center_y = 988  # from config.ini
    radius = 491    # from config.ini
    
    extract_base_globe(input_image, output_image, center_x, center_y, radius) 