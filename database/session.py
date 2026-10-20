import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base   # 👈 Base فقط از اینجا میاد

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "shortener.db")   # مسیر مطلق — دیگه مهم نیست از کجا اجرا کنی

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

seesion_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    import database.models          # 👈 تضمین که مدل‌ها قبل از create_all ثبت شدن
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import inspect
    print(f"📁 DB: {DB_PATH}")
    print(f"✅ Tables: {inspect(engine).get_table_names()}")   # وقتی درست شد حذفشون کن