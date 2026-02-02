import styles from "./page.module.css";

export default function Home() {
  // Mock temporaire: remplacé par fetch API Django ensuite
  const boards = [
    { id: 1, name: "Studio" },
    { id: 2, name: "Marketing" },
  ];

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brand}>StudioBoard</div>
        <div className={styles.sub}>
          Interface Next.js (CSR) — backend Django
        </div>
      </header>

      <section className={styles.section}>
        <h2 className={styles.h2}>Boards</h2>

        <div className={styles.grid}>
          {boards.map((b) => (
            <a key={b.id} className={styles.card} href={`/b/${b.id}`}>
              <div className={styles.cardTitle}>{b.name}</div>
              <div className={styles.cardMeta}>Ouvrir le kanban →</div>
            </a>
          ))}
        </div>
      </section>
    </main>
  );
}