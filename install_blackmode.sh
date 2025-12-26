#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a Python package is installed in venv
check_python_package() {
    /home/henry/randall-clock-desktop-background/venv/bin/python3 -c "import $1" >/dev/null 2>&1
}

# Function to install Python package in venv
install_python_package() {
    echo "Installing $1..."
    /home/henry/randall-clock-desktop-background/venv/bin/pip3 install "$1" >/dev/null 2>&1
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

# Check for feh (required for setting background)
if ! command_exists feh; then
    echo "feh is required for setting the background."
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

# Get update interval from user
echo "How often should the clock update? (in minutes)"
echo "Enter a number between 1 and 60 (e.g., 1, 3, 5, 15):"
read -r update_interval

# Validate input
if ! [[ "$update_interval" =~ ^[1-9][0-9]*$ ]] || [ "$update_interval" -gt 60 ]; then
    echo "Error: Please enter a valid number between 1 and 60"
    exit 1
fi

echo "Clock will update every $update_interval minute(s)"

# Get user's location for the red dot
echo "You will now be prompted to click your location on the globe."
echo "This will be used to place the red dot on the clock."
echo "Press Enter to continue, or 's' to skip and use previous location..."
read -r response

if [ "$response" = "s" ] || [ "$response" = "S" ]; then
    if [ -f "config.ini" ]; then
        echo "Using previous location from config.ini"
    else
        echo "Error: No previous location found in config.ini"
        exit 1
    fi
else
    # Run the location picker
    /home/henry/randall-clock-desktop-background/venv/bin/python3 src/scripts/pick_location.py
fi

# Read coordinates from config.ini
x=$(/home/henry/randall-clock-desktop-background/venv/bin/python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c['LOCATION']['x'])")
y=$(/home/henry/randall-clock-desktop-background/venv/bin/python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c['LOCATION']['y'])")

# Add update interval to config.ini
/home/henry/randall-clock-desktop-background/venv/bin/python3 -c "
import configparser
c = configparser.ConfigParser()
c.read('config.ini')
if 'DEFAULT' not in c:
    c['DEFAULT'] = {}
c['DEFAULT']['update_interval'] = '$update_interval'
with open('config.ini', 'w') as f:
    c.write(f)
"

# Create the base globe with red dot
echo "Creating base globe with red dot..."
/home/henry/randall-clock-desktop-background/venv/bin/python3 src/black_mode.py --base-globe src/images/base_globe.png --overlay src/images/stationary_overlay.png --temp-dir /tmp/randall-clock --create-base --dot-x "$x" --dot-y "$y"

# Verify the base globe with dot was created
if [ ! -f "src/images/base_globe_with_dot.png" ]; then
    echo "Error: Failed to create base_globe_with_dot.png"
    exit 1
fi

# Set up the background update script
echo "Setting up background update script..."
cat > update_background.sh << EOF
#!/bin/bash

# Log file for debugging
LOG_FILE="/tmp/randall-clock/update_background.log"

# Log the start of the update
echo "\$(date): Starting background update" >> "\$LOG_FILE"

# Create timestamped filename
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
FRAME_DIR="/tmp/randall-clock"
NEW_FRAME="\$FRAME_DIR/frame_\${TIMESTAMP}.png"

# Generate new frame
echo "Generating new frame..." >> "\$LOG_FILE"
/home/henry/randall-clock-desktop-background/venv/bin/python3 /home/henry/randall-clock-desktop-background/src/black_mode.py --base-globe /home/henry/randall-clock-desktop-background/src/images/base_globe_with_dot.png --overlay /home/henry/randall-clock-desktop-background/src/images/stationary_overlay.png --temp-dir "\$FRAME_DIR" --update-interval $update_interval >> "\$LOG_FILE" 2>&1

# Log the current frame
echo "Current frame exists: \$(test -f "\$FRAME_DIR/current_frame.png" && echo 'yes' || echo 'no')" >> "\$LOG_FILE"
echo "Current frame size: \$(ls -l "\$FRAME_DIR/current_frame.png" 2>/dev/null || echo 'not found')" >> "\$LOG_FILE"

# Copy the current frame to a new timestamped file
cp "\$FRAME_DIR/current_frame.png" "\$NEW_FRAME"
echo "Created new frame: \$NEW_FRAME" >> "\$LOG_FILE"

# Update the symlink
ln -sf "\$NEW_FRAME" "\$FRAME_DIR/current_frame.png"
echo "Updated symlink" >> "\$LOG_FILE"

# Update the background using feh
export DISPLAY=:0
export XAUTHORITY=/home/henry/.Xauthority
feh --image-bg black --bg-max "\$NEW_FRAME"
echo "Updated background using feh" >> "\$LOG_FILE"

echo "\$(date): Background update complete" >> "\$LOG_FILE"
EOF

chmod +x update_background.sh

# Set up the cron jobs
echo "Setting up automatic updates..."

# Create a temporary file for the new crontab
temp_crontab=$(mktemp)

# Get current crontab and remove any existing clock-related jobs
crontab -l 2>/dev/null | grep -v "randall-clock-desktop-background" > "$temp_crontab"

# Add our new cron jobs
echo "*/$update_interval * * * * $(pwd)/update_background.sh" >> "$temp_crontab"

# Install the new crontab
crontab "$temp_crontab"

# Clean up
rm "$temp_crontab"

# Set the initial background
./update_background.sh

echo "Installation complete!"
echo "The background will update every $update_interval minute(s)."
echo "You can find the current frame at: /tmp/randall-clock/current_frame.png" 