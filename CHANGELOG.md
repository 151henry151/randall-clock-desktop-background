# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.7] - 2026-06-24

### Changed

- Update root README with live web clock link, web deployment directions, and current version

## [1.1.6] - 2026-06-24

### Changed

- Detect actual globe disk radius from image alpha instead of using half the canvas width, fixing red-dot placement on full-frame artwork

## [1.1.5] - 2026-06-24

### Changed

- Fix web globe rotation direction to match PIL/desktop black_mode.py (canvas vs PIL sign convention)
- Start IP geolocation in parallel with browser prompt; prefer browser when granted, IP when denied
- Request IP geolocation via same-origin `api/geo` first for CSP-compatible deploys
- Add nginx subpath proxy example for `/clock/api/geo` deployments
- Clarify that clock time is correct without geolocation; only the red dot requires location

## [1.1.4] - 2026-06-24

### Changed

- Fix web overlay mask to use alpha instead of RGB with `destination-in` compositing so the rotating globe remains visible

## [1.1.3] - 2026-06-24

### Changed

- Draw the web overlay with an inverted globe alpha mask so the rotating globe remains visible under the stationary overlay
- Start the web clock immediately after assets load instead of waiting for geolocation
- Prompt for browser geolocation first and fall back to IP geolocation when permission is denied

## [1.1.2] - 2026-06-24

### Changed

- Use `SCRIPT_DIR` in `update_background.sh` instead of hardcoded install paths
- Auto-detect X display and Xauthority in `update_background.sh` for GDM + i3 sessions
- Set `DISPLAY` and `XAUTHORITY` in the Black Mode systemd unit environment

## [1.1.1] - 2026-06-24

### Changed

- Track `base_globe.png` and `stationary_overlay.png` in git under `web/assets/` and `src/images/`
- Update `.gitignore` to allow the committed base globe assets while keeping generated frame PNGs ignored

## [1.1.0] - 2026-06-24

### Added

- Add static web deployment under `web/` with browser-based Black Mode clock rendering
- Add `web/js/projection.js` with south-pole azimuthal equidistant lat/lon to pixel conversion
- Add `web/js/geo.js` with IP geolocation, browser geolocation fallback, and URL override
- Add `web/js/clock.js` canvas renderer mirroring desktop rotation and compositing logic
- Add `web/tools/validate-projection.html` for verifying red-dot placement against reference cities
- Add `web/setup_assets.sh` to copy image assets from the desktop install
- Add example nginx and Apache configs in `web/deploy/`
- Add `web/README.md` with deployment and geolocation documentation

## [1.0.0]

### Added

- Initial desktop background Randall Clock (XKCD "Now" clock) with Black Mode support
