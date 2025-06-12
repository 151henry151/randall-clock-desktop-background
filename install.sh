#!/bin/bash

set -e

echo "Welcome to the Randall Clock Desktop Background Installer!"

# 1. Dependency check (suppress output)
echo "Checking for required dependencies..."
missing_deps=()
command -v feh >/dev/null 2>&1 || missing_deps+=("feh")
command -v convert >/dev/null 2>&1 || missing_deps+=("imagemagick")
command -v python3 >/dev/null 2>&1 || missing_deps+=("python3")
command -v pip3 >/dev/null 2>&1 || missing_deps+=("python3-pip")
if ! dpkg -l | grep -q "python3-tk"; then missing_deps+=("python3-tk"); fi
if ! dpkg -l | grep -q "python3-pil"; then missing_deps+=("python3-pil"); fi
if ! dpkg -l | grep -q "python3-numpy"; then missing_deps+=("python3-numpy"); fi

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo "The following dependencies are missing and need to be installed:"
    echo "${missing_deps[@]}"
    echo "Running: sudo apt-get install -y ${missing_deps[@]}"
    read -p "Press Enter to continue with installation (requires sudo)..."
    sudo apt-get install -y "${missing_deps[@]}" >/dev/null 2>&1
fi

pip3 install -r requirements.txt >/dev/null 2>&1

CONFIG=config.ini

# Remove duplicate RedDot, image_style, and interval from all sections except [DEFAULT]
sed -i '/\[.*\]/!b;:a;n;/^RedDot *=/d;ba' "$CONFIG"
sed -i '/\[.*\]/!b;:a;n;/^image_style *=/d;ba' "$CONFIG"
sed -i '/\[.*\]/!b;:a;n;/^interval *=/d;ba' "$CONFIG"

# 2. Red dot prompt
read -p "Do you want a red dot to indicate your location? (y/n): " red_dot

if [[ "$red_dot" =~ ^[Yy]$ ]]; then
    # Only run pick-location.py if location is not set
    if ! grep -q "^x *=" "$CONFIG" || ! grep -q "^y *=" "$CONFIG"; then
        echo "Please pick your location on the XKCD globe..."
        python3 src/scripts/pick-location.py
    fi
    # Only run measure-globe.py if globe measurements are missing
    if ! grep -q "\[XKCD_GLOBE\]" "$CONFIG" || ! grep -q "\[BLACK_GLOBE\]" "$CONFIG"; then
        echo "Measuring globe radii (developer/advanced use only)..."
        python3 src/scripts/measure-globe.py
    fi
    # Mark in config that red dot is desired (in [DEFAULT])
    if grep -q "^RedDot" "$CONFIG"; then
        sed -i '/^RedDot *=/d' "$CONFIG"
    fi
    sed -i '/^\[DEFAULT\]/a RedDot = 1' "$CONFIG" || echo -e "[DEFAULT]\nRedDot = 1" >> "$CONFIG"
else
    if grep -q "^RedDot" "$CONFIG"; then
        sed -i '/^RedDot *=/d' "$CONFIG"
    fi
    sed -i '/^\[DEFAULT\]/a RedDot = 0' "$CONFIG" || echo -e "[DEFAULT]\nRedDot = 0" >> "$CONFIG"
fi

# 4. Clock style prompt
echo "Which clock style do you want?"
select style in "black" "xkcd"; do
    case $style in
        black ) clock_style="black"; break;;
        xkcd ) clock_style="xkcd"; break;;
    esac
done

# 5. Interval prompt
echo "Which interval do you want?"
select interval in "1m" "15m"; do
    case $interval in
        1m ) clock_interval="1m"; break;;
        15m ) clock_interval="15m"; break;;
    esac
done

# Update config.ini with style and interval in [DEFAULT]
sed -i '/^image_style *=/d' "$CONFIG"
sed -i '/^interval *=/d' "$CONFIG"
sed -i '/^\[DEFAULT\]/a image_style = '$clock_style'\ninterval = '$clock_interval'' "$CONFIG" || echo -e "[DEFAULT]\nimage_style = $clock_style\ninterval = $clock_interval" >> "$CONFIG"

# 6. Generate base frames if needed
if [[ "$clock_style" == "black" && "$clock_interval" == "1m" ]]; then
    BASEDIR="src/images/intervals1m/blackGreenOverlay"
    if [ ! -d "$BASEDIR" ] || [ -z "$(ls -A $BASEDIR 2>/dev/null)" ]; then
        echo "Generating base 1m black clock frames..."
        python3 src/scripts/generate-frames.py
        echo "Base frames saved to: $BASEDIR"
    fi
elif [[ "$clock_style" == "black" && "$clock_interval" == "15m" ]]; then
    BASEDIR="src/images/intervals15m/blackGlobeGreenOverlay"
    if [ ! -d "$BASEDIR" ] || [ -z "$(ls -A $BASEDIR 2>/dev/null)" ]; then
        echo "Generating base 15m black clock frames..."
        python3 src/scripts/generate-frames.py
        echo "Base frames saved to: $BASEDIR"
    fi
elif [[ "$clock_style" == "xkcd" ]]; then
    BASEDIR="src/images/intervals15m/xkcdOriginal"
    # Assume XKCD frames are already present
    echo "Using XKCD original frames in: $BASEDIR"
fi

# 7. Generate red dot images if needed
if [[ "$red_dot" =~ ^[Yy]$ ]]; then
    echo "Adding red dot to clock frames..."
    python3 src/scripts/red-dot.py
    if [[ "$clock_style" == "black" && "$clock_interval" == "1m" ]]; then
        REDDIR="src/images/intervals1m/blackGreenOverlayRedDot"
    elif [[ "$clock_style" == "black" && "$clock_interval" == "15m" ]]; then
        REDDIR="src/images/intervals15m/blackGlobeGreenOverlayRedDot"
    elif [[ "$clock_style" == "xkcd" ]]; then
        REDDIR="src/images/intervals15m/xkcdOriginalRedDot"
    fi
    echo "Red dot images saved to: $REDDIR"
else
    echo "No red dot selected. Using base clock images."
fi

# 8. Set up background update (using new timeupdate.bash)
chmod +x timeupdate.bash

# Remove any old cron jobs for this script
crontab -l 2>/dev/null | grep -v "timeupdate.bash" | crontab -

# Add new cron job for the selected interval
if [[ "$clock_interval" == "1m" ]]; then
    (crontab -l 2>/dev/null; echo "* * * * * $(pwd)/timeupdate.bash") | crontab -
else
    (crontab -l 2>/dev/null; echo "*/15 * * * * $(pwd)/timeupdate.bash") | crontab -
fi

echo "Installation complete! Running initial update..."

# Run the script immediately for first update
./timeupdate.bash

echo "Your desktop background should now be updated with the Randall Clock."
echo "It will automatically update every $clock_interval." 