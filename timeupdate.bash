#!/bin/bash
DISPLAY=:0
hour=$(date -d "7 hours ago" +%H)
min=$(date -d "7 hours ago" +%M)
 
if [[ ! $((${min}%15)) -eq 0 ]]; then
	        min=$((${min}-$((${min}%15))))
	fi
	 
	feh --image-bg white --bg-center "/home/username/randall-clock-desktop-background/now/${hour}h${min}m.png"
