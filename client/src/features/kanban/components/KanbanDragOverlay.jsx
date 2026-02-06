// src/features/kanban/components/KanbanDragOverlay.jsx

export function KanbanDragOverlay({ styles, activeDragIdea }) {
  if (!activeDragIdea) return null;

  return (
    <div className={styles.dragOverlay}>
      <div className={styles.card}>
        <div className={styles.cardTitle}>{activeDragIdea.title}</div>
      </div>
    </div>
  );
}