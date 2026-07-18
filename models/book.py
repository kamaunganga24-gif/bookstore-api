# models/book.py
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import field_validator

# 1. Base properties shared by all schemas
class BookBase(SQLModel):
    title: str = Field(index=True)
    author: str = Field(index=True)
    isbn: str = Field(unique=True, index=True)
    published_year: int = Field(index=True)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    available: bool = Field(default=True)

    @field_validator("published_year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        current_year = datetime.now(timezone.utc).year
        if not (1000 <= v <= current_year):
            raise ValueError(f"Year must be between 1000 and {current_year}")
        return v

# 2. Schema for creating a book
class BookCreate(BookBase):
    pass

# 3. Schema for updating a book (All fields optional for PATCH)
class BookUpdate(SQLModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    available: Optional[bool] = None

    @field_validator("published_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            current_year = datetime.now(timezone.utc).year
            if not (1000 <= v <= current_year):
                raise ValueError(f"Year must be between 1000 and {current_year}")
        return v

# 4. Main Table Model stored in the database
class Book(BookBase, table=True):
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )