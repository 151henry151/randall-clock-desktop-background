#!/bin/bash

# Set up environment
export DISPLAY=:0
export XAUTHORITY=/home/henry/.Xauthority
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Log file for debugging
LOG_FILE="/tmp/randall-clock/update_background.log"
mkdir -p /tmp/randall-clock

# Log the start of the update with a clear CRON marker
echo "==========================================" >> "$LOG_FILE"
echo "CRON JOB RUN AT $(date)" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

# Create timestamped filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FRAME_DIR="/tmp/randall-clock"
NEW_FRAME="$FRAME_DIR/frame_${TIMESTAMP}.png"

# Log the current frame
echo "Current frame exists: $(test -f "$FRAME_DIR/current_frame.png" && echo 'yes' || echo 'no')" >> "$LOG_FILE"
echo "Current frame size: $(ls -l "$FRAME_DIR/current_frame.png" 2>/dev/null || echo 'not found')" >> "$LOG_FILE"

# Copy the current frame to a new timestamped file
cp "$FRAME_DIR/current_frame.png" "$NEW_FRAME"
echo "Created new frame: $NEW_FRAME" >> "$LOG_FILE"

# Update the symlink
ln -sf "$NEW_FRAME" "$FRAME_DIR/current_frame.png"
echo "Updated symlink" >> "$LOG_FILE"

# Try to set the background using dbus-launch
dbus-launch gsettings set org.gnome.desktop.background picture-uri "file://$NEW_FRAME" 2>> "$LOG_FILE"
echo "Ran gsettings command with dbus-launch" >> "$LOG_FILE"

# If gsettings fails, try feh
if [ $? -ne 0 ]; then
    dbus-launch feh --image-bg black --bg-max "$NEW_FRAME" 2>> "$LOG_FILE"
    echo "Ran feh command with dbus-launch" >> "$LOG_FILE"
fi

echo "$(date): Background update complete" >> "$LOG_FILE"
