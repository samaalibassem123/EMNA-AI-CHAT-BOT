from langchain_core.messages import HumanMessage
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_table_context(session: Session, table_names: list[str]) -> str:
    """
    Returns LLM-friendly schema context for SQL Server data warehouse.
    Includes column types, nullability, and 3-row sample.
    Designed for star/galaxy schema with dimension and fact tables.
    """
    context_parts = []

    for table in table_names:
        # Get column metadata from SQL Server information_schema
        cols_query = text("""
            SELECT 
                COLUMN_NAME as column_name,
                DATA_TYPE as data_type,
                IS_NULLABLE as is_nullable,
                COLUMN_DEFAULT as column_default
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table_name AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
        """)
        
        try:
            cols_result = session.execute(cols_query, {"table_name": table})
            columns = cols_result.fetchall()
        except Exception as e:
            print(f"Error fetching columns for {table}: {e}")
            continue

        # Get row count from SQL Server DMV (faster than COUNT)
        count_query = text("""
            SELECT 
                SUM(ps.row_count) as estimate
            FROM sys.dm_db_partition_stats ps
            INNER JOIN sys.objects o ON ps.object_id = o.object_id
            INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE o.name = :table_name AND s.name = 'dbo'
        """)
        
        try:
            count_result = session.execute(count_query, {"table_name": table})
            row_estimate = count_result.scalar() or 0
        except Exception:
            row_estimate = "N/A"

        # Get 3-row sample for context
        sample_query = text(f"""
            SELECT TOP 3 *
            FROM [dbo].[{table}]
        """)
        
        try:
            sample_result = session.execute(sample_query)
            sample_rows = sample_result.fetchall()
        except Exception as e:
            print(f"Error fetching sample for {table}: {e}")
            sample_rows = []

        col_lines = "\n".join(
            f"  - {c.column_name} ({c.data_type})"
            f"{'  NOT NULL' if c.is_nullable == 'NO' else ''}"
            for c in columns
        )

        context_parts.append(
            f"Table: [dbo].[{table}]\n"
            f"Approx rows: {row_estimate:,}\n"
            f"Columns:\n{col_lines}\n"
            f"Sample (3 rows): {[dict(r._mapping) for r in sample_rows] if sample_rows else 'No data'}\n"
        )

    return "\n\n".join(context_parts)

def get_last_user_message(messages):
    return next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)),
        None
    )