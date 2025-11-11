"""SQLAlchemy declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):  # type: ignore[misc]
    """Base class for all SQLAlchemy ORM models.

    All database models should inherit from this class to use SQLAlchemy's
    declarative mapping system. This base class provides the foundation for
    defining tables, columns, and relationships in an object-oriented way.

    Example:
        class MyModel(Base):
            __tablename__ = "my_table"
            __table_args__ = {'schema': 'my_schema'}

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    """

    pass
