// src/features/kanban/components/KanbanBoardMobile.jsx

import { KanbanColumn } from './KanbanColumn';

export function KanbanBoardMobile({
  styles,
  columns,
  activeIndex,
  setActiveIndex,
  boardId,
  highlightedIdeaId,
  renderCard,
}) {
  const activeColumn = columns[activeIndex] || null;

  return (
    <section className={styles.kanbanMobile}>
      <div className={styles.mobileNav}>
        <button
          className={styles.navBtn}
          disabled={activeIndex === 0}
          onClick={() => setActiveIndex((i) => Math.max(0, i - 1))}
        >
          ←
        </button>

        <div className={styles.mobileTitle}>
          {activeColumn?.name}
          <span className={styles.mobileCount}>{(activeColumn?.ideas || []).length}</span>
        </div>

        <button
          className={styles.navBtn}
          disabled={activeIndex === columns.length - 1}
          onClick={() => setActiveIndex((i) => Math.min(columns.length - 1, i + 1))}
        >
          →
        </button>
      </div>

      {activeColumn && (
        <KanbanColumn
          styles={styles}
          column={activeColumn}
          boardId={boardId}
          highlightedIdeaId={highlightedIdeaId}
          renderCard={renderCard}
          showHeader={false}
          isMobile
        />
      )}
    </section>
  );
}