import os
import configparser
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Paths
IMG_PATH = os.path.join('src', 'images', 'base_globe.png')
CONFIG_PATH = 'config.ini'

# Load image
img = mpimg.imread(IMG_PATH)

print("Click on your approximate location in the image window.")
print("This will be used to place the red dot on the globe.")

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
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
    print(f"Coordinates saved to {CONFIG_PATH} under [LOCATION]: x={x}, y={y}")
else:
    print("No location selected.") 