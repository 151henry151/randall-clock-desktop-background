#!/bin/bash

# Create frame directory if it doesn't exist
FRAME_DIR="/tmp/randall-clock"
mkdir -p "$FRAME_DIR"

# Log file for debugging
LOG_FILE="$FRAME_DIR/update_background.log"

# Log the start of the update
echo "$(date): Starting background update" >> "$LOG_FILE"

# Create timestamped filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEW_FRAME="$FRAME_DIR/frame_${TIMESTAMP}.png"

# Generate new frame
echo "Generating new frame..." >> "$LOG_FILE"
/home/henry/randall-clock-desktop-background/venv/bin/python3 /home/henry/randall-clock-desktop-background/src/black_mode.py --base-globe /home/henry/randall-clock-desktop-background/src/images/base_globe_with_dot.png --overlay /home/henry/randall-clock-desktop-background/src/images/stationary_overlay.png --temp-dir "$FRAME_DIR" --update-interval 5 >> "$LOG_FILE" 2>&1

# Log the current frame
echo "Current frame exists: $(test -f "$FRAME_DIR/current_frame.png" && echo 'yes' || echo 'no')" >> "$LOG_FILE"
echo "Current frame size: $(ls -l "$FRAME_DIR/current_frame.png" 2>/dev/null || echo 'not found')" >> "$LOG_FILE"

# Copy the current frame to a new timestamped file
cp "$FRAME_DIR/current_frame.png" "$NEW_FRAME"
echo "Created new frame: $NEW_FRAME" >> "$LOG_FILE"

# Update the symlink
ln -sf "$NEW_FRAME" "$FRAME_DIR/current_frame.png"
echo "Updated symlink" >> "$LOG_FILE"

# Update the background using feh
export DISPLAY=:0
export XAUTHORITY=/home/henry/.Xauthority
feh --image-bg black --bg-max "$NEW_FRAME"
echo "Updated background using feh" >> "$LOG_FILE"

echo "$(date): Background update complete" >> "$LOG_FILE"
