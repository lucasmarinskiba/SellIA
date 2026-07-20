"""
E-commerce API — Catálogo, carrito, órdenes, pagos para vendedor de bienes/servicios.

Endpoints:
- Catálogo: GET /products, GET /products/:id, POST /products (admin)
- Carrito: GET /cart, POST /cart/add, DELETE /cart/:item_id, PATCH /cart/:item_id
- Órdenes: POST /checkout, GET /orders/:id, GET /orders (history)
- Pagos: webhook para Stripe/PayPal confirmación

P1: TODOS los datos persisten en PostgreSQL real via SQLAlchemy ORM.
Ver: backend/app/core/database/payment_models.py
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.core.database.payment_models import Product as ProductModel, Order as OrderModel
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/ecommerce", tags=["ecommerce"])
logger = logging.getLogger(__name__)


class Product(BaseModel):
    """Producto en catálogo."""
    id: Optional[str] = None
    name: str
    description: str
    price_usd: float
    stock_qty: int
    sku: str
    category: str
    images: List[str] = []
    tags: List[str] = []


class CartItem(BaseModel):
    """Item en carrito."""
    product_id: str
    qty: int
    price_snapshot: float


class OrderRequest(BaseModel):
    """Request para crear orden."""
    items: List[CartItem]
    payment_method: str
    discount_pct: float = 0.0


@router.get("/products", tags=["catalog"])
async def list_products(category: Optional[str] = None, tag: Optional[str] = None, limit: int = 50):
    """Lista productos con filtros opcionales desde DB."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(ProductModel)

            if category:
                stmt = stmt.where(ProductModel.category == category)

            result = await db.execute(stmt)
            products = result.scalars().all()

            # Filtrar por tag en memoria (JSON query)
            if tag:
                products = [p for p in products if tag in (p.tags or [])]

            products_list = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price_usd": p.price_usd,
                    "stock_qty": p.stock_qty,
                    "sku": p.sku,
                    "category": p.category,
                    "images": p.images or [],
                    "tags": p.tags or [],
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in products[:limit]
            ]

            return {
                "total": len(products),
                "products": products_list
            }
    except Exception as e:
        logger.error(f"Error listando productos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", tags=["catalog"])
async def get_product(product_id: str):
    """Detalle de producto."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(ProductModel).where(ProductModel.id == product_id)
            result = await db.execute(stmt)
            product = result.scalars().first()

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price_usd": product.price_usd,
                "stock_qty": product.stock_qty,
                "sku": product.sku,
                "category": product.category,
                "images": product.images or [],
                "tags": product.tags or [],
                "created_at": product.created_at.isoformat() if product.created_at else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo producto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products", tags=["catalog"])
async def create_product(product: Product):
    """Admin: crear producto."""
    try:
        if product.price_usd <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")

        if not product.id:
            product.id = str(uuid.uuid4())

        async with AsyncSessionLocal() as db:
            db_product = ProductModel(
                id=product.id,
                name=product.name,
                description=product.description,
                price_usd=product.price_usd,
                stock_qty=product.stock_qty,
                sku=product.sku,
                category=product.category,
                images=product.images,
                tags=product.tags,
            )
            db.add(db_product)
            await db.commit()

            logger.info(f"Producto creado: {product.id} - {product.name}")

            return {
                "status": "created",
                "product_id": product.id,
                "name": product.name,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando producto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout", tags=["orders"])
async def checkout(order_req: OrderRequest, user_id: str):
    """Crear orden desde carrito. Inicia proceso de pago."""
    try:
        if not order_req.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Validar stock antes de crear orden
        async with AsyncSessionLocal() as db:
            for item in order_req.items:
                stmt = select(ProductModel).where(ProductModel.id == item.product_id)
                result = await db.execute(stmt)
                product = result.scalars().first()

                if not product:
                    raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

                if product.stock_qty < item.qty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock: {product.name}"
                    )

            # Calcular totales
            subtotal = sum(item.qty * item.price_snapshot for item in order_req.items)
            discount_amount = subtotal * (order_req.discount_pct / 100)
            total = subtotal - discount_amount

            # Crear orden
            order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            db_order = OrderModel(
                id=order_id,
                customer_email="",  # TODO: Obtener de context
                customer_name=user_id,
                product_id="",
                product_name="",
                product_price=0,
                amount=total,
                currency="USD",
                status="pending",
                payment_status="pending",
                stripe_session_id="",
                delivery_type="physical",
                source="ecommerce_api",
            )
            db.add(db_order)

            # Reducir stock
            for item in order_req.items:
                stmt = select(ProductModel).where(ProductModel.id == item.product_id)
                result = await db.execute(stmt)
                product = result.scalars().first()
                product.stock_qty -= item.qty

            await db.commit()

            logger.info(f"[{user_id}] Orden creada: {order_id}, total ${total}")

            return {
                "status": "order_created",
                "order_id": order_id,
                "total": total,
                "payment_method": order_req.payment_method,
                "next": "Integration with Stripe checkout"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{user_id}", tags=["orders"])
async def get_orders(user_id: str):
    """Historial de órdenes del usuario."""
    try:
        async with AsyncSessionLocal() as db:
            # TODO: Buscar órdenes donde customer_name = user_id
            stmt = select(OrderModel).where(OrderModel.customer_name == user_id)
            result = await db.execute(stmt)
            orders = result.scalars().all()

            return {
                "total": len(orders),
                "orders": [
                    {
                        "id": o.id,
                        "status": o.status,
                        "amount": o.amount,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                    for o in orders
                ]
            }
    except Exception as e:
        logger.error(f"Error obteniendo órdenes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/details", tags=["orders"])
async def get_order_details(order_id: str):
    """Detalles de una orden."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(OrderModel).where(OrderModel.id == order_id)
            result = await db.execute(stmt)
            order = result.scalars().first()

            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            return {
                "order": {
                    "id": order.id,
                    "status": order.status,
                    "amount": order.amount,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                },
                "invoice_url": f"/invoices/{order_id}.pdf",
                "tracking": {"status": "pending", "eta": None}
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo orden: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
