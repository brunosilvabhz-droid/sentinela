from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from app.models.data_source import DataSource


def load_data_source(data_source: DataSource) -> pd.DataFrame:
    if data_source.source_type in {"csv", "txt"}:
        separator = (data_source.config or {}).get("separator", "," if data_source.source_type == "csv" else "\t")
        return pd.read_csv(Path(data_source.file_path), sep=separator)

    if data_source.source_type == "excel":
        sheet_name = (data_source.config or {}).get("sheet_name", 0)
        return pd.read_excel(Path(data_source.file_path), sheet_name=sheet_name)

    if data_source.source_type == "postgresql":
        if not data_source.connection_uri or not data_source.table_name:
            raise ValueError("Fonte PostgreSQL exige connection_uri e table_name")
        if not data_source.table_name.replace("_", "").isalnum():
            raise ValueError("table_name invalido")
        engine = create_engine(data_source.connection_uri, pool_pre_ping=True)
        query = text(f'SELECT * FROM "{data_source.table_name}" LIMIT 10000')
        return pd.read_sql(query, engine)

    raise ValueError(f"Tipo de fonte nao suportado: {data_source.source_type}")
