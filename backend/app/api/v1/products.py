from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.websites.models import Website
from app.domains.products.models import (
    Product, ProductVariant, ProductCategory,
    ShoppingCart, CartItem, Order, OrderItem
)
from app.domains.products.schemas import (
    ProductCreateRequest, ProductUpdateRequest, ProductResponse,
    CartItemRequest, ShoppingCartResponse, CartCheckoutRequest,
    OrderResponse, OrderListResponse, ProductCategoryCreateRequest,
    ProductCategoryResponse
)

router = APIRouter()


async def _get_website_for_user(business_id: UUID, user: User, db: AsyncSession) -> Website:
    result = await db.execute(
        select(Website).join(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")
    return website


# ============================================================
# PRODUCTS ENDPOINTS
# ============================================================

@router.post("/businesses/{business_id}/products")
async def create_product(
    business_id: UUID,
    data: ProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new product."""
    website = await _get_website_for_user(business_id, current_user, db)

    product = Product(
        website_id=website.id,
        name=data.name,
        slug=data.slug or data.name.lower().replace(' ', '-'),
        description=data.description,
        short_description=data.short_description,
        price=data.price,
        compare_at_price=data.compare_at_price,
        sku=data.sku,
        barcode=data.barcode,
        weight=data.weight,
        inventory_count=data.inventory_count,
        track_inventory=data.track_inventory,
        featured_image_url=data.featured_image_url,
        images=data.images,
        status=data.status,
        metadata=data.metadata,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return ProductResponse.from_orm(product)


@router.get("/businesses/{business_id}/products/{product_id}")
async def get_product(
    business_id: UUID,
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get product details."""
    website = await _get_website_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.website_id == website.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return ProductResponse.from_orm(product)


@router.get("/businesses/{business_id}/products")
async def list_products(
    business_id: UUID,
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List products."""
    website = await _get_website_for_user(business_id, current_user, db)

    query = select(Product).where(Product.website_id == website.id)
    if status:
        query = query.where(Product.status == status)

    result = await db.execute(query.offset(skip).limit(limit))
    products = result.scalars().all()

    total_result = await db.execute(
        select(func.count(Product.id)).where(Product.website_id == website.id)
    )
    total = total_result.scalar()

    return {
        "products": [ProductResponse.from_orm(p) for p in products],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.put("/businesses/{business_id}/products/{product_id}")
async def update_product(
    business_id: UUID,
    product_id: UUID,
    data: ProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product."""
    website = await _get_website_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.website_id == website.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if data.name:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.short_description is not None:
        product.short_description = data.short_description
    if data.price:
        product.price = data.price
    if data.compare_at_price is not None:
        product.compare_at_price = data.compare_at_price
    if data.inventory_count is not None:
        product.inventory_count = data.inventory_count
    if data.featured_image_url is not None:
        product.featured_image_url = data.featured_image_url
    if data.images is not None:
        product.images = data.images
    if data.status:
        product.status = data.status
    if data.metadata is not None:
        product.metadata = data.metadata

    product.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(product)

    return ProductResponse.from_orm(product)


@router.delete("/businesses/{business_id}/products/{product_id}")
async def delete_product(
    business_id: UUID,
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete product."""
    website = await _get_website_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.website_id == website.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    await db.delete(product)
    await db.commit()

    return {"status": "deleted"}


# ============================================================
# CART ENDPOINTS
# ============================================================

@router.post("/websites/{website_id}/cart/add")
async def add_to_cart(
    website_id: UUID,
    data: CartItemRequest,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add product to cart (public endpoint)."""
    # Get or create cart
    cart_result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.website_id == website_id,
            ShoppingCart.session_id == session_id,
            ShoppingCart.status == 'ACTIVE',
        )
    )
    cart = cart_result.scalar_one_or_none()

    if not cart:
        cart = ShoppingCart(
            website_id=website_id,
            session_id=session_id,
            status='ACTIVE',
        )
        db.add(cart)
        await db.flush()

    # Get product
    product_result = await db.execute(
        select(Product).where(
            Product.id == data.product_id,
            Product.website_id == website_id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Check if item already in cart
    item_result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == data.product_id,
            CartItem.variant_id == data.variant_id,
        )
    )
    item = item_result.scalar_one_or_none()

    if item:
        item.quantity += data.quantity
        item.line_total = item.unit_price * item.quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            quantity=data.quantity,
            unit_price=product.price,
            line_total=product.price * data.quantity,
        )
        db.add(item)

    # Recalculate cart totals
    items_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id)
    )
    items = items_result.scalars().all()

    cart.subtotal = sum(item.line_total for item in items)
    cart.total = cart.subtotal + cart.tax + cart.shipping - cart.discount
    cart.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(cart)

    return ShoppingCartResponse.from_orm(cart)


