'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import styles from './page.module.css';
import { useRequireAuth } from '../../hooks/useRequireAuth';
import { apiGet } from '../../lib/api';

export default function BoardsPage() {
  const { authenticated, loading: authLoading } = useRequireAuth();

  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!authLoading && authenticated) {
      async function loadBoards() {
        try {
          const data = await apiGet('/api/boards/');
          setBoards(data.boards || []);
        } catch (err) {
          setError(err.message || 'Impossible de charger les boards');
        } finally {
          setLoading(false);
        }
      }

      loadBoards();
    }
  }, [authenticated, authLoading]);

  // While auth is loading or redirecting, render nothing
  if (authLoading || !authenticated) {
    return null;
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Mes boards</h1>
        <p className={styles.subtitle}>
          Accède à l’ensemble de tes espaces de travail.
        </p>
      </header>

      <section className={styles.section}>
        {loading && <div className={styles.state}>Chargement des boards…</div>}

        {error && <div className={styles.error}>Erreur : {error}</div>}

        {!loading && !error && boards.length === 0 && (
          <div className={styles.state}>Aucun board disponible.</div>
        )}

        {!loading && !error && boards.length > 0 && (
          <div className={styles.grid}>
            {boards.map((b) => (
              <Link key={b.id} className={styles.card} href={`/boards/${b.id}`}>
                <div className={styles.cardTitle}>{b.name}</div>
                <div className={styles.cardMeta}>Ouvrir le kanban →</div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
