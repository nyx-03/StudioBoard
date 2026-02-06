// src/features/kanban/hooks/useKanbanData.js

import { useEffect, useMemo, useRef, useState } from 'react';
import { apiGet, apiPost } from '@/lib/api';

export function useKanbanData({ boardId, authenticated, authLoading }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [highlightedIdeaId, setHighlightedIdeaId] = useState(null);

  const refetchKanban = useRef(null);
  const dataRef = useRef(null);

  const columns = useMemo(() => (Array.isArray(data?.columns) ? data.columns : []), [data]);
  const boardName = useMemo(
    () => data?.board?.name || (boardId ? `Board #${boardId}` : 'Board'),
    [data, boardId]
  );

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  useEffect(() => {
    if (authLoading) return;
    if (!authenticated) return;
    if (!boardId) return;

    let cancelled = false;

    async function loadKanban() {
      try {
        setLoading(true);
        setError(null);
        const json = await apiGet(`/api/boards/${boardId}/kanban/`);
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || 'Erreur inconnue');
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    setHighlightedIdeaId(null);
    loadKanban();
    refetchKanban.current = loadKanban;

    return () => {
      cancelled = true;
    };
  }, [authLoading, authenticated, boardId]);

  const canQuickAdd = !loading && !error && columns.length > 0;

  async function quickAdd({ text, columnId }) {
    if (!boardId) throw new Error('Board invalide');
    const created = await apiPost(`/api/boards/${boardId}/ideas/quick-add/`, {
      text,
      column_id: columnId,
    });

    const newId = created?.idea?.id ?? null;
    if (newId) {
      setHighlightedIdeaId(newId);
      window.setTimeout(() => setHighlightedIdeaId(null), 1200);
    }

    if (typeof refetchKanban.current === 'function') {
      await refetchKanban.current();
    }

    return created;
  }

  return {
    data,
    setData,
    dataRef,
    columns,
    boardName,

    loading,
    error,

    refetchKanban,
    canQuickAdd,

    highlightedIdeaId,
    quickAdd,
  };
}