from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()
DB="items.db"

def init():
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, price REAL)")
    con.commit(); con.close()
init()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(it: Item):
    con=sqlite3.connect(DB); cur=con.cursor()
    cur.execute("INSERT INTO items(name,price) VALUES(?,?)",(it.name,it.price))
    con.commit(); i=cur.lastrowid; con.close()
    return {"id": i, **it.dict()}

@app.get("/items/{id}")
def read_item(id: int):
    con=sqlite3.connect(DB); cur=con.cursor()
    cur.execute("SELECT id,name,price FROM items WHERE id=?",(id,))
    row=cur.fetchone(); con.close()
    if not row: raise HTTPException(404,"Not found")
    return {"id": row[0], "name": row[1], "price": row[2]}

@app.put("/items/{id}")
def update_item(id: int, it: Item):
    con=sqlite3.connect(DB); cur=con.cursor()
    cur.execute("UPDATE items SET name=?, price=? WHERE id=?",(it.name,it.price,id))
    con.commit(); changed=cur.rowcount; con.close()
    if not changed: raise HTTPException(404,"Not found")
    return {"id": id, **it.dict()}

@app.delete("/items/{id}")
def delete_item(id: int):
    con=sqlite3.connect(DB); cur=con.cursor()
    cur.execute("DELETE FROM items WHERE id=?",(id,))
    con.commit(); changed=cur.rowcount; con.close()
    if not changed: raise HTTPException(404,"Not found")
    return {"ok": True}