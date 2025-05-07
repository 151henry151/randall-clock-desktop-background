# randall-clock-desktop-background
Change desktop background using the XKCD now clock from https://xkcd.com/1335/

## Quick Installation

Simply run:
```bash
./install.sh
```

This will:
1. Automatically detect and install dependencies (feh)
2. Detect your timezone
3. Configure the scripts for your system
4. Set up the cron job
5. Run the initial update immediately

You can choose between two styles:
1. Regular (white background)
2. Black background

## Manual Installation
If you prefer to set things up manually:

1. Install feh:
   - Debian/Ubuntu: `sudo apt install feh`
   - Arch: `sudo pacman -S feh`
   - Fedora: `sudo dnf install feh`

2. Edit the timezone in either `timeupdate.bash` or `blk_timeupdate.bash`
   - Find the line with `"7 hours ago"` and adjust according to your timezone

3. Make the script executable:
   ```bash
   chmod +x timeupdate.bash  # or blk_timeupdate.bash
   ```

4. Add a cron job:
   ```bash
   crontab -e
   ```
   Add the line:
   ```
   */15 * * * * /path/to/timeupdate.bash
   ```
   (or use `blk_timeupdate.bash` for the black version)

## Troubleshooting

If the background is not updating:
1. Make sure feh is installed
2. Check if the script is executable
3. Verify your display is set correctly (DISPLAY=:0)
4. Check cron logs: `grep CRON /var/log/syslog`
