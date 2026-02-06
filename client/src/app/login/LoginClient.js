'use client';

import { useSearchParams, useRouter } from 'next/navigation';
// + tes imports useAuth, api, styles, etc.

export default function LoginClient() {
  const router = useRouter();
  const params = useSearchParams();

  // ton code actuel basé sur params
  // ex: const next = params.get('next') || '/boards';

  return (
    // ton JSX actuel
    <div>...</div>
  );
}