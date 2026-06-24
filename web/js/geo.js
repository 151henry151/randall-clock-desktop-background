/**
 * Resolve viewer location from URL override, IP geolocation, or browser GPS.
 */
(function (global) {
  'use strict';

  var IP_ENDPOINTS = [
    {
      url: 'https://ipwho.is/',
      parse: function (data) {
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
    },
    {
      url: 'https://ipapi.co/json/',
      parse: function (data) {
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

  function lookupByIp() {
    var attempt = function (index) {
      if (index >= IP_ENDPOINTS.length) {
        return Promise.reject(new Error('All IP geolocation providers failed'));
      }
      var endpoint = IP_ENDPOINTS[index];
      return fetchJson(endpoint.url, 8000).then(function (data) {
        var parsed = endpoint.parse(data);
        return {
          lat: parsed.lat,
          lon: parsed.lon,
          source: 'ip',
          label: [parsed.city, parsed.region, parsed.country].filter(Boolean).join(', ')
        };
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
          resolve({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            source: 'browser',
            label: 'Browser location'
          });
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
   * @returns {Promise<{ lat: number, lon: number, source: string, label?: string }>}
   */
  function resolveLocation() {
    var override = parseUrlOverride();
    if (override) {
      return Promise.resolve(override);
    }

    return lookupByIp().catch(function () {
      return lookupByBrowser();
    });
  }

  global.RandallGeo = {
    resolveLocation: resolveLocation,
    parseUrlOverride: parseUrlOverride
  };
})(typeof window !== 'undefined' ? window : this);
