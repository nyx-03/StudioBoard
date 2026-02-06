'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../hooks/useAuth';
import styles from './page.module.css';

export default function Home() {
  const { authenticated, loading: authLoading } = useAuth();
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadBoards() {
      try {
        const res = await fetch('/api/boards/');
        if (!res.ok) {
          throw new Error('Failed to load boards');
        }
        const data = await res.json();
        setBoards(data.boards || []);
      } catch (err) {
        setError(err.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    loadBoards();
  }, []);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <div className={styles.brand}>StudioBoard</div>
          <div className={styles.sub}>
            Ton studio personnel pour capturer, structurer et faire avancer tes idées.
          </div>
        </div>
      </header>

      <section className={styles.section}>
        <h2 className={styles.h2}>Pourquoi StudioBoard ?</h2>
        <div className={styles.state}>
          StudioBoard est une application simple et rapide pour gérer tes idées et projets sous forme de boards.
          L’objectif : éviter les notes éparpillées, garder une vision claire, et transformer une idée en plan d’action.
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Comment l’utiliser</h2>
        <div className={styles.state}>
          <ol style={{ margin: '10px 0 0 18px', lineHeight: 1.7 }}>
            <li><b>Choisis un board</b> (ex : “Studio”, “Marketing”, “Produit”).</li>
            <li><b>Ajoute une idée</b> avec un titre, un statut et une description en Markdown.</li>
            <li><b>Organise</b> tes cartes par colonnes et priorise avec l’impact et la prochaine action.</li>
            <li><b>Utilise les templates</b> pour standardiser tes briefs (cahier des charges, specs, checklists…).</li>
          </ol>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Bonnes pratiques</h2>
        <div className={styles.state}>
          <ul style={{ margin: '10px 0 0 18px', lineHeight: 1.7 }}>
            <li><b>Une carte = une intention</b> : évite de mélanger plusieurs sujets.</li>
            <li><b>Écris la “next action”</b> : la prochaine étape concrète et faisable.</li>
            <li><b>Markdown</b> : structure avec titres, listes, checklists, liens et code.</li>
            <li><b>Templates</b> : gagne du temps sur tout ce qui se répète.</li>
          </ul>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.h2}>Boards</h2>

        {authLoading && (
          <div className={styles.state}>Vérification de la connexion…</div>
        )}

        {!authLoading && !authenticated && (
          <div className={styles.state}>
            Connecte‑toi pour voir tes boards.
          </div>
        )}

        {!authLoading && authenticated && (
          <>
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
          </>
        )}
      </section>
    </main>
  );
}