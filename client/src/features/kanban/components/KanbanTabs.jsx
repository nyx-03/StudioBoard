// src/features/kanban/components/KanbanTabs.jsx

export function KanbanTabs({ styles, columns, activeIndex, setActiveIndex, isMobile, columnRefs }) {
  if (!columns?.length) return null;

  return (
    <div className={styles.tabs}>
      {columns.map((col, idx) => (
        <button
          key={col.id}
          className={`${styles.tab} ${idx === activeIndex ? styles.tabActive : ''}`}
          onClick={() => {
            setActiveIndex(idx);
            if (!isMobile) {
              const el = columnRefs?.current?.[idx];
              el?.scrollIntoView({ behavior: 'smooth', inline: 'start' });
            }
          }}
        >
          <span>{col.name}</span>
          <span className={styles.tabCount}>{(col.ideas || []).length}</span>
        </button>
      ))}
    </div>
  );
}