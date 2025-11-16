import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

# Database
from database import db

app = FastAPI(title="E-Commerce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Helpers
# -----------------------------
class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
    image_url: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None

    class Config:
        from_attributes = True


def serialize_product(doc) -> ProductOut:
    return ProductOut(
        id=str(doc.get("_id")),
        title=doc.get("title", ""),
        description=doc.get("description"),
        price=float(doc.get("price", 0)),
        category=doc.get("category", "General"),
        in_stock=bool(doc.get("in_stock", True)),
        image_url=doc.get("image_url"),
        brand=doc.get("brand"),
        rating=float(doc.get("rating", 0)) if doc.get("rating") is not None else None,
    )


# -----------------------------
# Seed data on startup (if empty)
# -----------------------------
@app.on_event("startup")
def seed_products_if_needed():
    if db is None:
        # Database not configured; raise at runtime when endpoints are called
        return

    try:
        count = db["product"].count_documents({})
        if count == 0:
            sample_products = [
                {
                    "title": "Classic Tee",
                    "description": "Soft cotton tee with a perfect everyday fit.",
                    "price": 19.99,
                    "category": "Apparel",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop",
                    "brand": "BlueWave",
                    "rating": 4.5,
                },
                {
                    "title": "Running Sneakers",
                    "description": "Lightweight shoes designed for comfort and speed.",
                    "price": 59.99,
                    "category": "Footwear",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop",
                    "brand": "SwiftStep",
                    "rating": 4.3,
                },
                {
                    "title": "Wireless Headphones",
                    "description": "Noise-cancelling over-ear headphones with 30h battery.",
                    "price": 129.0,
                    "category": "Electronics",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1518442031670-681f9a19dbcc?q=80&w=1200&auto=format&fit=crop",
                    "brand": "SonicX",
                    "rating": 4.7,
                },
                {
                    "title": "Smart Watch",
                    "description": "Track health, messages, and workouts with ease.",
                    "price": 149.99,
                    "category": "Electronics",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1511732351157-1865efcb7b7b?q=80&w=1200&auto=format&fit=crop",
                    "brand": "PulseOne",
                    "rating": 4.2,
                },
                {
                    "title": "Backpack",
                    "description": "Durable backpack with multiple compartments.",
                    "price": 39.5,
                    "category": "Accessories",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1511174511562-5f7f18b874f8?q=80&w=1200&auto=format&fit=crop",
                    "brand": "TrailPro",
                    "rating": 4.1,
                },
                {
                    "title": "Sunglasses",
                    "description": "UV400 polarized sunglasses with classic style.",
                    "price": 24.99,
                    "category": "Accessories",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=1200&auto=format&fit=crop",
                    "brand": "SunRay",
                    "rating": 4.0,
                },
                {
                    "title": "Water Bottle",
                    "description": "Insulated stainless steel bottle (1L).",
                    "price": 18.0,
                    "category": "Outdoors",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1542736667-069246bdbc74?q=80&w=1200&auto=format&fit=crop",
                    "brand": "HydroFlow",
                    "rating": 4.6,
                },
                {
                    "title": "Desk Lamp",
                    "description": "Adjustable LED lamp with warm and cool modes.",
                    "price": 32.0,
                    "category": "Home",
                    "in_stock": True,
                    "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?q=80&w=1200&auto=format&fit=crop",
                    "brand": "GlowLite",
                    "rating": 4.4,
                },
            ]
            if sample_products:
                db["product"].insert_many(sample_products)
    except Exception:
        # Ignore seed failures to avoid crashing startup
        pass


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/api/products", response_model=List[ProductOut])
def list_products(q: Optional[str] = Query(None, description="Search query")):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {}
    if q:
        # Case-insensitive match on title and category
        filter_query = {
            "$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}},
                {"brand": {"$regex": q, "$options": "i"}},
            ]
        }

    docs = list(db["product"].find(filter_query).sort("title"))
    return [serialize_product(d) for d in docs]


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")

    doc = db["product"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")

    return serialize_product(doc)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
