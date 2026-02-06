// src/features/kanban/components/KanbanCard.jsx

import Link from 'next/link';

export function KanbanCard({ styles, boardId, idea, highlightedIdeaId, children }) {
  return (
    <Link
      className={`${styles.card} ${idea.id === highlightedIdeaId ? styles.cardNew : ''}`}
      href={`/boards/${boardId}/ideas/${idea.id}`}
    >
      <div className={styles.cardTitle}>{idea.title}</div>

      <div className={styles.cardMeta}>
        {idea.next_action ? (
          <span className={styles.pill}>Next: {idea.next_action}</span>
        ) : (
          <span className={styles.pillMuted}>Pas de next action</span>
        )}

        {typeof idea.impact === 'number' || typeof idea.impact === 'string' ? (
          <span className={styles.pill}>Impact: {idea.impact}</span>
        ) : null}
      </div>

      {children}
    </Link>
  );
}