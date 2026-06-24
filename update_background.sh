#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

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
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/src/black_mode.py" --base-globe "$SCRIPT_DIR/src/images/base_globe_with_dot.png" --overlay "$SCRIPT_DIR/src/images/stationary_overlay.png" --temp-dir "$FRAME_DIR" --update-interval 5 >> "$LOG_FILE" 2>&1

# Log the current frame
echo "Current frame exists: $(test -f "$FRAME_DIR/current_frame.png" && echo 'yes' || echo 'no')" >> "$LOG_FILE"
echo "Current frame size: $(ls -l "$FRAME_DIR/current_frame.png" 2>/dev/null || echo 'not found')" >> "$LOG_FILE"

# Copy the current frame to a new timestamped file
cp "$FRAME_DIR/current_frame.png" "$NEW_FRAME"
echo "Created new frame: $NEW_FRAME" >> "$LOG_FILE"

# Update the symlink
ln -sf "$NEW_FRAME" "$FRAME_DIR/current_frame.png"
echo "Updated symlink" >> "$LOG_FILE"

# Update the background using feh. After GPU/driver changes, X may be :1 instead of :0.
pick_display() {
    local sock n
    if [[ -n "${DISPLAY:-}" ]]; then
        sock="/tmp/.X11-unix/X${DISPLAY#:}"
        if [[ -S "$sock" ]]; then
            return 0
        fi
    fi
    for sock in /tmp/.X11-unix/X[0-9]*; do
        [[ -S "$sock" ]] || continue
        n="${sock##*/X}"
        export DISPLAY=:${n}
        return 0
    done
    return 1
}
pick_display || true

# In GDM + i3 sessions, the valid cookie is often in /run/user/<uid>/gdm/Xauthority
# (not ~/.Xauthority). Pick the first existing candidate.
pick_xauthority() {
    local uid candidate
    uid="$(id -u)"
    for candidate in \
        "/run/user/${uid}/gdm/Xauthority" \
        "$HOME/.Xauthority"; do
        if [[ -f "$candidate" ]]; then
            export XAUTHORITY="$candidate"
            return 0
        fi
    done
    return 1
}
pick_xauthority || true
feh --image-bg black --bg-max "$NEW_FRAME"
echo "Updated background using feh" >> "$LOG_FILE"

echo "$(date): Background update complete" >> "$LOG_FILE"
