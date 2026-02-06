

'use client';

function getCookie(name) {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

export async function ensureCSRF() {
  // Ensure Django sets csrftoken cookie
  const res = await fetch('/api/auth/csrf/', {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error('Failed to get CSRF token');
  }

  // In practice Django sets `csrftoken` cookie; we read it for POST headers.
  const token = getCookie('csrftoken');
  if (!token) {
    // Not fatal in all setups, but for Django's csrf_protect it is required.
    throw new Error('CSRF cookie not set');
  }

  return token;
}

export async function apiMe() {
  const res = await fetch('/api/auth/me/', {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error('Failed to fetch auth state');
  }
  return res.json();
}

export async function apiLogin({ username, password }) {
  const csrf = await ensureCSRF();

  const res = await fetch('/api/auth/login/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrf,
    },
    body: JSON.stringify({ username, password }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || 'Login failed');
  }

  return data;
}

export async function apiLogout() {
  const csrf = await ensureCSRF();

  const res = await fetch('/api/auth/logout/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrf,
    },
  });

  if (!res.ok) {
    throw new Error('Logout failed');
  }

  return res.json().catch(() => ({ authenticated: false }));
}