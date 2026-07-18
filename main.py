# main.py
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlmodel import Session, select, or_

from database.session import get_session, init_db
from models.book import Book, BookCreate, BookUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Generates database tables automatically when application boots up
    init_db()
    yield

# This is the exact variable Uvicorn is looking for!
app = FastAPI(
    title="Bookstore Nganga API",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Create a new book
@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book_in: BookCreate, session: Session = Depends(get_session)):
    existing_isbn = session.exec(select(Book).where(Book.isbn == book_in.isbn)).first()
    if existing_isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A book with this ISBN already exists."
        )
    
    db_book = Book.model_validate(book_in)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book

# 2. List all books (with optional filters)
@app.get("/books", response_model=List[Book])
def list_books(
    author: Optional[str] = None,
    available: Optional[bool] = None,
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    query = select(Book)
    if author:
        query = query.where(Book.author == author)
    if available is not None:
        query = query.where(Book.available == available)
    
    books = session.exec(query.offset(offset).limit(limit)).all()
    return books

# 3. Search books by title or author (Partial match / Case insensitive)
@app.get("/books/search", response_model=List[Book])
def search_books(
    q: str = Query(..., description="Search term for title or author"),
    session: Session = Depends(get_session)
):
    query = select(Book).where(
        or_(
            Book.title.ilike(f"%{q}%"),
            Book.author.ilike(f"%{q}%")
        )
    )
    return session.exec(query).all()

# 4. Get a specific book by ID
@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    db_book = session.get(Book, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return db_book

# 5. Update a book (PATCH handles partial field payloads)
@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book_in: BookUpdate, session: Session = Depends(get_session)):
    db_book = session.get(Book, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    update_data = book_in.model_dump(exclude_unset=True)
    
    if "isbn" in update_data and update_data["isbn"] != db_book.isbn:
        existing_isbn = session.exec(select(Book).where(Book.isbn == update_data["isbn"])).first()
        if existing_isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="A book with this ISBN already exists."
            )

    for key, value in update_data.items():
        setattr(db_book, key, value)
        
    from datetime import datetime, timezone
    db_book.updated_at = datetime.now(timezone.utc)
    
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book

# 6. Delete a book
@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, session: Session = Depends(get_session)):
    db_book = session.get(Book, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    session.delete(db_book)
    session.commit()
    return None