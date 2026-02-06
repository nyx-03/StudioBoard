// src/features/kanban/dnd/dndIds.js

export const dndIdeaId = (id) => `idea-${id}`;
export const dndColId = (id) => `col-${id}`;

export const parseIdeaId = (id) =>
  String(id).startsWith('idea-') ? Number(String(id).replace('idea-', '')) : null;

export const parseColId = (id) =>
  String(id).startsWith('col-') ? Number(String(id).replace('col-', '')) : null;

export const findColumnByIdeaDndId = (ideaDndId, cols) => {
  const n = parseIdeaId(ideaDndId);
  if (n == null) return null;
  return cols.find((c) => (c.ideas || []).some((i) => Number(i.id) === n)) || null;
};

export const resolveContainerDndId = (anyDndId, cols) => {
  const colNum = parseColId(anyDndId);
  if (colNum != null) return dndColId(colNum);

  const byIdea = findColumnByIdeaDndId(anyDndId, cols);
  return byIdea ? dndColId(byIdea.id) : null;
};

export const getIdeaIndexByDndId = (col, ideaDndId) => {
  const n = parseIdeaId(ideaDndId);
  if (n == null) return -1;
  return (col?.ideas || []).findIndex((i) => Number(i.id) === n);
};

export const getOverIdeaIndexByDndId = (col, overDndId) => {
  const n = parseIdeaId(overDndId);
  if (n == null) return -1;
  return (col?.ideas || []).findIndex((i) => Number(i.id) === n);
};