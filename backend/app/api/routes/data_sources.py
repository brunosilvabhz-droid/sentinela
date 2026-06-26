from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_super_admin
from app.db.session import get_db
from app.models.collector import IngestedAttribute, IngestedRecord
from app.models.data_source import DataSource
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.data_source import DataSourceAttributeRead, DataSourceCreate, DataSourcePreview, DataSourceRead, DataSourceUpdate
from app.services.data_loader import load_data_source
from app.services.tenant_limits import assert_can_create_data_source

router = APIRouter(prefix="/data-sources", tags=["data_sources"])
UPLOAD_DIR = Path("storage/uploads")
DATABASE_SOURCE_TYPES = {"postgresql", "oracle", "sqlserver"}


@router.get("", response_model=list[DataSourceRead])
def list_data_sources(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[DataSource]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    return db.query(DataSource).filter(DataSource.tenant_id == target_tenant_id).all()


@router.get("/{data_source_id}/preview", response_model=DataSourcePreview)
def preview_data_source(
    data_source_id: int,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> DataSourcePreview:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id, DataSource.tenant_id == target_tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    if data_source.source_type == "managed":
        records = (
            db.query(IngestedRecord.payload)
            .filter(IngestedRecord.tenant_id == target_tenant_id, IngestedRecord.data_source_id == data_source.id)
            .order_by(IngestedRecord.ingested_at.desc())
            .limit(20)
            .all()
        )
        rows = [record[0] for record in records]
        columns = sorted({key for row in rows for key in row.keys()})
        return DataSourcePreview(columns=columns, rows=rows, total_preview_rows=len(rows))

    dataframe = load_data_source(data_source)
    preview = dataframe.head(20)
    return DataSourcePreview(
        columns=[str(column) for column in dataframe.columns],
        rows=preview.where(preview.notnull(), None).to_dict(orient="records"),
        total_preview_rows=len(preview),
    )


@router.get("/{data_source_id}/attributes", response_model=list[DataSourceAttributeRead])
def list_data_source_attributes(
    data_source_id: int,
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[dict]:
    target_tenant_id = resolve_tenant_id(current_user, tenant_id)
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id, DataSource.tenant_id == target_tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")

    attributes = (
        db.query(IngestedAttribute.attribute_name, IngestedAttribute.attribute_type)
        .filter(IngestedAttribute.tenant_id == target_tenant_id, IngestedAttribute.data_source_id == data_source_id)
        .group_by(IngestedAttribute.attribute_name, IngestedAttribute.attribute_type)
        .order_by(IngestedAttribute.attribute_name)
        .all()
    )
    if attributes:
        return [
            {
                "name": name,
                "type": attribute_type,
                "sample_values": _sample_attribute_values(db, target_tenant_id, data_source_id, name),
            }
            for name, attribute_type in attributes
        ]

    preview = preview_data_source(data_source_id, tenant_id, db, current_user)
    return [
        {
            "name": column,
            "type": None,
            "sample_values": [str(row.get(column)) if row.get(column) is not None else None for row in preview.rows[:5]],
        }
        for column in preview.columns
    ]


@router.post("", response_model=DataSourceRead)
def create_data_source(
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> DataSource:
    if payload.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para criar fonte")
    tenant = get_active_tenant(db, payload.tenant_id)
    assert_can_create_data_source(db, tenant)
    if payload.source_type not in DATABASE_SOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de fonte invalido para conexao")
    if not payload.connection_uri or not payload.table_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="connection_uri e table_name sao obrigatorios")
    data = payload.model_dump(exclude={"tenant_id"})
    data_source = DataSource(tenant_id=tenant.id, **data)
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.post("/upload", response_model=DataSourceRead)
def upload_data_source(
    name: str,
    source_type: str,
    tenant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> DataSource:
    tenant = get_active_tenant(db, tenant_id)
    assert_can_create_data_source(db, tenant)
    if source_type not in {"csv", "txt", "excel"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de arquivo invalido")
    tenant_dir = UPLOAD_DIR / str(tenant.id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename).name
    file_path = tenant_dir / safe_filename
    file_path.write_bytes(file.file.read())

    data_source = DataSource(
        tenant_id=tenant.id,
        name=name,
        source_type=source_type,
        file_path=str(file_path),
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.delete("/{data_source_id}", response_model=DataSourceRead)
def delete_data_source(
    data_source_id: int,
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> DataSource:
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id, DataSource.tenant_id == tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    data_source.is_active = False
    db.commit()
    db.refresh(data_source)
    return data_source


@router.patch("/{data_source_id}", response_model=DataSourceRead)
def update_data_source(
    data_source_id: int,
    payload: DataSourceUpdate,
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
) -> DataSource:
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id, DataSource.tenant_id == tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(data_source, key, value)
    db.commit()
    db.refresh(data_source)
    return data_source


def resolve_tenant_id(current_user: User, tenant_id: int | None) -> int:
    if current_user.role == "super_admin":
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id e obrigatorio para admin geral")
        return tenant_id
    return current_user.tenant_id


def get_active_tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active.is_(True)).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa nao encontrada")
    return tenant


def _sample_attribute_values(db: Session, tenant_id: int, data_source_id: int, attribute_name: str) -> list[str | None]:
    rows = (
        db.query(IngestedAttribute.attribute_value)
        .filter(
            IngestedAttribute.tenant_id == tenant_id,
            IngestedAttribute.data_source_id == data_source_id,
            IngestedAttribute.attribute_name == attribute_name,
        )
        .order_by(IngestedAttribute.ingested_at.desc())
        .limit(5)
        .all()
    )
    return [row[0] for row in rows]
