# randall-clock-desktop-background
Change desktop background using the XKCD now clock from https://xkcd.com/1335/

# Installation:


1. install feh
on debian systems: `apt install feh`

2. add a cron job like 
`*/15 * * * * /path/to/timeupdate.bash`
to edit cron jobs on a debian system, `crontab -e`

3. adjust to your timezone by modifying the "7 hours ago" in timeupdate.bash
