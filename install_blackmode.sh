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
    pip3 install "$1" >/dev/null 2>&1
}

# Check for required system packages
echo "Checking required system packages..."

# Check for Python 3
if ! command_exists python3; then
    echo "Python 3 is required but not installed."
    echo "Please install it with: sudo apt-get install python3"
    exit 1
fi

# Check for pip3
if ! command_exists pip3; then
    echo "pip3 is required but not installed."
    echo "Please install it with: sudo apt-get install python3-pip"
    exit 1
fi

# Check for feh (required for setting background in i3)
if ! command_exists feh; then
    echo "feh is required for setting the background in i3."
    echo "Would you like to install it? (y/n)"
    read -r install_feh
    if [ "$install_feh" = "y" ] || [ "$install_feh" = "Y" ]; then
        sudo apt-get install feh
    else
        echo "Error: feh is required for this script to work."
        exit 1
    fi
fi

# Check for xdotool (optional, for click-to-position feature)
if ! command_exists xdotool; then
    echo "xdotool is recommended for the click-to-position feature."
    echo "Would you like to install it? (y/n)"
    read -r install_xdotool
    if [ "$install_xdotool" = "y" ] || [ "$install_xdotool" = "Y" ]; then
        sudo apt-get install xdotool
    fi
fi

# Check for required Python packages
echo "Checking required Python packages..."

# Check and install Pillow if needed
if ! check_python_package "PIL"; then
    echo "Installing Pillow..."
    install_python_package "Pillow"
fi

# Check and install numpy if needed
if ! check_python_package "numpy"; then
    echo "Installing numpy..."
    install_python_package "numpy"
fi

# Check and install matplotlib if needed
if ! check_python_package "matplotlib"; then
    echo "Installing matplotlib..."
    install_python_package "matplotlib"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p src/images
mkdir -p /tmp/randall-clock

# Copy the base globe and overlay images if they don't exist
if [ ! -f "src/images/base_globe.png" ]; then
    echo "Error: base_globe.png not found in src/images/"
    exit 1
fi

if [ ! -f "src/images/stationary_overlay.png" ]; then
    echo "Error: stationary_overlay.png not found in src/images/"
    exit 1
fi

# Get user's location for the red dot
echo "You will now be prompted to click your location on the globe."
echo "This will be used to place the red dot on the clock."
echo "Press Enter when ready..."
read -r

# Run the location picker
python3 src/scripts/pick_location.py

# Read coordinates from config.ini
x=$(python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c['LOCATION']['x'])")
y=$(python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c['LOCATION']['y'])")

# Create the base globe with red dot
echo "Creating base globe with red dot..."
python3 src/black_mode.py --base-globe src/images/base_globe.png --overlay src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --create-base --dot-x "$x" --dot-y "$y"

# Verify the base globe with dot was created
if [ ! -f "src/images/base_globe_with_dot.png" ]; then
    echo "Error: Failed to create base_globe_with_dot.png"
    exit 1
fi

# Generate the first frame
echo "Generating the first frame..."
python3 src/black_mode.py --base-globe src/images/base_globe_with_dot.png --overlay src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --use-red-dot

# Verify the first frame was created
if [ ! -f "/tmp/randall-clock/current_frame.png" ]; then
    echo "Error: Failed to generate first frame"
    exit 1
fi

# Create a symbolic link to the current frame
ln -sf /tmp/randall-clock/current_frame.png ~/current_frame.png

# Set up the background update script
echo "Setting up background update script..."
cat > timeupdate.bash << 'EOF'
#!/bin/bash

# Set background to the current frame
feh --image-bg black --bg-max "/tmp/randall-clock/current_frame.png"
EOF
chmod +x timeupdate.bash

# Set up the cron jobs
echo "Setting up automatic updates..."

# Create a temporary file for the new crontab
temp_crontab=$(mktemp)

# Get current crontab and remove any existing clock-related jobs
crontab -l 2>/dev/null | grep -v "randall-clock-desktop-background" > "$temp_crontab"

# Add our new cron jobs
echo "*/1 * * * * $(pwd)/src/black_mode.py --base-globe $(pwd)/src/images/base_globe_with_dot.png --overlay $(pwd)/src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --use-red-dot" >> "$temp_crontab"
echo "*/1 * * * * $(pwd)/timeupdate.bash" >> "$temp_crontab"

# Install the new crontab
crontab "$temp_crontab"

# Clean up
rm "$temp_crontab"

# Set the initial background
./timeupdate.bash

echo "Installation complete!"
echo "The background will update every minute."
echo "You can find the current frame at: /tmp/randall-clock/current_frame.png" 