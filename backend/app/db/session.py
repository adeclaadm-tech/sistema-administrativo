from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Neon cierra conexiones ociosas; esto evita el primer 500
    pool_size=5,
    max_overflow=10,
    # `echo` monta su propio handler y duplica cada línea sobre el que ya puso
    # logging.basicConfig. El volcado de SQL se activa desde SQL_ECHO, que sube
    # el nivel del logger y deja que imprima el handler de la raíz, una sola vez.
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
