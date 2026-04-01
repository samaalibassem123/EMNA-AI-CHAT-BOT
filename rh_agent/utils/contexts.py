from langchain_core.messages import HumanMessage
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_table_context(session: Session, table_names: list[str]) -> str:
    """
    Returns LLM-friendly schema context without loading full table data.
    Includes column types, nullability, row count, and 3-row sample.
    """
    context_parts = []

    for table in table_names:
        # Column metadata from information_schema (no table scan)
        cols_result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table AND table_schema = 'public'
            ORDER BY ordinal_position
        """), {"table": table})
        columns = cols_result.fetchall()

        # Fast approximate row count from pg_stat (no COUNT(*) scan!)
        count_result = session.execute(text("""
            SELECT reltuples::bigint AS estimate
            FROM pg_class WHERE relname = :table
        """), {"table": table})
        row_estimate = count_result.scalar() or 0

        # 3-row sample for the LLM to understand data format
        sample_result = session.execute(
            text(f"SELECT * FROM {table} LIMIT 3")
        )
        sample_rows = sample_result.fetchall()

        col_lines = "\n".join(
            f"  - {c.column_name} ({c.data_type})"
            f"{'  NOT NULL' if c.is_nullable == 'NO' else ''}"
            for c in columns
        )

        context_parts.append(
            f"Table: {table}\n"
            f"Approx rows: {row_estimate:,}\n"
            f"Columns:\n{col_lines}\n"
            f"Sample (3 rows): {[dict(r._mapping) for r in sample_rows]}\n"
        )

    return "\n\n".join(context_parts)

def get_last_user_message(messages):
    return next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)),
        None
    )