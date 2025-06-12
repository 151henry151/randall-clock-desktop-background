import matplotlib
matplotlib.use('TkAgg')
import os
import configparser
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math

# Mode options and corresponding image paths
MODES = {
    'black': os.path.join('src', 'images', 'intervals15m', 'blackGlobeGreenOverlay', '00h00m.png'),
    'xkcd': os.path.join('src', 'images', 'intervals15m', 'xkcdOriginal', '00h00m.png'),
}
CONFIG_PATH = 'config.ini'

while True:
    print("\nWhich globe would you like to measure?")
    print("  1. black (black globe with green overlay)")
    print("  2. xkcd (original XKCD now clock)")
    print("  q. quit")
    mode = ''
    while mode not in MODES and mode != 'q':
        choice = input("Enter 1 for black, 2 for xkcd, or q to quit: ").strip()
        if choice == '1':
            mode = 'black'
        elif choice == '2':
            mode = 'xkcd'
        elif choice.lower() == 'q':
            mode = 'q'
        else:
            print("Invalid choice. Please enter 1, 2, or q.")
    if mode == 'q':
        print("Exiting.")
        break

    IMG_PATH = MODES[mode]
    img = mpimg.imread(IMG_PATH)
    height, width = img.shape[0], img.shape[1]
    center_x, center_y = width // 2, height // 2
    print(f"Image dimensions: width={width}, height={height}")
    print(f"Image center: ({center_x}, {center_y})")
    print(f"Click a point on the EDGE of the globe in the {mode} image window.")
    fig, ax = plt.subplots()
    ax.imshow(img)
    coords = []

    # Click event handler
    def onclick(event):
        if event.xdata is not None and event.ydata is not None:
            x, y = int(event.xdata), int(event.ydata)
            coords.append((x, y))
            plt.close()

    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()

    if len(coords) == 1:
        edge_x, edge_y = coords[0]
        radius = int(math.hypot(edge_x - center_x, edge_y - center_y))
        print(f"Measured center: ({center_x}, {center_y})")
        print(f"Measured radius: {radius}")
        # Write to config.ini
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        section = 'BLACK_GLOBE' if mode == 'black' else 'XKCD_GLOBE'
        if section not in config:
            config[section] = {}
        config[section]['center_x'] = str(center_x)
        config[section]['center_y'] = str(center_y)
        config[section]['radius'] = str(radius)
        config[section]['width'] = str(width)
        config[section]['height'] = str(height)
        with open(CONFIG_PATH, 'w') as configfile:
            config.write(configfile)
        print(f"Saved to [{section}] in {CONFIG_PATH}")
    else:
        print("You must click exactly one point: the edge of the globe.") 