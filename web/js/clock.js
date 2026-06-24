/**
 * Browser renderer for the Randall Clock (Black Mode).
 * Mirrors src/black_mode.py rotation and compositing logic.
 */
(function (global) {
  'use strict';

  var ROTATION_OFFSET_DEG = 195;
  var VERTICAL_OFFSET = 10;
  var DOT_LAYERS = [
    { radius: 20, alpha: 40 },
    { radius: 15, alpha: 80 },
    { radius: 10, alpha: 120 },
    { radius: 5, alpha: 255 }
  ];

  function calculateRotationDegrees(date) {
    var utc = date || new Date();
    var totalSeconds = utc.getUTCHours() * 3600 +
      utc.getUTCMinutes() * 60 +
      utc.getUTCSeconds();
    var degrees = (totalSeconds * 360 / 86400) + ROTATION_OFFSET_DEG;
    return -degrees;
  }

  function loadImage(src) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () { resolve(img); };
      img.onerror = function () { reject(new Error('Failed to load ' + src)); };
      img.src = src;
    });
  }

  function drawRedDot(ctx, x, y) {
    for (var i = 0; i < DOT_LAYERS.length; i++) {
      var layer = DOT_LAYERS[i];
      ctx.beginPath();
      ctx.arc(x, y, layer.radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 0, 0, ' + (layer.alpha / 255) + ')';
      ctx.fill();
    }
  }

  function ClockRenderer(options) {
    this.canvas = options.canvas;
    this.ctx = this.canvas.getContext('2d');
    this.statusEl = options.statusEl || null;
    this.globeImage = null;
    this.overlayImage = null;
    this.globeGeometry = null;
    this.location = null;
    this.animationId = null;
    this.lastFrameTime = 0;
    this.verticalOffset = options.verticalOffset != null ? options.verticalOffset : VERTICAL_OFFSET;
  }

  ClockRenderer.prototype.loadAssets = function (globeSrc, overlaySrc) {
    var self = this;
    return Promise.all([
      loadImage(globeSrc),
      loadImage(overlaySrc)
    ]).then(function (images) {
      self.globeImage = images[0];
      self.overlayImage = images[1];
      self.globeGeometry = global.RandallProjection.globeGeometryFromImage(self.globeImage);
      self.canvas.width = self.overlayImage.naturalWidth || self.overlayImage.width;
      self.canvas.height = self.overlayImage.naturalHeight || self.overlayImage.height;
    });
  };

  ClockRenderer.prototype.setLocation = function (location) {
    this.location = location;
    if (this.statusEl && location && location.label) {
      this.statusEl.textContent = location.label;
      this.statusEl.hidden = false;
    }
  };

  ClockRenderer.prototype.clearStatus = function (message) {
    if (this.statusEl) {
      this.statusEl.textContent = message || '';
      this.statusEl.hidden = !message;
    }
  };

  ClockRenderer.prototype.renderFrame = function (date) {
    if (!this.globeImage || !this.overlayImage) {
      return;
    }

    var ctx = this.ctx;
    var globe = this.globeGeometry;
    var globeW = globe.width;
    var globeH = globe.height;
    var rotationDeg = calculateRotationDegrees(date);
    var rotationRad = rotationDeg * Math.PI / 180;
    var pasteX = Math.round((this.canvas.width - globeW) / 2);
    var pasteY = Math.round((this.canvas.height - globeH) / 2) + this.verticalOffset;

    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    var globeCanvas = document.createElement('canvas');
    globeCanvas.width = globeW;
    globeCanvas.height = globeH;
    var globeCtx = globeCanvas.getContext('2d');

    globeCtx.drawImage(this.globeImage, 0, 0);

    if (this.location) {
      var point = global.RandallProjection.latLonToGlobePixel(
        this.location.lat,
        this.location.lon,
        globe
      );
      var clamped = global.RandallProjection.clampToGlobe(point.x, point.y, globe);
      drawRedDot(globeCtx, clamped.x, clamped.y);
    }

    ctx.save();
    ctx.translate(pasteX + globeW / 2, pasteY + globeH / 2);
    ctx.rotate(rotationRad);
    ctx.drawImage(globeCanvas, -globeW / 2, -globeH / 2);
    ctx.restore();

    ctx.drawImage(this.overlayImage, 0, 0);
  };

  ClockRenderer.prototype.start = function () {
    var self = this;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    function tick(now) {
      if (now - self.lastFrameTime >= 1000) {
        self.renderFrame(new Date());
        self.lastFrameTime = now;
      }
      self.animationId = requestAnimationFrame(tick);
    }

    this.renderFrame(new Date());
    this.lastFrameTime = performance.now();
    this.animationId = requestAnimationFrame(tick);
  };

  ClockRenderer.prototype.stop = function () {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  };

  global.RandallClock = {
    ClockRenderer: ClockRenderer,
    calculateRotationDegrees: calculateRotationDegrees
  };
})(typeof window !== 'undefined' ? window : this);
