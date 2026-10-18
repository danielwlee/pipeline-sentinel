"""Chunk a dbt model's SQL for embedding/retrieval.

Granularity (docs/wiki/chunking.md): ONE chunk per model. A model's SQL is short
enough to fit in a single 32k context window, and chunking finer would tear
apart CTEs and break the lineage link. We keep the whole model as one chunk.

sqlglot cannot parse raw jinja (`{% set %}`, `{{ ref() }}`), so we render a
lightweight "jinja-stripped" copy good enough for sqlglot to read the structure.
The original jinja template is preserved verbatim in `raw_code` so M4's diff still
sees the real template.
"""
from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

# Jinja-stripping goal: *parseable* SQL for sqlglot, not a faithful render --
# dbt itself renders jinja for execution. We only need a structural skeleton so
# the LLM/reranker can see columns, CTEs, and joins.
#
# dbt templates nest blocks ({% for %} around {% if %}) and reuse `else`/`endif`
# as many times as a loop iterates, so a naive per-tag regex would unbalance the
# SQL. We instead tokenize, collapse each *balanced* block to one placeholder
# (so parens stay balanced), then strip bare `{% set %}` and `{{ }}` renders.

# `{{ ... }}` render, or `{% tag %}` (allow whitespace/whitespace-ctrl `-`/`+`).
_TOKEN_RE = re.compile(r"{{\s*(.*?)\s*}}|\{%[-+]?\s*(.*?)[-+]?[^%]*%}", re.DOTALL)

# Block keywords that open / close a nested scope.
_OPEN = {"for", "if", "macro", "with", "document"}
_CLOSE = {
    "endfor": "for",
    "endif": "if",
    "endmacro": "macro",
    "endwith": "with",
    "enddocument": "document",
}


def _tokenize(code):
    """Yield ('text'|'render'|'tag', payload) tokens for jinja in *code*."""
    pos = 0
    for m in _TOKEN_RE.finditer(code):
        if m.start() > pos:
            yield ("text", code[pos : m.start()])
        if m.group(1) is not None:  # {{ ... }}
            yield ("render", m.group(1).strip())
        else:  # {% ... %}
            yield ("tag", m.group(2).strip())
        pos = m.end()
    if pos < len(code):
        yield ("text", code[pos:])


def _render_expr(inner):
    """Turn `{{ ref('x') }}` / `{{ source('s','x') }}` into a bare identifier."""
    mm = re.match(r"ref\(\s*['\"]([^'\"]+)['\"]\s*\)", inner)
    if mm:
        return mm.group(1)
    mm = re.match(r"source\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", inner)
    if mm:
        return f"{mm.group(1)}_{mm.group(2)}"
    return ""


def strip_jinja(code):
    """Render jinja away enough that sqlglot can parse the result.

    Balances nested/repeated blocks first (so `else`/`endif` inside a `{% for %}`
    no longer unbalances the SQL), then strips `{% set %}` and `{{ }}` renders.
    """
    # Pass 1: turn every tag/render into a (placeholder, kind) token, balancing
    # open/close with a stack so nested blocks collapse to a single empty slot.
    pieces = []  # list of str output segments
    stack = []  # indices of pieces that are open-block placeholders
    for kind, payload in _tokenize(code):
        if kind == "text":
            pieces.append(payload)
        elif kind == "render":
            pieces.append(_render_expr(payload))
        else:
            kw = payload.split()[0].lower() if payload else ""
            if kw in _OPEN:
                stack.append(len(pieces))
                pieces.append("")  # placeholder for the whole block
            elif kw in _CLOSE:
                if stack:
                    stack.pop()
            elif kw == "else":
                # Inside a block we're discarding; harmless no-op.
                pass
            elif kw == "set":
                pass  # drop the assignment entirely
            else:
                # Unknown standalone tag -> drop (don't leave dangling jinja).
                pass
    # Unmatched opens leave dangling placeholders -- leave them as "" (harmless).
    return "".join(pieces)


def parse_structure(raw_code):
    """Return a structural summary of a model's SQL via sqlglot.

    Keys: ctes (names), selects (top-level projection expressions), parsed (bool),
    error (str|None). On parse failure we degrade gracefully rather than raising,
    so one odd model never aborts ingestion.
    """
    stripped = strip_jinja(raw_code)
    structure = {"ctes": [], "selects": [], "parsed": False, "error": None}
    try:
        statements = [s for s in sqlglot.parse(stripped, read="duckdb") if s is not None]
        structure["parsed"] = bool(statements)
    except Exception as e:  # noqa: BLE001 - degrade, don't crash ingestion
        structure["error"] = f"{type(e).__name__}: {e}"
        return structure

    ctes = []
    selects = []
    for stmt in statements:
        for cte in stmt.find_all(exp.CTE):
            name = cte.alias
            if name:
                ctes.append(name)
        for proj in _top_level_selects(stmt):
            if isinstance(proj, exp.Alias):
                selects.append(proj.alias)
            elif isinstance(proj, exp.Star):
                selects.append("*")
            else:
                selects.append(proj.sql(dialect="duckdb"))
    structure["ctes"] = sorted(set(ctes))
    structure["selects"] = selects
    return structure


def _top_level_selects(stmt):
    """Yield the projections of the *outermost* SELECT of a statement."""
    for sel in stmt.find_all(exp.Select):
        parent = sel.parent
        nested = False
        while parent is not None and parent is not stmt:
            if isinstance(parent, (exp.Select, exp.CTE)):
                nested = True
                break
            parent = parent.parent
        if not nested:
            return sel.expressions
    main = stmt.find(exp.Select)
    return main.expressions if main else []