@router.get("/websites/{website_id}/cart")
async def get_cart(
    website_id: UUID,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get cart (public endpoint)."""
    result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.website_id == website_id,
            ShoppingCart.session_id == session_id,
            ShoppingCart.status == 'ACTIVE',
        )
    )
    cart = result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")

    return ShoppingCartResponse.from_orm(cart)


@router.post("/websites/{website_id}/cart/remove/{item_id}")
async def remove_from_cart(
    website_id: UUID,
    item_id: UUID,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Remove item from cart."""
    result = await db.execute(
        select(CartItem).join(ShoppingCart).where(
            CartItem.id == item_id,
            ShoppingCart.website_id == website_id,
            ShoppingCart.session_id == session_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    cart_id = item.cart_id
    await db.delete(item)

    # Recalculate totals
    cart_result = await db.execute(select(ShoppingCart).where(ShoppingCart.id == cart_id))
    cart = cart_result.scalar_one_or_none()

    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    items = items_result.scalars().all()

    cart.subtotal = sum(item.line_total for item in items)
    cart.total = cart.subtotal + cart.tax + cart.shipping - cart.discount
    cart.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(cart)

    return ShoppingCartResponse.from_orm(cart)


# ============================================================
# ORDER ENDPOINTS
# ============================================================

@router.post("/websites/{website_id}/checkout")
async def checkout(
    website_id: UUID,
    data: CartCheckoutRequest,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Create order from cart."""
    # Get cart
    cart_result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.website_id == website_id,
            ShoppingCart.session_id == session_id,
            ShoppingCart.status == 'ACTIVE',
        )
    )
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=400, detail="Carrito vacío")

    # Generate order number
    order_count_result = await db.execute(
        select(func.count(Order.id)).where(Order.website_id == website_id)
    )
    order_count = order_count_result.scalar() or 0
    order_number = f"ORD-{datetime.utcnow().year}-{order_count + 1:06d}"

    # Create order
    order = Order(
        website_id=website_id,
        order_number=order_number,
        session_id=session_id,
        status='PENDING',
        payment_status='UNPAID',
        subtotal=cart.subtotal,
        tax=cart.tax,
        shipping_cost=cart.shipping,
        discount=cart.discount,
        total=cart.total,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        shipping_address=data.shipping_address,
        billing_address=data.billing_address or data.shipping_address,
        notes=data.notes,
    )
    db.add(order)
    await db.flush()

    # Create order items
    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    cart_items = items_result.scalars().all()

    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            variant_id=cart_item.variant_id,
            product_name=cart_item.product.name,
            product_sku=cart_item.product.sku,
            variant_name=cart_item.variant.name if cart_item.variant else None,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            line_total=cart_item.line_total,
        )
        db.add(order_item)

    # Mark cart as converted
    cart.status = 'CONVERTED'
    cart.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(order)

    return OrderResponse.from_orm(order)


@router.get("/businesses/{business_id}/orders")
async def list_orders(
    business_id: UUID,
    status: str = Query(None),
    payment_status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List orders for business."""
    website = await _get_website_for_user(business_id, current_user, db)

    query = select(Order).where(Order.website_id == website.id)
    if status:
        query = query.where(Order.status == status)
    if payment_status:
        query = query.where(Order.payment_status == payment_status)

    result = await db.execute(query.order_by(Order.created_at.desc()).offset(skip).limit(limit))
    orders = result.scalars().all()

    total_result = await db.execute(
        select(func.count(Order.id)).where(Order.website_id == website.id)
    )
    total = total_result.scalar()

    return OrderListResponse(
        orders=[OrderResponse.from_orm(o) for o in orders],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
    )


@router.get("/businesses/{business_id}/orders/{order_id}")
async def get_order(
    business_id: UUID,
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get order details."""
    website = await _get_website_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.website_id == website.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return OrderResponse.from_orm(order)


@router.put("/businesses/{business_id}/orders/{order_id}")
async def update_order(
    business_id: UUID,
    order_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update order status or payment status."""
    website = await _get_website_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.website_id == website.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if 'status' in data:
        order.status = data['status']
    if 'payment_status' in data:
        order.payment_status = data['payment_status']
        if data['payment_status'] == 'PAID':
            order.paid_at = datetime.utcnow()

    order.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(order)

    return OrderResponse.from_orm(order)
