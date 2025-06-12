#!/bin/bash

# Read config.ini
CONFIG="config.ini"
STYLE=$(awk -F' *= *' '/^image_style *=/ {print $2}' "$CONFIG")
INTERVAL=$(awk -F' *= *' '/^interval *=/ {print $2}' "$CONFIG")
USE_REDDOT=0
if grep -q "RedDot" "$CONFIG"; then
    USE_REDDOT=$(awk -F' *= *' '/^RedDot *=/ {print $2}' "$CONFIG")
fi

# Determine image directory
if [[ "$STYLE" == "black" && "$INTERVAL" == "1m" ]]; then
    BASEDIR="src/images/intervals1m/blackGreenOverlay"
    REDDIR="src/images/intervals1m/blackGreenOverlayRedDot"
elif [[ "$STYLE" == "black" && "$INTERVAL" == "15m" ]]; then
    BASEDIR="src/images/intervals15m/blackGlobeGreenOverlay"
    REDDIR="src/images/intervals15m/blackGlobeGreenOverlayRedDot"
elif [[ "$STYLE" == "xkcd" ]]; then
    BASEDIR="src/images/intervals15m/xkcdOriginal"
    REDDIR="src/images/intervals15m/xkcdOriginalRedDot"
fi

if [[ "$USE_REDDOT" == "1" && -d "$REDDIR" ]]; then
    IMGDIR="$REDDIR"
else
    IMGDIR="$BASEDIR"
fi

# Get current UTC time and apply 8-hour offset
HOUR=$(date -u +%H)
MIN=$(date -u +%M)

# Subtract 8 hours, wrap around if negative
HOUR=$(( (10#$HOUR - 8 + 24) % 24 ))

# Round down to nearest interval
if [[ "$INTERVAL" == "15m" ]]; then
    MIN=$((MIN - MIN % 15))
    printf -v MIN "%02d" $MIN
fi

IMGFILE=$(printf "%02dh%02dm.png" "$HOUR" "$MIN")
IMG="$IMGDIR/$IMGFILE"

# Set background
feh --image-bg black --bg-max "$IMG" 