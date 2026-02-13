"""Misclassification feedback database model.

This module defines the SQLAlchemy ORM model for misclassification feedback,
which is stored in the 'feedback' schema namespace.
"""

import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from life_organizer.db.base import Base


class MisclassificationFeedback(Base):
    """Misclassification feedback model for tracking correction data.

    Stores user-submitted corrections when the classifier assigns an input
    to the wrong category. This data can be used for training improvements.

    All feedback records are stored in the 'feedback' schema namespace.

    Attributes:
        id: Primary key auto-incremented integer
        original_input: The original user input that was misclassified
        wrong_category: The category incorrectly assigned by the classifier
        correct_category: The correct category as identified by the user
        created_at: Timestamp when the feedback was submitted (auto-generated)
    """

    __tablename__ = "misclassifications"
    __table_args__ = ({"schema": "feedback"},)

    id: Mapped[int] = mapped_column(primary_key=True)
    original_input: Mapped[str] = mapped_column(Text, nullable=False)
    wrong_category: Mapped[str] = mapped_column(String(50), nullable=False)
    correct_category: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<MisclassificationFeedback(id={self.id}, "
            f"wrong_category={self.wrong_category}, "
            f"correct_category={self.correct_category})>"
        )
