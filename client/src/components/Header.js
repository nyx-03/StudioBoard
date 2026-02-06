'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import styles from './header.module.css';
import { useAuth } from '../hooks/useAuth';

export default function Header() {
  const router = useRouter();
  const { authenticated, user, logout, loading } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.left}>
          <Link href="/" className={styles.brand}>
            StudioBoard
          </Link>

          <nav className={styles.nav}>
            <Link href="/" className={styles.link}>Home</Link>
            <Link href="/boards" className={styles.link}>Boards</Link>
          </nav>
        </div>

        <div className={styles.right}>
          {!loading && !authenticated && (
            <Link href="/login" className={styles.button}>
              Connexion
            </Link>
          )}

          {!loading && authenticated && user && (
            <div className={styles.userBox}>
              <span className={styles.username}>👋 {user.username}</span>
              <button onClick={handleLogout} className={styles.button}>
                Déconnexion
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}