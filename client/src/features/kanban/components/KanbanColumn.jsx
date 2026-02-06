// src/features/kanban/components/KanbanColumn.jsx

import { useDroppable } from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { dndIdeaId, dndColId } from '../dnd/dndIds';

function SortableCardWrapper({ id, containerId, children }) {
  const sid = String(id);
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: sid,
    data: { type: 'idea', containerId: String(containerId) },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    touchAction: 'none',
    cursor: isDragging ? 'grabbing' : 'grab',
    opacity: isDragging ? 0.75 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={isDragging ? 'dragging' : undefined}
      {...attributes}
      {...listeners}
    >
      {children}
    </div>
  );
}

function DroppableColumn({ id, children }) {
  const cid = String(id);
  const { setNodeRef, isOver } = useDroppable({ id: cid });
  return (
    <div ref={setNodeRef} className={isOver ? 'dropOver' : undefined}>
      {children}
    </div>
  );
}

export function KanbanColumn({
  styles,
  column,
  boardId,
  highlightedIdeaId,
  renderCard,
  showHeader = true,
  isMobile = false,
  columnRef,
}) {
  const colDndId = dndColId(column.id);
  const ideas = Array.isArray(column.ideas) ? column.ideas : [];

  return (
    <DroppableColumn id={colDndId}>
      <div
        className={styles.column}
        data-id={column.id}
        id={String(column.id)}
        ref={columnRef || undefined}
      >
        {showHeader && (
          <div className={styles.columnHeader}>
            <div className={styles.columnName}>{column.name}</div>
            <div className={styles.columnCount}>{ideas.length}</div>
          </div>
        )}

        <div className={styles.cards}>
          <SortableContext
            id={colDndId}
            items={ideas.map((i) => dndIdeaId(i.id))}
            strategy={verticalListSortingStrategy}
          >
            {ideas.map((idea) => (
              <SortableCardWrapper key={idea.id} id={dndIdeaId(idea.id)} containerId={colDndId}>
                {renderCard({ boardId, idea, highlightedIdeaId, styles, isMobile })}
              </SortableCardWrapper>
            ))}
          </SortableContext>

          {ideas.length === 0 && <div className={styles.emptyCol}>Aucune carte</div>}
        </div>
      </div>
    </DroppableColumn>
  );
}