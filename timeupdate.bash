#!/bin/bash
export DISPLAY=:0
# adjust "04 hours ago" to account for your time zone
hour=$(date -d "04 hours ago" +%H)
min=$(date -d "04 hours ago" +%M)
 
if [[ ! $((${min}%15)) -eq 0 ]]; then
      min=$((${min}-$((${min}%15))))
fi

if [[ $min == 0 ]]; then
      min="00";
fi

# replace "henry" with your username below
feh --image-bg white --bg-center "/home/henry/randall-clock-desktop-background/now/${hour}h${min}m.png"
