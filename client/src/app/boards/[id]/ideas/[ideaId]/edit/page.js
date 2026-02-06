

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import styles from './page.module.css';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { apiGet, apiPost } from '@/lib/api';

export default function IdeaEditPage() {
  const router = useRouter();
  const params = useParams();

  const boardId = params?.id;
  const ideaId = params?.ideaId;

  const { authenticated, loading: authLoading } = useRequireAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [saved, setSaved] = useState(false);

  const [boardName, setBoardName] = useState('');
  const [columns, setColumns] = useState([]);

  // Form fields
  const [title, setTitle] = useState('');
  const [bodyMd, setBodyMd] = useState('');
  const [columnId, setColumnId] = useState('');
  const [tagsText, setTagsText] = useState('');
  const [impact, setImpact] = useState('');
  const [nextAction, setNextAction] = useState('');

  // Determine whether optional fields exist (based on API payload)
  const [hasImpact, setHasImpact] = useState(false);
  const [hasNextAction, setHasNextAction] = useState(false);

  const tagsPreview = useMemo(() => {
    return (tagsText || '')
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
  }, [tagsText]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (authLoading) return;
      if (!authenticated) {
        // useRequireAuth will redirect, but keep UI safe
        return;
      }
      if (!boardId || !ideaId) return;

      setLoading(true);
      setError(null);
      setSaved(false);

      try {
        // 1) load idea detail
        const detail = await apiGet(`/api/boards/${boardId}/ideas/${ideaId}/`);

        // 2) load board columns (kanban endpoint already returns columns)
        const kanban = await apiGet(`/api/boards/${boardId}/kanban/`);

        if (cancelled) return;

        const idea = detail?.idea;
        const board = detail?.board || kanban?.board;

        setBoardName(board?.name || '');
        setColumns(Array.isArray(kanban?.columns) ? kanban.columns : []);

        setTitle(idea?.title || '');
        setBodyMd(idea?.body_md || '');
        setColumnId(String(idea?.column?.id || ''));

        const tags = Array.isArray(idea?.tags) ? idea.tags : [];
        setTagsText(tags.join(', '));

        // Optional fields
        const impactVal = idea?.impact;
        setHasImpact(typeof impactVal !== 'undefined');
        setImpact(impactVal === null || typeof impactVal === 'undefined' ? '' : String(impactVal));

        const nextVal = idea?.next_action;
        setHasNextAction(typeof nextVal !== 'undefined');
        setNextAction(nextVal || '');
      } catch (err) {
        if (!cancelled) setError(err.message || "Impossible de charger l'idée");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [authLoading, authenticated, boardId, ideaId]);

  const handleSave = async (e) => {
    e?.preventDefault?.();
    if (!boardId || !ideaId) return;

    const cleanTitle = (title || '').trim();
    if (!cleanTitle) {
      setSaveError('Le titre est requis.');
      return;
    }

    // Normalize tags for backend
    const tags = (tagsText || '')
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = {
      title: cleanTitle,
      body_md: bodyMd || '',
      column_id: columnId ? Number(columnId) : undefined,
      tags,
    };

    if (hasImpact) {
      payload.impact = impact === '' ? null : Number(impact);
    }
    if (hasNextAction) {
      payload.next_action = nextAction || '';
    }

    try {
      setSaving(true);
      setSaveError(null);
      setSaved(false);

      await apiPost(`/api/boards/${boardId}/ideas/${ideaId}/update/`, payload);

      setSaved(true);
      // Optional: go back to detail after save
      router.push(`/boards/${boardId}/ideas/${ideaId}`);
    } catch (err) {
      setSaveError(err.message || "Impossible d'enregistrer");
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || !authenticated) {
    return (
      <div className={styles.page}>
        <div className={styles.shell}>
          <div className={styles.panel}>Chargement…</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.shell}>
        <header className={styles.header}>
          <div>
            <div className={styles.kicker}>StudioBoard</div>
            <h1 className={styles.h1}>Modifier une idée</h1>
            <div className={styles.sub}>
              <span className={styles.pill}>Board : <b>{boardName || `#${boardId}`}</b></span>
              <span className={styles.pill}>ID : <b>#{ideaId}</b></span>
            </div>
          </div>

          <div className={styles.actions}>
            <Link className={styles.btnSecondary} href={`/boards/${boardId}/ideas/${ideaId}`}>
              ← Retour
            </Link>
            <button className={styles.btnPrimary} onClick={handleSave} disabled={saving || loading}>
              {saving ? 'Enregistrement…' : 'Enregistrer'}
            </button>
          </div>
        </header>

        {error && <div className={styles.alert}>Erreur : {error}</div>}
        {saveError && <div className={styles.alert}>Erreur : {saveError}</div>}
        {saved && <div className={styles.notice}>Sauvegardé ✅</div>}

        <div className={styles.grid}>
          <form className={styles.panel} onSubmit={handleSave}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="title">Titre</label>
              <input
                id="title"
                className={styles.input}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Titre de l'idée"
              />
            </div>

            <div className={styles.row2}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="column">Colonne</label>
                <select
                  id="column"
                  className={styles.select}
                  value={columnId}
                  onChange={(e) => setColumnId(e.target.value)}
                >
                  <option value="" disabled>
                    Choisir…
                  </option>
                  {columns.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              {hasImpact && (
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="impact">Impact</label>
                  <input
                    id="impact"
                    className={styles.input}
                    value={impact}
                    onChange={(e) => setImpact(e.target.value)}
                    placeholder="Ex: 3"
                    inputMode="numeric"
                  />
                </div>
              )}
            </div>

            {hasNextAction && (
              <div className={styles.field}>
                <label className={styles.label} htmlFor="nextAction">Next action</label>
                <input
                  id="nextAction"
                  className={styles.input}
                  value={nextAction}
                  onChange={(e) => setNextAction(e.target.value)}
                  placeholder="Prochaine action"
                />
              </div>
            )}

            <div className={styles.field}>
              <label className={styles.label} htmlFor="tags">Tags</label>
              <input
                id="tags"
                className={styles.input}
                value={tagsText}
                onChange={(e) => setTagsText(e.target.value)}
                placeholder="ux, next, api"
              />
              <div className={styles.hint}>
                {tagsPreview.length > 0 ? (
                  <div className={styles.tagsPreview}>
                    {tagsPreview.map((t) => (
                      <span key={t} className={styles.tag}>#{t}</span>
                    ))}
                  </div>
                ) : (
                  <span>Aucun tag.</span>
                )}
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="body">Description (Markdown)</label>
              <textarea
                id="body"
                className={styles.textarea}
                value={bodyMd}
                onChange={(e) => setBodyMd(e.target.value)}
                placeholder="Écris en Markdown…"
                rows={14}
              />
            </div>

            <div className={styles.footer}>
              <button className={styles.btnPrimary} type="submit" disabled={saving || loading}>
                {saving ? 'Enregistrement…' : 'Enregistrer'}
              </button>
              <Link className={styles.btnSecondary} href={`/boards/${boardId}/ideas/${ideaId}`}>
                Annuler
              </Link>
            </div>
          </form>

          <div className={styles.panel}>
            <div className={styles.previewHeader}>
              <div>
                <div className={styles.label}>Preview</div>
                <div className={styles.previewSub}>Rendu live du Markdown</div>
              </div>
            </div>

            <div className={styles.preview}>
              {bodyMd?.trim() ? (
                <div className={styles.md}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {bodyMd}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className={styles.muted}>Aucune description pour le moment.</div>
              )}
            </div>
          </div>
        </div>

        <div className={styles.backLink}>
          <Link className={styles.link} href={`/boards/${boardId}`}>
            ← Retour au Kanban
          </Link>
        </div>
      </div>
    </div>
  );
}