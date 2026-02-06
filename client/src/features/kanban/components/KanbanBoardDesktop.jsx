// src/features/kanban/components/KanbanBoardDesktop.jsx

import { KanbanColumn } from './KanbanColumn';

export function KanbanBoardDesktop({
  styles,
  columns,
  boardId,
  highlightedIdeaId,
  renderCard,
  columnRefs,
}) {
  return (
    <section className={styles.kanban}>
      {columns.map((col, idx) => (
        <KanbanColumn
          key={col.id}
          styles={styles}
          column={col}
          boardId={boardId}
          highlightedIdeaId={highlightedIdeaId}
          renderCard={renderCard}
          showHeader
          columnRef={(el) => (columnRefs.current[idx] = el)}
        />
      ))}
    </section>
  );
}