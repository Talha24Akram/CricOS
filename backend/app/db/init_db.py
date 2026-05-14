from app.db.session import engine
from app.models.base import Base
from app.models import tables  # noqa: F401


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
