#!/bin/bash

# Set environment variables
export DISPLAY=:0
export XAUTHORITY=/home/henry/.Xauthority

# Log the environment
echo "Environment at $(date):" >> /tmp/cron_test.log
env >> /tmp/cron_test.log

# Try to set the background
feh --bg-fill /tmp/randall-clock/current_frame.png 2>> /tmp/cron_test.log 