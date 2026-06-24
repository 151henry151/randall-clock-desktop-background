/**
 * Resolve viewer location from URL override, browser GPS, or IP geolocation.
 *
 * IP lookups prefer a same-origin proxy (api/geo) so they work under strict CSP.
 * External providers are tried when the proxy is unavailable (e.g. local dev).
 */
(function (global) {
  'use strict';

  function parseIpWho(data) {
    if (!data.success) {
      throw new Error(data.message || 'IP lookup failed');
    }
    return {
      lat: data.latitude,
      lon: data.longitude,
      city: data.city,
      region: data.region,
      country: data.country
    };
  }

  function parseIpApiCo(data) {
    if (data.error) {
      throw new Error(data.reason || data.error);
    }
    return {
      lat: parseFloat(data.latitude),
      lon: parseFloat(data.longitude),
      city: data.city,
      region: data.region,
      country: data.country_name
    };
  }

  function parseGeoJs(data) {
    return {
      lat: parseFloat(data.latitude),
      lon: parseFloat(data.longitude),
      city: data.city,
      region: data.region,
      country: data.country
    };
  }

  var IP_ENDPOINTS = [
    {
      url: 'api/geo',
      parse: parseIpWho,
      sameOrigin: true
    },
    {
      url: 'https://ipwho.is/',
      parse: parseIpWho
    },
    {
      url: 'https://get.geojs.io/v1/ip/geo.json',
      parse: parseGeoJs
    },
    {
      url: 'https://ipapi.co/json/',
      parse: parseIpApiCo
    }
  ];

  function parseUrlOverride() {
    var params = new URLSearchParams(global.location.search);
    var lat = params.get('lat');
    var lon = params.get('lon');
    if (lat == null || lon == null) {
      return null;
    }
    lat = parseFloat(lat);
    lon = parseFloat(lon);
    if (!isFinite(lat) || !isFinite(lon)) {
      return null;
    }
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      return null;
    }
    return {
      lat: lat,
      lon: lon,
      source: 'url',
      label: lat.toFixed(2) + ', ' + lon.toFixed(2)
    };
  }

  function fetchJson(url, timeoutMs) {
    var controller = new AbortController();
    var timer = setTimeout(function () {
      controller.abort();
    }, timeoutMs);

    return fetch(url, {
      signal: controller.signal,
      headers: { Accept: 'application/json' }
    }).then(function (response) {
      clearTimeout(timer);
      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }
      return response.json();
    }).catch(function (err) {
      clearTimeout(timer);
      throw err;
    });
  }

  function normalizeLocation(parsed, source) {
    var lat = parseFloat(parsed.lat);
    var lon = parseFloat(parsed.lon);
    if (!isFinite(lat) || !isFinite(lon)) {
      throw new Error('Invalid coordinates from ' + source);
    }
    var label = [parsed.city, parsed.region, parsed.country].filter(Boolean).join(', ');
    if (!label) {
      label = source === 'ip' ? 'Approximate location (IP)' : 'Browser location';
    } else if (source === 'ip') {
      label = label + ' (approx.)';
    }
    return {
      lat: lat,
      lon: lon,
      source: source,
      label: label
    };
  }

  function lookupByIp() {
    var attempt = function (index) {
      if (index >= IP_ENDPOINTS.length) {
        return Promise.reject(new Error('All IP geolocation providers failed'));
      }
      var endpoint = IP_ENDPOINTS[index];
      return fetchJson(endpoint.url, 8000).then(function (data) {
        return normalizeLocation(endpoint.parse(data), 'ip');
      }).catch(function () {
        return attempt(index + 1);
      });
    };
    return attempt(0);
  }

  function lookupByBrowser() {
    return new Promise(function (resolve, reject) {
      if (!navigator.geolocation) {
        reject(new Error('Browser geolocation unavailable'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        function (position) {
          resolve(normalizeLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            city: '',
            region: '',
            country: ''
          }, 'browser'));
        },
        function (err) {
          reject(err);
        },
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000
        }
      );
    });
  }

  /**
   * Resolve the best available viewer location.
   *
   * Starts IP lookup immediately (works under CSP via same-origin proxy).
   * Prompts for browser geolocation in parallel; uses it when granted.
   *
   * @returns {Promise<{ lat: number, lon: number, source: string, label?: string }>}
   */
  function resolveLocation() {
    var override = parseUrlOverride();
    if (override) {
      return Promise.resolve(override);
    }

    var ipPromise = lookupByIp();
    var browserPromise = lookupByBrowser().catch(function () {
      return null;
    });

    return browserPromise.then(function (browserLocation) {
      if (browserLocation) {
        return browserLocation;
      }
      return ipPromise;
    });
  }

  global.RandallGeo = {
    resolveLocation: resolveLocation,
    parseUrlOverride: parseUrlOverride,
    lookupByIp: lookupByIp
  };
})(typeof window !== 'undefined' ? window : this);
