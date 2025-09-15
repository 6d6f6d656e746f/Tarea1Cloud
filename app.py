import os, sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

DB_DIR = "/var/lib/app"
DB_PATH = os.path.join(DB_DIR, "app.db")
os.makedirs(DB_DIR, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

app = FastAPI()

class ItemIn(BaseModel):
    title: str
    description: Optional[str] = None

class Item(ItemIn):
    id: int

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/items", response_model=List[Item])
def list_items():
    conn = get_conn()
    items = [dict(row) for row in conn.execute("SELECT id, title, description FROM items")]
    conn.close()
    return items

@app.post("/items", response_model=Item, status_code=201)
def create_item(item: ItemIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO items (title, description) VALUES (?, ?)", (item.title, item.description))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **item.dict()}

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    conn = get_conn()
    row = conn.execute("SELECT id, title, description FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE items SET title = ?, description = ? WHERE id = ?", (item.title, item.description, item_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Not found")
    conn.commit()
    conn.close()
    return {"id": item_id, **item.dict()}

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Not found")
    conn.commit()
    conn.close()
    return

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
