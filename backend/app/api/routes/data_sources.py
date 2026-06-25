from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.data_source import DataSource
from app.models.user import User
from app.schemas.data_source import DataSourceCreate, DataSourceRead, DataSourceUpdate

router = APIRouter(prefix="/data-sources", tags=["data_sources"])
UPLOAD_DIR = Path("storage/uploads")


@router.get("", response_model=list[DataSourceRead])
def list_data_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DataSource]:
    return db.query(DataSource).filter(DataSource.tenant_id == current_user.tenant_id).all()


@router.post("", response_model=DataSourceRead)
def create_data_source(
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSource:
    data_source = DataSource(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.post("/upload", response_model=DataSourceRead)
def upload_data_source(
    name: str,
    source_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSource:
    if source_type not in {"csv", "txt", "excel"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de arquivo invalido")
    tenant_dir = UPLOAD_DIR / str(current_user.tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename).name
    file_path = tenant_dir / safe_filename
    file_path.write_bytes(file.file.read())

    data_source = DataSource(
        tenant_id=current_user.tenant_id,
        name=name,
        source_type=source_type,
        file_path=str(file_path),
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.patch("/{data_source_id}", response_model=DataSourceRead)
def update_data_source(
    data_source_id: int,
    payload: DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSource:
    data_source = (
        db.query(DataSource)
        .filter(DataSource.id == data_source_id, DataSource.tenant_id == current_user.tenant_id)
        .first()
    )
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte nao encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(data_source, key, value)
    db.commit()
    db.refresh(data_source)
    return data_source
