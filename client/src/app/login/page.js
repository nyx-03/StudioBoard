'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import styles from './page.module.css';
import { useAuth } from '../../hooks/useAuth';

function LoginInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams?.get('next') || '/';
  const { login, authenticated, loading } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && authenticated) {
      router.replace(nextUrl);
    }
  }, [authenticated, loading, router, nextUrl]);

  const ensureCsrfCookie = async () => {
    // Django sets the CSRF cookie on this endpoint.
    // We MUST include credentials so the cookie is stored/sent on LAN/mobile.
    await fetch('/api/auth/csrf', { credentials: 'include' });
  };

  // Warm up CSRF cookie on page load.
  useEffect(() => {
    ensureCsrfCookie().catch(() => {
      // Ignore; login will retry.
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await ensureCsrfCookie();
      await login({ username, password });
      router.replace(nextUrl);
    } catch (err) {
      const msg = (err?.message || '').toLowerCase();
      if (msg.includes('csrf')) {
        setError("Échec CSRF. Recharge la page puis réessaie (réseau local / IP).");
        setSubmitting(false);
        return;
      }
      setError(err?.message || 'Échec de la connexion');
      setSubmitting(false);
    }
  };

  if (loading || authenticated) {
    return null;
  }

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>Connexion</h1>
        <p className={styles.subtitle}>Accède à ton espace StudioBoard</p>

        <form onSubmit={onSubmit} className={styles.form}>
          <label className={styles.label}>
            Nom d’utilisateur
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={styles.input}
              required
              autoFocus
            />
          </label>

          <label className={styles.label}>
            Mot de passe
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              required
            />
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <button type="submit" className={styles.button} disabled={submitting}>
            {submitting ? 'Connexion…' : 'Se connecter'}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}