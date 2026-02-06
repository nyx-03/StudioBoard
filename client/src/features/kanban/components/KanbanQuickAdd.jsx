// src/features/kanban/components/KanbanQuickAdd.jsx

import { useState } from 'react';

export function KanbanQuickAdd({ styles, canQuickAdd, columns, activeColumn, onQuickAdd }) {
  const [quickTitle, setQuickTitle] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [quickError, setQuickError] = useState(null);

  if (!columns?.length) return null;

  const columnId = activeColumn?.id || columns[0]?.id || null;

  const handleSubmit = async (e) => {
    e?.preventDefault?.();
    if (!canQuickAdd) return;

    const text = (quickTitle || '').trim();
    if (!text) {
      setQuickError('Le titre est requis.');
      return;
    }
    if (!columnId) {
      setQuickError('Aucune colonne disponible.');
      return;
    }

    try {
      setSubmitting(true);
      setQuickError(null);
      await onQuickAdd({ text, columnId });
      setQuickTitle('');
    } catch (err) {
      setQuickError(err?.message || "Impossible d'ajouter l'idée");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className={styles.quickAdd} onSubmit={handleSubmit}>
      <input
        className={styles.quickInput}
        value={quickTitle}
        onChange={(e) => setQuickTitle(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            setQuickTitle('');
            setQuickError(null);
            e.currentTarget.blur();
          }
        }}
        placeholder="Ajouter une idée… (#tags @colonne !impact)"
        aria-label="Ajouter une idée"
      />
      <button
        className={styles.quickBtn}
        type="submit"
        disabled={submitting}
        title={activeColumn ? `Ajouter dans: ${activeColumn.name}` : 'Ajouter'}
      >
        {submitting ? 'Ajout…' : 'Ajouter'}
      </button>

      {quickError && <div className={styles.quickError}>Erreur : {quickError}</div>}
    </form>
  );
}