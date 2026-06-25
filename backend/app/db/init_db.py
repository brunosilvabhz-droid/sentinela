from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.alert import Alert
from app.models.data_source import DataSource
from app.models.tenant import Tenant
from app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Tenant).count() == 0:
            tenant = Tenant(name="Demo Corp", document="00000000000100", plan="free", max_alerts=5)
            db.add(tenant)
            db.flush()
            user = User(
                tenant_id=tenant.id,
                name="Admin Demo",
                email="admin@demo.com",
                hashed_password=hash_password("admin1234"),
                role="admin",
            )
            db.add(user)
            upload_dir = "storage/uploads/1"
            import os

            os.makedirs(upload_dir, exist_ok=True)
            csv_path = f"{upload_dir}/pedidos.csv"
            with open(csv_path, "w", encoding="utf-8") as file:
                file.write("pedido_id,cliente,valor_total,status\n")
                file.write("1,Acme,850,ok\n")
                file.write("2,Globex,1250,atencao\n")
                file.write("3,Umbrella,2300,critico\n")

            source = DataSource(
                tenant_id=tenant.id,
                name="Pedidos Demo",
                source_type="csv",
                file_path=csv_path,
                config={"separator": ","},
            )
            db.add(source)
            db.flush()

            alert = Alert(
                tenant_id=tenant.id,
                data_source_id=source.id,
                name="Pedidos acima de 1000",
                column_name="valor_total",
                condition=">",
                threshold_value="1000",
                frequency="15m",
                recipients=["financeiro@demo.com"],
                channels=["email"],
            )
            db.add(alert)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
