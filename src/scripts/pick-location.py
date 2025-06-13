import os
import configparser
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Mode options and corresponding image paths
MODES = {
    'black': os.path.join('src', 'images', 'intervals15m', 'blackGlobeGreenOverlay', '00h00m.png'),
    'xkcd': os.path.join('src', 'images', 'intervals15m', 'xkcdOriginal', '00h00m.png'),
}
CONFIG_PATH = 'config.ini'

# Prompt user for mode
print("Select clock style for location pick:")
print("  1. black (black globe with green overlay)")
print("  2. xkcd (original XKCD now clock)")
mode = ''
while mode not in MODES:
    choice = input("Enter 1 for black, 2 for xkcd: ").strip()
    if choice == '1':
        mode = 'black'
    elif choice == '2':
        mode = 'xkcd'
    else:
        print("Invalid choice. Please enter 1 or 2.")

IMG_PATH = MODES[mode]

# Load image
img = mpimg.imread(IMG_PATH)

print(f"Click on your approximate location in the {mode} image window.")

fig, ax = plt.subplots()
ax.imshow(img)
coords = []

# Click event handler
def onclick(event):
    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        print(f"You clicked at: x={x}, y={y}")
        coords.append((x, y))
        plt.close()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()

if coords:
    x, y = coords[0]
    # Write to config.ini
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    if 'LOCATION' not in config:
        config['LOCATION'] = {}
    config['LOCATION']['x'] = str(x)
    config['LOCATION']['y'] = str(y)
    config['LOCATION']['mode'] = mode
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
    print(f"Coordinates saved to {CONFIG_PATH} under [LOCATION]: x={x}, y={y}, mode={mode}")
else:
    print("No location selected.") 