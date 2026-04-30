"""SQLite FTS5 search backend for the Sherlock index."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from fetch import framework_is_installed, index_db_path


@contextmanager
def _conn():
    con = sqlite3.connect(index_db_path())
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def search_index(
    query: str,
    framework: str | None = None,
    kind: str | None = None,
    limit: int = 10,
) -> list[dict]:
    where = ["docs_fts MATCH ?"]
    params: list = [query]
    if framework:
        where.append("docs.framework = ?")
        params.append(framework.lower())
    if kind:
        where.append("docs.kind = ?")
        params.append(kind.lower())

    sql = f"""
        SELECT docs.path, docs.title, docs.framework, docs.kind,
               docs.summary, bm25(docs_fts) AS score
        FROM docs_fts
        JOIN docs ON docs.rowid = docs_fts.rowid
        WHERE {' AND '.join(where)}
        ORDER BY score
        LIMIT ?
    """
    params.append(limit)

    with _conn() as con:
        rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def list_frameworks_status() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT framework, COUNT(*) AS pages FROM docs "
            "GROUP BY framework ORDER BY framework"
        ).fetchall()
    return [
        {
            "framework": r["framework"],
            "pages": r["pages"],
            "installed": framework_is_installed(r["framework"]),
        }
        for r in rows
    ]
