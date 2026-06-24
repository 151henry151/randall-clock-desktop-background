# Randall Clock — Web Deployment

**Live demo:** [hromp.com/clock/](https://hromp.com/clock/)

Serve the XKCD "Now" clock (Black Mode) as a static web page with automatic red-dot placement from the viewer's geolocation.

## Requirements

- A web server (nginx or Apache) serving static files
- HTTPS in production (browser geolocation requires a secure context)
- Image assets (`base_globe.png`, `stationary_overlay.png`) are committed in `web/assets/` for static deployment

## Quick start

1. **Serve the `web/` directory** with any static file server:

   ```bash
   cd web && python3 -m http.server 8080
   ```

   Open `http://localhost:8080/` in a browser.

2. **Configure nginx or Apache** using the example configs in `web/deploy/`.

## Geolocation

The clock resolves the viewer's location in this order:

1. **URL override** — `?lat=44.5&lon=-72.5` (useful for testing)
2. **Browser geolocation** — prompts for permission; used when granted
3. **IP geolocation** — starts immediately in parallel; used when browser access is denied

The globe and correct time display do **not** depend on geolocation — only the red dot does.

### Content-Security-Policy and IP lookup

Sites with a strict `Content-Security-Policy` (such as `connect-src 'self'`) block browser requests to third-party geo APIs. Configure a **same-origin proxy** so `api/geo` forwards to a provider:

- Root deploy: see `deploy/nginx.conf.example` (`location /api/geo`)
- Subpath deploy (e.g. `/clock/`): see `deploy/nginx-subpath.conf.example` (`location /clock/api/geo`)

Alternatively, add `https://ipwho.is` and `https://get.geojs.io` to your CSP `connect-src` directive.

The globe renders immediately after assets load. The red dot appears once a location is resolved.

## Red dot placement

Geographic coordinates are converted to pixel coordinates with a south-pole azimuthal equidistant projection. The artwork orientation constant is `lon0 = 15°` (see `projection.js`), tuned against painted continent outlines.

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
│   ├── nginx-subpath.conf.example
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
