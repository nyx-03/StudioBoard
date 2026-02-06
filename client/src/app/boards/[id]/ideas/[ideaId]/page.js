'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import styles from './page.module.css';
import { useRequireAuth } from '../../../../../hooks/useRequireAuth';
import { apiGet } from '../../../../../lib/api';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';

export default function IdeaDetailPage() {
  const { authenticated, loading: authLoading } = useRequireAuth();
  const params = useParams();

  const boardId = useMemo(() => Number(params?.id), [params]);
  const ideaId = useMemo(() => Number(params?.ideaId), [params]);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (authLoading || !authenticated) return;
    if (!boardId || !ideaId) return;

    let cancelled = false;

    async function loadIdea() {
      try {
        setLoading(true);
        const json = await apiGet(`/api/boards/${boardId}/ideas/${ideaId}/`);
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setError(err.message || 'Impossible de charger la carte');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadIdea();
    return () => {
      cancelled = true;
    };
  }, [authLoading, authenticated, boardId, ideaId]);

  if (authLoading || !authenticated) return null;

  if (!boardId || !ideaId) {
    return (
      <main className={styles.page}>
        <div className={styles.state}>Carte invalide.</div>
      </main>
    );
  }

  const boardName = data?.board?.name;
  const idea = data?.idea;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>{idea?.title || 'Carte'}</h1>
          {boardName && (
            <div className={styles.subtitle}>Board : {boardName}</div>
          )}
        </div>

        <div className={styles.actions}>
          <Link
            className={styles.back}
            href={`/boards/${boardId}`}
          >
            ← Retour au Kanban
          </Link>

          <Link
            className={styles.edit}
            href={`/boards/${boardId}/ideas/${ideaId}/edit`}
          >
            ✏️ Modifier
          </Link>
        </div>
      </header>

      {loading && <div className={styles.state}>Chargement de la carte…</div>}

      {error && <div className={styles.error}>Erreur : {error}</div>}

      {!loading && !error && idea && (
        <section className={styles.card}>
          <div className={styles.meta}>
            <span className={styles.pill}>Colonne : {idea.column?.name}</span>
            {idea.status && <span className={styles.pill}>Statut : {idea.status}</span>}
            {idea.impact !== null && (
              <span className={styles.pill}>Impact : {idea.impact}</span>
            )}
            {idea.next_action && (
              <span className={styles.pill}>Next : {idea.next_action}</span>
            )}
          </div>

          {Array.isArray(idea.tags) && idea.tags.length > 0 && (
            <div className={styles.tags}>
              {idea.tags.map((t) => (
                <span key={t} className={styles.tag}>#{t}</span>
              ))}
            </div>
          )}

          <div className={styles.body}>
            {idea.body_md ? (
              <div className={styles.md}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeSanitize]}
                  components={{
                    a: ({ node, ...props }) => (
                      <a {...props} target="_blank" rel="noreferrer" />
                    ),
                    code: ({ inline, className, children, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      if (inline) {
                        return (
                          <code className={styles.inlineCode} {...props}>
                            {children}
                          </code>
                        );
                      }
                      return (
                        <pre className={styles.codeBlock}>
                          <code className={className} data-lang={match?.[1] || ''} {...props}>
                            {children}
                          </code>
                        </pre>
                      );
                    },
                  }}
                >
                  {idea.body_md}
                </ReactMarkdown>
              </div>
            ) : (
              <div className={styles.empty}>Aucune description.</div>
            )}
          </div>
        </section>
      )}
    </main>
  );
}