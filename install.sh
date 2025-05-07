#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get timezone offset in hours
get_timezone_offset() {
    # Get the local timezone offset in hours
    local tz_offset
    tz_offset=$(date +%z | sed 's/^+//' | sed 's/00$//')
    if [[ ${tz_offset:0:1} == "-" ]]; then
        echo "${tz_offset:1:2}"
    else
        echo "-${tz_offset:0:2}"
    fi
}

echo "Installing XKCD Clock Desktop Background..."

# Check if running as root and exit if so
if [ "$(id -u)" = "0" ]; then
    echo "This script should not be run as root. Please run as a normal user."
    exit 1
fi

# Get the username
USERNAME=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install feh if not already installed
if ! command_exists feh; then
    echo "Installing feh..."
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y feh
    elif command_exists pacman; then
        sudo pacman -S --noconfirm feh
    elif command_exists dnf; then
        sudo dnf install -y feh
    else
        echo "Error: Could not find a supported package manager. Please install feh manually."
        exit 1
    fi
fi

# Get timezone offset
TZ_OFFSET=$(get_timezone_offset)

# Update the scripts with correct timezone and username
for script in "$SCRIPT_DIR"/timeupdate.bash "$SCRIPT_DIR"/blk_timeupdate.bash; do
    if [ -f "$script" ]; then
        # Make backup of original script
        cp "$script" "${script}.bak"
        
        # Update timezone and username in the script
        sed -i "s/7 hours ago/${TZ_OFFSET} hours ago/" "$script"
        sed -i "s|/home/henry/|/home/${USERNAME}/|g" "$script"
        sed -i "s/henry/${USERNAME}/g" "$script"
        
        # Make script executable
        chmod +x "$script"
    fi
done

# Ask user which version they prefer
echo
echo "Which version would you like to use?"
echo "1) Regular (white background)"
echo "2) Black background"
read -p "Enter choice [1/2]: " choice

case $choice in
    1)
        SCRIPT_PATH="$SCRIPT_DIR/timeupdate.bash"
        ;;
    2)
        SCRIPT_PATH="$SCRIPT_DIR/blk_timeupdate.bash"
        ;;
    *)
        echo "Invalid choice. Defaulting to regular version."
        SCRIPT_PATH="$SCRIPT_DIR/timeupdate.bash"
        ;;
esac

# Add or update cron job
(crontab -l 2>/dev/null | grep -v "randall-clock-desktop-background" ; echo "*/15 * * * * $SCRIPT_PATH") | crontab -

echo "Installation complete! Running initial update..."

# Run the script immediately for first update
$SCRIPT_PATH

echo "Your desktop background should now be updated with the XKCD clock."
echo "It will automatically update every 15 minutes." 