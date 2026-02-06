'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from './useAuth';

/**
 * useRequireAuth
 * - Hard-gate for protected pages
 * - Redirects to /login if the user is not authenticated
 * - Preserves the current path via ?next=
 */
export function useRequireAuth() {
  const router = useRouter();
  const pathname = usePathname();
  const { authenticated, loading } = useAuth();

  useEffect(() => {
    if (loading) return;

    // Avoid redirect loop if we are already on login
    if (!authenticated && pathname !== '/login') {
      const next = encodeURIComponent(pathname || '/');
      router.replace(`/login?next=${next}`);
    }
  }, [authenticated, loading, pathname, router]);

  return { authenticated, loading };
}