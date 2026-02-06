// useKanbanDnd.js
import { useRef, useState } from 'react';
import { PointerSensor, useSensor, useSensors, closestCenter } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';

import {
  dndColId,
  parseColId,
  parseIdeaId,
  resolveContainerDndId,
  findColumnByIdeaDndId,
  getIdeaIndexByDndId,
  getOverIdeaIndexByDndId,
} from './dndIds';

import { apiPost } from '@/lib/api';

export function useKanbanDnd({ boardId, columns, setData, dataRef, refetchKanban }) {
  const safeRefetch = async () => {
    try {
      if (typeof refetchKanban === 'function') {
        await refetchKanban();
      } else if (refetchKanban && typeof refetchKanban.current === 'function') {
        await refetchKanban.current();
      }
    } catch (_) {}
  };

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));
  const collisionDetection = closestCenter;

  const [activeDragIdea, setActiveDragIdea] = useState(null);

  // ✅ NEW: garder la source de vérité du "from" au moment du dragStart
  const originRef = useRef({ activeId: null, fromContainerId: null });

  // RAF throttle for dragOver state updates (prevents Safari/React update loops)
  const lastDragOverRef = useRef({ activeId: null, overId: null, fromId: null, toId: null });
  const dragOverRafRef = useRef(0);
  const pendingDragOverRef = useRef(null);

  const cleanupOverRaf = () => {
    pendingDragOverRef.current = null;
    if (dragOverRafRef.current) {
      cancelAnimationFrame(dragOverRafRef.current);
      dragOverRafRef.current = 0;
    }
    lastDragOverRef.current = { activeId: null, overId: null, fromId: null, toId: null };
  };

  const resetOrigin = () => {
    originRef.current = { activeId: null, fromContainerId: null };
  };

  const handleDragStart = (event) => {
    const { active } = event;
    const activeId = String(active.id);
    const ideaNum = parseIdeaId(activeId);

    const found = columns
      .flatMap((c) => c.ideas || [])
      .find((i) => ideaNum != null && Number(i.id) === ideaNum);

    // ✅ NEW: déterminer la colonne d’origine au moment exact du start (avant l’optimistic move)
    const fromCol = findColumnByIdeaDndId(activeId, columns);
    originRef.current = {
      activeId,
      fromContainerId: fromCol ? dndColId(fromCol.id) : null,
    };

    setActiveDragIdea(found || null);
    cleanupOverRaf();
  };

  const handleDragCancel = () => {
    setActiveDragIdea(null);
    cleanupOverRaf();
    resetOrigin();
  };

  const handleDragOver = (event) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    pendingDragOverRef.current = { activeId, overId };
    if (dragOverRafRef.current) return;

    dragOverRafRef.current = requestAnimationFrame(() => {
      dragOverRafRef.current = 0;

      const pending = pendingDragOverRef.current;
      pendingDragOverRef.current = null;
      if (!pending) return;

      const { activeId: aId, overId: oId } = pending;

      setData((prev) => {
        if (!prev || !Array.isArray(prev.columns)) return prev;
        const cols = prev.columns;

        const fromCol = findColumnByIdeaDndId(aId, cols);
        const toColDndId = resolveContainerDndId(oId, cols);
        if (!fromCol || !toColDndId) return prev;

        const fromId = dndColId(fromCol.id);
        const toId = String(toColDndId);

        const last = lastDragOverRef.current;
        if (
          last &&
          last.activeId === aId &&
          last.overId === oId &&
          last.fromId === fromId &&
          last.toId === toId
        ) {
          return prev;
        }
        lastDragOverRef.current = { activeId: aId, overId: oId, fromId, toId };

        // Same column -> reorder handled onDragEnd
        if (fromId === toId) return prev;

        const fromNum = parseColId(fromId);
        const toNum = parseColId(toId);
        if (fromNum == null || toNum == null) return prev;

        const prevFrom = cols.find((c) => Number(c.id) === fromNum);
        const prevTo = cols.find((c) => Number(c.id) === toNum);
        if (!prevFrom || !prevTo) return prev;

        const prevFromIdeas = Array.isArray(prevFrom.ideas) ? prevFrom.ideas : [];
        const prevToIdeas = Array.isArray(prevTo.ideas) ? prevTo.ideas : [];

        const aNum = parseIdeaId(aId);
        if (aNum == null) return prev;

        const idx = prevFromIdeas.findIndex((i) => Number(i.id) === aNum);
        if (idx < 0) return prev;

        const movedIdea = prevFromIdeas[idx];
        const nextFromIdeas = prevFromIdeas.filter((_, k) => k !== idx);

        // Insert before hovered idea if hovering a card; else append
        const overIdeaNum = parseIdeaId(oId);
        const overIndexInTo = prevToIdeas.findIndex(
          (i) => overIdeaNum !== null && Number(i.id) === overIdeaNum
        );
        const insertIndex = overIndexInTo >= 0 ? overIndexInTo : prevToIdeas.length;

        const toWithout = prevToIdeas.filter((i) => Number(i.id) !== aNum);
        const safeInsert = Math.max(0, Math.min(insertIndex, toWithout.length));

        const nextToIdeas = [
          ...toWithout.slice(0, safeInsert),
          movedIdea,
          ...toWithout.slice(safeInsert),
        ];

        return {
          ...prev,
          columns: cols.map((c) => {
            const cid = dndColId(c.id);
            if (cid === fromId) return { ...c, ideas: nextFromIdeas };
            if (cid === toId) return { ...c, ideas: nextToIdeas };
            return c;
          }),
        };
      });
    });
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;

    setActiveDragIdea(null);
    cleanupOverRaf();
    if (!over) {
      resetOrigin();
      return;
    }

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeIdeaNum = parseIdeaId(activeId);
    if (activeIdeaNum == null) {
      resetOrigin();
      return;
    }

    const colsNow = Array.isArray(dataRef.current?.columns) ? dataRef.current.columns : columns;

    const resolveContainerIdSafe = (dndId) => {
      const asStr = String(dndId || '');
      if (parseColId(asStr) != null) return asStr;

      const col = findColumnByIdeaDndId(asStr, colsNow);
      if (col) return dndColId(col.id);

      return resolveContainerDndId(asStr, colsNow);
    };

    // ✅ NEW: from = source de vérité du dragStart (sinon fallback)
    const origin = originRef.current;
    const originFrom = origin?.activeId === activeId ? origin.fromContainerId : null;

    const fromContainerId =
      originFrom ||
      (active?.data?.current?.sortable?.containerId
        ? String(active.data.current.sortable.containerId)
        : resolveContainerIdSafe(activeId));

    const toContainerId =
      over?.data?.current?.sortable?.containerId
        ? String(over.data.current.sortable.containerId)
        : resolveContainerIdSafe(overId);

    resetOrigin();

    if (!fromContainerId || !toContainerId) return;

    // ✅ IMPORTANT: on compare avec la vraie colonne d’origine (pas celle après optimistic move)
    if (fromContainerId === toContainerId) {
      const fromNum = parseColId(fromContainerId);
      if (fromNum == null) return;

      const col = colsNow.find((c) => Number(c.id) === fromNum);
      if (!col) return;

      const oldIndex = getIdeaIndexByDndId(col, activeId);
      let newIndex = over?.data?.current?.sortable?.index ?? getOverIdeaIndexByDndId(col, overId);

      if (newIndex < 0) newIndex = Math.max(0, (col.ideas || []).length - 1);
      if (oldIndex < 0 || oldIndex === newIndex) return;

      const newIdeas = arrayMove(col.ideas || [], oldIndex, newIndex);

      setData((prev) => ({
        ...prev,
        columns: prev.columns.map((c) =>
          Number(c.id) === fromNum ? { ...c, ideas: newIdeas } : c
        ),
      }));

      try {
        await apiPost(`/api/boards/${boardId}/columns/${fromNum}/reorder/`, {
          ordered_ids: newIdeas.map((i) => i.id),
        });
      } catch (err) {
        await safeRefetch();
      }
      return;
    }

    // Inter-column move
    try {
      const fromNum = parseColId(fromContainerId);
      const toNum = parseColId(toContainerId);
      if (fromNum == null || toNum == null) return;

      const toColAtDrop = colsNow.find((c) => Number(c.id) === toNum) || null;
      const toIdeasRaw = Array.isArray(toColAtDrop?.ideas) ? toColAtDrop.ideas : [];

      let targetIndex = toIdeasRaw.findIndex((i) => Number(i.id) === Number(activeIdeaNum));
      if (targetIndex < 0) {
        const overIdeaNum = parseIdeaId(overId);
        const toIdeas = toIdeasRaw.filter((i) => Number(i.id) !== Number(activeIdeaNum));

        if (overIdeaNum != null) {
          const idx = toIdeas.findIndex((i) => Number(i.id) === Number(overIdeaNum));
          targetIndex = idx >= 0 ? idx : toIdeas.length;
        } else {
          targetIndex = toIdeas.length;
        }
      }

      if (!Number.isFinite(targetIndex) || targetIndex < 0) targetIndex = 0;

      await apiPost(`/api/boards/${boardId}/ideas/${activeIdeaNum}/move/`, {
        from_column_id: Number(fromNum),
        to_column_id: Number(toNum),
        target_index: Number(targetIndex),
      });

      await safeRefetch();
    } catch (err) {
      await safeRefetch();
    }
  };

  return {
    sensors,
    collisionDetection,
    activeDragIdea,
    handleDragStart,
    handleDragCancel,
    handleDragOver,
    handleDragEnd,
  };
}