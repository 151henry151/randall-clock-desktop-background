# Randall Clock — Web Deployment

Serve the XKCD "Now" clock (Black Mode) as a static web page with automatic red-dot placement from the viewer's geolocation.

## Requirements

- A web server (nginx or Apache) serving static files
- HTTPS in production (browser geolocation requires a secure context)
- Image assets from a desktop Black Mode install:
  - `base_globe.png`
  - `stationary_overlay.png`

## Quick start

1. **Copy assets** from an existing desktop install:

   ```bash
   ./web/setup_assets.sh
   ```

   This copies `src/images/base_globe.png` and `src/images/stationary_overlay.png` into `web/assets/`.

2. **Serve the `web/` directory** with any static file server:

   ```bash
   cd web && python3 -m http.server 8080
   ```

   Open `http://localhost:8080/` in a browser.

3. **Configure nginx or Apache** using the example configs in `web/deploy/`.

## Geolocation

The clock resolves the viewer's location in this order:

1. **URL override** — `?lat=44.5&lon=-72.5` (useful for testing)
2. **IP geolocation** — client-side lookup via `ipwho.is` or `ipapi.co`
3. **Browser geolocation** — `navigator.geolocation` if the user grants permission

If all methods fail, the clock still runs but without a red dot. A brief status message appears in the lower-right corner when location is available.

## Red dot placement

The globe artwork uses a **south-pole azimuthal equidistant** projection. Geographic coordinates are converted to pixel coordinates with a single orientation constant (`lon0 = 8°`) matching the static artwork's 00h00m reference frame.

Validate placement with the QA tool:

```bash
# After setup_assets.sh, serve web/ and open:
# http://localhost:8080/tools/validate-projection.html
```

Reference cities should land on the correct continent outlines.

## Directory layout

```
web/
├── index.html              # Main clock page
├── css/style.css
├── js/
│   ├── projection.js       # lat/lon → globe pixels
│   ├── geo.js              # IP + browser geolocation
│   └── clock.js            # Canvas renderer
├── assets/                 # base_globe.png, stationary_overlay.png
├── tools/
│   └── validate-projection.html
├── deploy/
│   ├── nginx.conf.example
│   └── apache.conf.example
├── setup_assets.sh
└── README.md
```

## Deployment notes

- No backend or Python runtime is required on the server.
- The desktop install (`install_blackmode.sh`, `src/black_mode.py`, etc.) is **not modified** by the web deployment.
- IP geolocation accuracy depends on the viewer's network; browser geolocation is often more precise.
- Example server configs are in `deploy/nginx.conf.example` and `deploy/apache.conf.example`.

## Credits

- XKCD "Now" clock: [xkcd.com/1335](https://xkcd.com/1335)
- Black globe artwork: Fred Weinhaus ImageMagick scripts
