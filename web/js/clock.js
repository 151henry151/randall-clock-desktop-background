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

  function drawRedDot(ctx, x, y, brightness) {
    var pulse = brightness != null ? brightness : 1;
    var minPulse = 0.35;
    var scale = minPulse + (1 - minPulse) * pulse;
    for (var i = 0; i < DOT_LAYERS.length; i++) {
      var layer = DOT_LAYERS[i];
      ctx.beginPath();
      ctx.arc(x, y, layer.radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 0, 0, ' + ((layer.alpha * scale) / 255) + ')';
      ctx.fill();
    }
  }

  /** Brightness pulse 0–1, cycling once per UTC second. */
  function dotPulsePhase(date) {
    var t = date.getUTCSeconds() + date.getUTCMilliseconds() / 1000;
    return (Math.sin(2 * Math.PI * t) + 1) / 2;
  }

  /**
   * Build inverted globe alpha mask matching black_mode.py overlay_mask.
   * Overlay is drawn only where the base globe image is transparent.
   */
  function createOverlayMaskCanvas(globeImage) {
    var width = globeImage.naturalWidth || globeImage.width;
    var height = globeImage.naturalHeight || globeImage.height;
    var maskCanvas = document.createElement('canvas');
    maskCanvas.width = width;
    maskCanvas.height = height;
    var maskCtx = maskCanvas.getContext('2d');

    maskCtx.drawImage(globeImage, 0, 0);
    var imageData = maskCtx.getImageData(0, 0, width, height);
    var data = imageData.data;
    for (var i = 0; i < data.length; i += 4) {
      var globeAlpha = data[i + 3];
      var showOverlay = globeAlpha > 0 ? 0 : 255;
      data[i] = 255;
      data[i + 1] = 255;
      data[i + 2] = 255;
      data[i + 3] = showOverlay;
    }
    maskCtx.putImageData(imageData, 0, 0);
    return maskCanvas;
  }

  function drawOverlayWithMask(ctx, overlayImage, maskCanvas) {
    var width = ctx.canvas.width;
    var height = ctx.canvas.height;
    var tempCanvas = document.createElement('canvas');
    tempCanvas.width = width;
    tempCanvas.height = height;
    var tempCtx = tempCanvas.getContext('2d');

    tempCtx.drawImage(overlayImage, 0, 0);
    tempCtx.globalCompositeOperation = 'destination-in';
    tempCtx.drawImage(maskCanvas, 0, 0);
    ctx.drawImage(tempCanvas, 0, 0);
  }

  function ClockRenderer(options) {
    this.canvas = options.canvas;
    this.ctx = this.canvas.getContext('2d');
    this.statusEl = options.statusEl || null;
    this.globeImage = null;
    this.overlayImage = null;
    this.overlayMaskCanvas = null;
    this.globeGeometry = null;
    this.location = null;
    this.animationId = null;
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
      self.overlayMaskCanvas = createOverlayMaskCanvas(self.globeImage);
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
    if (!this.globeImage || !this.overlayImage || !this.overlayMaskCanvas) {
      return;
    }

    var ctx = this.ctx;
    var globe = this.globeGeometry;
    var globeW = globe.width;
    var globeH = globe.height;
    var rotationDeg = calculateRotationDegrees(date);
    // PIL rotate() uses negative angles for clockwise; canvas uses positive for clockwise.
    var rotationRad = -rotationDeg * Math.PI / 180;
    var pasteX = Math.round((this.canvas.width - globeW) / 2);
    var pasteY = Math.round((this.canvas.height - globeH) / 2) + this.verticalOffset;

    if (globeW === this.canvas.width && globeH === this.canvas.height) {
      pasteX = 0;
      pasteY = this.verticalOffset;
    }

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
      drawRedDot(globeCtx, clamped.x, clamped.y, dotPulsePhase(date));
    }

    ctx.save();
    ctx.translate(pasteX + globeW / 2, pasteY + globeH / 2);
    ctx.rotate(rotationRad);
    ctx.drawImage(globeCanvas, -globeW / 2, -globeH / 2);
    ctx.restore();

    drawOverlayWithMask(ctx, this.overlayImage, this.overlayMaskCanvas);
  };

  ClockRenderer.prototype.start = function () {
    var self = this;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    function tick(now) {
      self.renderFrame(new Date());
      self.animationId = requestAnimationFrame(tick);
    }

    this.renderFrame(new Date());
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
    calculateRotationDegrees: calculateRotationDegrees,
    createOverlayMaskCanvas: createOverlayMaskCanvas
  };
})(typeof window !== 'undefined' ? window : this);
