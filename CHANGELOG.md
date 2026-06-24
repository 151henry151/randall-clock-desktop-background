# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
