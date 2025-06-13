#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a Python package is installed
check_python_package() {
    python3 -c "import $1" >/dev/null 2>&1
}

# Function to install Python package
install_python_package() {
    echo "Installing $1..."
    pip3 install "$1"
}

# Function to get user's location on the globe
get_user_location() {
    echo "Please click on your approximate location on the globe."
    echo "This will be used to place the red dot on the clock."
    echo "Press Enter when ready..."
    read -r
    
    # Use xdotool to get mouse position
    if command_exists xdotool; then
        # Wait for click
        while true; do
            if xdotool getmouselocation | grep -q "button1"; then
                # Get coordinates
                coords=$(xdotool getmouselocation | awk '{print $1 $2}' | tr -d 'xy:')
                x=$(echo "$coords" | cut -d' ' -f1)
                y=$(echo "$coords" | cut -d' ' -f2)
                break
            fi
            sleep 0.1
        done
    else
        echo "xdotool not found. Please install it to use the click-to-position feature."
        echo "For now, using default coordinates (center of image)."
        x=631
        y=857
    fi
    
    echo "Selected coordinates: x=$x, y=$y"
    return 0
}

# Check for required commands
echo "Checking for required commands..."

# Check for Python 3
if ! command_exists python3; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check for pip3
if ! command_exists pip3; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Check for required Python packages
echo "Checking for required Python packages..."

# Check and install Pillow if needed
if ! check_python_package "PIL"; then
    echo "Pillow is required but not installed."
    install_python_package "Pillow"
fi

# Check and install numpy if needed
if ! check_python_package "numpy"; then
    echo "numpy is required but not installed."
    install_python_package "numpy"
fi

# Check for xdotool (optional, for click-to-position feature)
if ! command_exists xdotool; then
    echo "Warning: xdotool not found. The click-to-position feature will not be available."
    echo "You can install it with: sudo apt-get install xdotool"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p src/images
mkdir -p /tmp/randall-clock

# Ask user which mode they want to use
echo "Which mode would you like to use?"
echo "1) XKCD mode (uses XKCD comics as background)"
echo "2) Black mode (uses a rotating globe with red dot)"
read -r -p "Enter your choice (1 or 2): " mode_choice

if [ "$mode_choice" = "2" ]; then
    # Black mode
    echo "Setting up black mode..."
    
    # Copy the base globe and overlay images
    cp src/images/base_globe.png src/images/base_globe_original.png
    cp src/images/stationary_overlay.png src/images/stationary_overlay_original.png
    
    # Get user's location for the red dot
    get_user_location
    
    # Create the base globe with red dot
    echo "Creating base globe with red dot..."
    python3 src/black_mode.py --base-globe src/images/base_globe.png --create-base --dot-x "$x" --dot-y "$y"
    
    # Update the base globe path to use the new version with red dot
    sed -i "s|base_globe.png|base_globe_with_dot.png|g" src/black_mode.py
    
    # Create a symbolic link to the current frame
    ln -sf /tmp/randall-clock/current_frame.png ~/current_frame.png
    
    # Set up the cron job for black mode
    (crontab -l 2>/dev/null; echo "*/1 * * * * $(pwd)/src/black_mode.py --base-globe $(pwd)/src/images/base_globe_with_dot.png --overlay $(pwd)/src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --use-red-dot") | crontab -
    
    # Set the initial background
    python3 src/black_mode.py --base-globe src/images/base_globe_with_dot.png --overlay src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --use-red-dot
    
    # Set up the background update script
    cat > update_background.sh << 'EOF'
#!/bin/bash
gsettings set org.gnome.desktop.background picture-uri "file:///tmp/randall-clock/current_frame.png"
EOF
    
    chmod +x update_background.sh
    
    # Add the background update to crontab
    (crontab -l 2>/dev/null; echo "*/1 * * * * $(pwd)/update_background.sh") | crontab -
    
    echo "Black mode setup complete!"
    echo "The background will update every minute."
    echo "You can find the current frame at: /tmp/randall-clock/current_frame.png"
else
    # XKCD mode
    echo "Setting up XKCD mode..."
    
    # Download the latest XKCD comic
    echo "Downloading the latest XKCD comic..."
    python3 src/download_xkcd.py
    
    # Create a symbolic link to the current frame
    ln -sf /tmp/randall-clock/current_frame.png ~/current_frame.png
    
    # Set up the cron job for XKCD mode
    (crontab -l 2>/dev/null; echo "0 */4 * * * $(pwd)/src/download_xkcd.py") | crontab -
    
    # Set the initial background
    gsettings set org.gnome.desktop.background picture-uri "file:///tmp/randall-clock/current_frame.png"
    
    # Set up the background update script
    cat > update_background.sh << 'EOF'
#!/bin/bash
gsettings set org.gnome.desktop.background picture-uri "file:///tmp/randall-clock/current_frame.png"
EOF
    
    chmod +x update_background.sh
    
    # Add the background update to crontab
    (crontab -l 2>/dev/null; echo "0 */4 * * * $(pwd)/update_background.sh") | crontab -
    
    echo "XKCD mode setup complete!"
    echo "The background will update every 4 hours."
    echo "You can find the current frame at: /tmp/randall-clock/current_frame.png"
fi

echo "Installation complete!" 