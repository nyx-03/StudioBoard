// StudioBoard API client
// Centralizes: credentials, CSRF, JSON parsing, and error handling.

// ⚠️ Règle fondamentale :
// Toutes les requêtes doivent passer par /api/... (proxy Next.js)
// Aucune URL absolue vers Django n’est autorisée ici.

const DEFAULT_HEADERS = {
  Accept: 'application/json',
};

function getCookie(name) {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function buildQuery(params) {
  if (!params) return '';
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      for (const item of v) usp.append(k, String(item));
    } else {
      usp.append(k, String(v));
    }
  }
  const s = usp.toString();
  return s ? `?${s}` : '';
}

async function parseJsonSafe(res) {
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    // Some endpoints may respond with empty body (204) or plain text.
    const text = await res.text().catch(() => '');
    return text ? { detail: text } : null;
  }
  return await res.json().catch(() => null);
}

function makeError(res, data) {
  const status = res.status;
  const statusText = res.statusText || 'Error';

  // Try to extract an informative message.
  let message = `HTTP ${status} ${statusText}`;
  if (data) {
    if (typeof data === 'string') message = data;
    else if (data.detail) message = data.detail;
    else if (data.error) message = data.error;
    else if (data.message) message = data.message;
    else if (data.errors && typeof data.errors === 'object') {
      const firstKey = Object.keys(data.errors)[0];
      if (firstKey) {
        const val = data.errors[firstKey];
        message = Array.isArray(val) ? val[0] : String(val);
      }
    }
  }

  const err = new Error(message);
  err.status = status;
  err.data = data;
  return err;
}

async function ensureCsrfCookie(csrfUrl = '/api/auth/csrf/') {
  // If cookie is already present, don't spam the server.
  if (getCookie('csrftoken')) return;
  if (!csrfUrl.startsWith('/')) {
    throw new Error('csrfUrl doit commencer par /');
  }
  await fetch(csrfUrl, {
    credentials: 'include',
    cache: 'no-store',
  });
}

async function request(method, url, {
  data,
  params,
  headers,
  csrfUrl,
  fetchOptions,
} = {}) {
  if (url.startsWith('http')) {
    throw new Error('api.js ne doit jamais utiliser d’URL absolue. Utilise /api/...');
  }

  const isSafeMethod = method === 'GET' || method === 'HEAD' || method === 'OPTIONS';

  const finalUrl = `${url}${buildQuery(params)}`;

  const finalHeaders = {
    ...DEFAULT_HEADERS,
    ...(headers || {}),
  };

  // JSON body by default when data is provided.
  let body;
  if (data !== undefined) {
    if (data instanceof FormData) {
      body = data;
      // Let the browser set the correct multipart boundary.
    } else {
      finalHeaders['Content-Type'] = finalHeaders['Content-Type'] || 'application/json';
      body = finalHeaders['Content-Type'].includes('application/json')
        ? JSON.stringify(data)
        : data;
    }
  }

  if (!isSafeMethod) {
    await ensureCsrfCookie(csrfUrl);
    const token = getCookie('csrftoken');
    if (!token) {
      throw new Error('CSRF cookie not set');
    }
    finalHeaders['X-CSRFToken'] = finalHeaders['X-CSRFToken'] || token;
  }

  const res = await fetch(finalUrl, {
    method,
    credentials: 'include',
    headers: {
      ...finalHeaders,
      // Force no cache at browser / Next.js level
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
    },
    body,
    // Disable Next.js App Router fetch caching
    cache: 'no-store',
    next: { revalidate: 0 },
    ...(fetchOptions || {}),
  });

  const parsed = await parseJsonSafe(res);

  if (!res.ok) {
    throw makeError(res, parsed);
  }

  return parsed;
}

export function apiGet(url, options) {
  return request('GET', url, options);
}

export function apiPost(url, data, options) {
  return request('POST', url, { ...(options || {}), data });
}

export function apiPut(url, data, options) {
  return request('PUT', url, { ...(options || {}), data });
}

export function apiPatch(url, data, options) {
  return request('PATCH', url, { ...(options || {}), data });
}

export function apiDelete(url, options) {
  return request('DELETE', url, options);
}

// Expose helpers for advanced usage/testing.
export const __internal = {
  getCookie,
  ensureCsrfCookie,
  buildQuery,
};