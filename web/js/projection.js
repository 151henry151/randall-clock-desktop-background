/**
 * South-pole azimuthal equidistant projection for the Randall Clock globe artwork.
 *
 * The Fred Weinhaus / XKCD black-globe map uses standard azimuthal equidistant
 * projection centered on the South Pole. A single longitude offset (lon0) accounts
 * for the artwork's orientation in the 00h00m reference frame.
 */
(function (global) {
  'use strict';

  var DEG = Math.PI / 180;

  /** Prime meridian orientation in the static base_globe artwork (degrees). */
  var GLOBE_LON0 = 8;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  /**
   * Convert geographic coordinates to pixel coordinates on the globe image.
   *
   * @param {number} lat - Latitude in degrees (-90 to 90).
   * @param {number} lon - Longitude in degrees (-180 to 180).
   * @param {object} globe - Globe geometry { centerX, centerY, radius, lon0? }.
   * @returns {{ x: number, y: number, rho: number, theta: number }}
   */
  function latLonToGlobePixel(lat, lon, globe) {
    var centerX = globe.centerX;
    var centerY = globe.centerY;
    var radius = globe.radius;
    var lon0 = globe.lon0 != null ? globe.lon0 : GLOBE_LON0;

    var phi = lat * DEG;
    var lam = lon * DEG;
    var phi0 = -Math.PI / 2;
    var lam0 = lon0 * DEG;

    var cosC = Math.sin(phi0) * Math.sin(phi) +
      Math.cos(phi0) * Math.cos(phi) * Math.cos(lam - lam0);
    cosC = clamp(cosC, -1, 1);
    var c = Math.acos(cosC);
    var rho = radius * c / Math.PI;

    if (c < 1e-12) {
      return { x: centerX, y: centerY, rho: 0, theta: 0 };
    }

    var x = Math.cos(phi) * Math.sin(lam - lam0);
    var y = Math.cos(phi0) * Math.sin(phi) -
      Math.sin(phi0) * Math.cos(phi) * Math.cos(lam - lam0);
    var theta = Math.atan2(y, x);

    return {
      x: centerX + rho * Math.cos(theta),
      y: centerY + rho * Math.sin(theta),
      rho: rho,
      theta: theta
    };
  }

  /**
   * Measure the visible globe disk radius from image alpha along radial rays.
   * Full-frame artwork (1980x1977) has a ~491px disk, not half the canvas width.
   */
  function detectGlobeDiskRadius(image) {
    var width = image.naturalWidth || image.width;
    var height = image.naturalHeight || image.height;
    var centerX = width / 2;
    var centerY = height / 2;
    var maxScan = Math.min(centerX, centerY);
    var canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(image, 0, 0);
    var data = ctx.getImageData(0, 0, width, height).data;
    var samples = [];

    for (var angle = 0; angle < 360; angle += 5) {
      var rad = angle * DEG;
      var lastOpaque = 0;
      for (var r = 1; r < maxScan; r++) {
        var x = Math.round(centerX + r * Math.cos(rad));
        var y = Math.round(centerY + r * Math.sin(rad));
        if (x < 0 || x >= width || y < 0 || y >= height) {
          break;
        }
        var alpha = data[(y * width + x) * 4 + 3];
        if (alpha > 0) {
          lastOpaque = r;
        } else if (lastOpaque > 100) {
          break;
        }
      }
      if (lastOpaque > 0) {
        samples.push(lastOpaque);
      }
    }

    if (!samples.length) {
      return Math.min(width, height) / 2;
    }

    samples.sort(function (a, b) { return a - b; });
    return samples[Math.floor(samples.length / 2)];
  }

  /**
   * Build globe geometry from a loaded image element.
   *
   * @param {HTMLImageElement} image
   * @param {number} [lon0]
   * @returns {{ centerX: number, centerY: number, radius: number, lon0: number, width: number, height: number }}
   */
  function globeGeometryFromImage(image, lon0) {
    var width = image.naturalWidth || image.width;
    var height = image.naturalHeight || image.height;

    return {
      centerX: width / 2,
      centerY: height / 2,
      radius: detectGlobeDiskRadius(image),
      lon0: lon0 != null ? lon0 : GLOBE_LON0,
      width: width,
      height: height
    };
  }

  /**
   * Clamp a dot position to the globe disk if floating-point error pushes it outside.
   */
  function clampToGlobe(x, y, globe) {
    var dx = x - globe.centerX;
    var dy = y - globe.centerY;
    var dist = Math.hypot(dx, dy);
    if (dist <= globe.radius || dist === 0) {
      return { x: x, y: y };
    }
    var scale = globe.radius / dist;
    return {
      x: globe.centerX + dx * scale,
      y: globe.centerY + dy * scale
    };
  }

  global.RandallProjection = {
    GLOBE_LON0: GLOBE_LON0,
    latLonToGlobePixel: latLonToGlobePixel,
    globeGeometryFromImage: globeGeometryFromImage,
    detectGlobeDiskRadius: detectGlobeDiskRadius,
    clampToGlobe: clampToGlobe
  };
})(typeof window !== 'undefined' ? window : this);
