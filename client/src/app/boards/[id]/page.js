'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import styles from './page.module.css';

import { useRequireAuth } from '@/hooks/useRequireAuth';
import { DndContext, DragOverlay } from '@dnd-kit/core';

import { useKanbanData } from '@/features/kanban/hooks/useKanbanData';
import { useKanbanDnd } from '@/features/kanban/dnd/useKanbanDnd';

import { KanbanTabs } from '@/features/kanban/components/KanbanTabs';
import { KanbanQuickAdd } from '@/features/kanban/components/KanbanQuickAdd';
import { KanbanBoardDesktop } from '@/features/kanban/components/KanbanBoardDesktop';
import { KanbanBoardMobile } from '@/features/kanban/components/KanbanBoardMobile';
import { KanbanCard } from '@/features/kanban/components/KanbanCard';
import { KanbanDragOverlay } from '@/features/kanban/components/KanbanDragOverlay';

export default function BoardKanbanPage() {
  const { authenticated, loading: authLoading } = useRequireAuth();
  const params = useParams();

  const boardId = useMemo(() => {
    const raw = params?.id;
    if (!raw) return null;
    const v = Array.isArray(raw) ? raw[0] : raw;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }, [params]);

  const [activeIndex, setActiveIndex] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const columnRefs = useRef([]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)');
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  const kanban = useKanbanData({ boardId, authenticated, authLoading });

  const dnd = useKanbanDnd({
    boardId,
    columns: kanban.columns,
    setData: kanban.setData,
    dataRef: kanban.dataRef,
    refetchKanban: kanban.refetchKanban,
  });

  // --- Debug helpers (temporary) ---
  const debugDnd = true;

  const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

  const logKanbanSnapshot = (label) => {
    if (!debugDnd) return;
    try {
      const snap = (kanban.columns || []).map((c) => ({
        colId: c.id,
        name: c.name,
        ideaIds: (c.ideas || []).map((i) => i.id),
      }));
      console.log(`[Kanban] ${label}`, snap);
    } catch (e) {
      console.log(`[Kanban] ${label} (failed)`, e);
    }
  };

  const safeRefetchKanban = async () => {
    const r = kanban?.refetchKanban;

    // Debug: show actual shape once, when enabled
    if (debugDnd) {
      try {
        console.log('[Kanban] refetchKanban typeof:', typeof r, 'value:', r);
        if (r && typeof r === 'object') console.log('[Kanban] refetchKanban keys:', Object.keys(r));
        if (r?.current && typeof r.current === 'object') console.log('[Kanban] refetchKanban.current keys:', Object.keys(r.current));
      } catch {
        // ignore debug errors
      }
    }

    // Case 1: function
    if (typeof r === 'function') return await r();

    // Case 2: { refetch: fn }
    if (r && typeof r.refetch === 'function') return await r.refetch();

    // Case 3: { current: fn }
    if (r?.current && typeof r.current === 'function') return await r.current();

    // Case 4: { current: { refetch: fn } }
    if (r?.current?.refetch && typeof r.current.refetch === 'function') return await r.current.refetch();

    throw new Error('refetchKanban has no callable refetch');
  };

  const handleDragStart = (evt) => {
    if (debugDnd) console.log('[DND] start', { active: evt?.active?.id });
    dnd.handleDragStart(evt);
  };

  const handleDragCancel = (evt) => {
    if (debugDnd) console.log('[DND] cancel');
    dnd.handleDragCancel(evt);
  };

  const handleDragOver = (evt) => {
    const activeId = evt?.active?.id;
    const overId = evt?.over?.id ?? null;

    if (debugDnd) console.log('[DND] over', { active: activeId, over: overId });

    // When pointer leaves droppable areas, over can be null.
    if (!overId) return;

    dnd.handleDragOver(evt);
  };

  const handleDragEnd = async (evt) => {
    if (debugDnd) console.log('[DND] end', { active: evt?.active?.id, over: evt?.over?.id });

    logKanbanSnapshot('before handleDragEnd');

    try {
      await dnd.handleDragEnd(evt);
    } catch (e) {
      if (debugDnd) console.error('[DND] handleDragEnd threw', e);
    }

    logKanbanSnapshot('after handleDragEnd (optimistic)');

    // Debug: log a concise event summary
    if (debugDnd) {
      console.log('[DND] end summary', {
        activeId: evt?.active?.id,
        overId: evt?.over?.id,
        activeDragIdea: dnd.activeDragIdea?.id,
      });
    }

    // Force a refetch after a tiny delay to validate backend persistence without racing updates.
    try {
      await sleep(150);
      await safeRefetchKanban();
      logKanbanSnapshot('after refetchKanban');
    } catch (e) {
      if (debugDnd) console.log('[Kanban] refetchKanban failed', e);
    }
  };

  if (authLoading || !authenticated) return null;

  if (!boardId) {
    return (
      <main className={styles.page}>
        <div className={styles.state}>Board invalide.</div>
      </main>
    );
  }

  const activeColumn = kanban.columns[activeIndex] || null;

  const renderCard = ({ boardId, idea, highlightedIdeaId, styles }) => (
    <KanbanCard
      styles={styles}
      boardId={boardId}
      idea={idea}
      highlightedIdeaId={highlightedIdeaId}
    />
  );

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>{kanban.boardName}</h1>
          <p className={styles.subtitle}>Vue Kanban — drag & drop.</p>
        </div>

        <div className={styles.actions}>
          <Link className={styles.back} href="/boards">
            ← Mes boards
          </Link>
        </div>
      </header>

      {kanban.loading && <div className={styles.state}>Chargement du kanban…</div>}
      {kanban.error && <div className={styles.error}>Erreur : {kanban.error}</div>}

      {!kanban.loading && !kanban.error && kanban.columns.length === 0 && (
        <div className={styles.state}>Aucune colonne pour ce board.</div>
      )}

      {!kanban.loading && !kanban.error && kanban.columns.length > 0 && (
        <>
          <KanbanTabs
            styles={styles}
            columns={kanban.columns}
            activeIndex={activeIndex}
            setActiveIndex={setActiveIndex}
            isMobile={isMobile}
            columnRefs={columnRefs}
          />

          <KanbanQuickAdd
            styles={styles}
            canQuickAdd={kanban.canQuickAdd}
            columns={kanban.columns}
            activeColumn={activeColumn}
            onQuickAdd={kanban.quickAdd}
          />

          <DndContext
            sensors={dnd.sensors}
            collisionDetection={dnd.collisionDetection}
            onDragStart={handleDragStart}
            onDragCancel={handleDragCancel}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            {isMobile ? (
              <KanbanBoardMobile
                styles={styles}
                columns={kanban.columns}
                activeIndex={activeIndex}
                setActiveIndex={setActiveIndex}
                boardId={boardId}
                highlightedIdeaId={kanban.highlightedIdeaId}
                renderCard={renderCard}
              />
            ) : (
              <KanbanBoardDesktop
                styles={styles}
                columns={kanban.columns}
                boardId={boardId}
                highlightedIdeaId={kanban.highlightedIdeaId}
                renderCard={renderCard}
                columnRefs={columnRefs}
              />
            )}

            <DragOverlay>
              <KanbanDragOverlay styles={styles} activeDragIdea={dnd.activeDragIdea} />
            </DragOverlay>
          </DndContext>
        </>
      )}
    </main>
  );
}