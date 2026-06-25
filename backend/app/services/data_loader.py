from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from app.models.data_source import DataSource

DATABASE_SOURCE_TYPES = {"postgresql", "oracle", "sqlserver"}


def load_data_source(data_source: DataSource) -> pd.DataFrame:
    if data_source.source_type in {"csv", "txt"}:
        separator = (data_source.config or {}).get("separator", "," if data_source.source_type == "csv" else "\t")
        return pd.read_csv(Path(data_source.file_path), sep=separator)

    if data_source.source_type == "excel":
        sheet_name = (data_source.config or {}).get("sheet_name", 0)
        return pd.read_excel(Path(data_source.file_path), sheet_name=sheet_name)

    if data_source.source_type in DATABASE_SOURCE_TYPES:
        if not data_source.connection_uri or not data_source.table_name:
            raise ValueError(f"Fonte {data_source.source_type} exige connection_uri e table_name")
        if not _is_safe_table_name(data_source.table_name):
            raise ValueError("table_name invalido")
        engine = create_engine(data_source.connection_uri, pool_pre_ping=True)
        query = text(_limited_select(data_source.source_type, data_source.table_name))
        return pd.read_sql(query, engine)

    raise ValueError(f"Tipo de fonte nao suportado: {data_source.source_type}")


def _is_safe_table_name(table_name: str) -> bool:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.$")
    return bool(table_name) and all(char in allowed for char in table_name)


def _limited_select(source_type: str, table_name: str, limit: int = 10000) -> str:
    quoted = _quote_table_name(source_type, table_name)
    if source_type == "sqlserver":
        return f"SELECT TOP {limit} * FROM {quoted}"
    if source_type == "oracle":
        return f"SELECT * FROM {quoted} FETCH FIRST {limit} ROWS ONLY"
    return f"SELECT * FROM {quoted} LIMIT {limit}"


def _quote_table_name(source_type: str, table_name: str) -> str:
    quote = "[" if source_type == "sqlserver" else '"'
    close_quote = "]" if source_type == "sqlserver" else '"'
    return ".".join(f"{quote}{part}{close_quote}" for part in table_name.split("."))
