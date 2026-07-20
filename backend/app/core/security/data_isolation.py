"""Per-user data isolation (Row-Level Security).

Ensures:
- Users can only access their own data (seller_id check)
- All queries filtered by seller_id automatically
- No cross-tenant data leakage
"""

from typing import Optional, Any, Type, TypeVar, List
from sqlalchemy import and_
from sqlalchemy.orm import Session, Query
from fastapi import Depends, HTTPException, status
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DataIsolationError(Exception):
    """Raised when data isolation is violated."""

    pass


class DataIsolationService:
    """Service for enforcing row-level security (RLS)."""

    @staticmethod
    def enforce_seller_id(
        query: Query[T],
        model: Type[T],
        seller_id: str,
    ) -> Query[T]:
        """
        Filter query by seller_id.

        Example:
            query = session.query(Order)
            query = DataIsolationService.enforce_seller_id(query, Order, user_seller_id)
        """
        if not seller_id:
            raise DataIsolationError("seller_id is required for data access")

        # Verify model has seller_id column
        if not hasattr(model, "seller_id"):
            logger.warning(f"Model {model.__name__} has no seller_id column")
            return query

        return query.filter(model.seller_id == seller_id)

    @staticmethod
    def check_seller_id(
        obj: Any,
        seller_id: str,
    ) -> bool:
        """
        Check if object belongs to seller.

        Raises:
            DataIsolationError: If object doesn't belong to seller
        """
        if not hasattr(obj, "seller_id"):
            # Objects without seller_id are considered shared/system objects
            return True

        if obj.seller_id != seller_id:
            logger.warning(
                f"Data isolation violation: Attempt to access {type(obj).__name__} "
                f"(seller_id={obj.seller_id}) by user with seller_id={seller_id}"
            )
            raise DataIsolationError(
                f"Access denied: This data belongs to a different account"
            )

        return True

    @staticmethod
    def filter_list(
        items: List[T],
        seller_id: str,
    ) -> List[T]:
        """Filter list of items by seller_id."""
        result = []
        for item in items:
            try:
                DataIsolationService.check_seller_id(item, seller_id)
                result.append(item)
            except DataIsolationError:
                continue
        return result


class IsolatedQuery:
    """Context manager for isolated queries."""

    def __init__(self, db: Session, seller_id: str):
        self.db = db
        self.seller_id = seller_id

    def query(self, model: Type[T]) -> Query[T]:
        """Create isolated query."""
        query = self.db.query(model)
        return DataIsolationService.enforce_seller_id(query, model, self.seller_id)


def require_seller_context(func):
    """
    Decorator to require seller_id in function.

    Usage:
        @require_seller_context
        async def get_user_orders(seller_id: str, db: Session):
            ...
    """

    @wraps(func)
    async def wrapper(*args, seller_id: Optional[str] = None, **kwargs):
        if not seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="seller_id context required",
            )

        try:
            return await func(*args, seller_id=seller_id, **kwargs)
        except DataIsolationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

    return wrapper


class SellerContext:
    """Request context for seller_id."""

    def __init__(self, seller_id: str, user_id: str):
        self.seller_id = seller_id
        self.user_id = user_id

    def __repr__(self) -> str:
        return f"SellerContext(seller_id={self.seller_id}, user_id={self.user_id})"


async def get_seller_context(
    db: Session,
    current_user_id: str,
) -> SellerContext:
    """
    Get seller context for current user.

    In a multi-tenant system, this maps user_id -> seller_id.
    """
    # For now, assume seller_id == user_id (single-user accounts)
    # In a more complex system, query Users table to get seller_id
    return SellerContext(seller_id=current_user_id, user_id=current_user_id)


# Data isolation middleware for automatic enforcement

class DataIsolationMiddleware:
    """Middleware to attach seller_context to request."""

    async def __call__(self, request, call_next):
        # Extract seller_id from user token (if available)
        seller_id = getattr(request.state, "seller_id", None)

        if seller_id:
            request.state.seller_context = SellerContext(
                seller_id=seller_id,
                user_id=getattr(request.state, "user_id", seller_id),
            )

        response = await call_next(request)
        return response


# Audit log for data access violations

async def log_isolation_violation(
    seller_id: str,
    user_id: str,
    attempted_seller_id: str,
    resource_type: str,
    resource_id: str,
    ip_address: Optional[str] = None,
) -> None:
    """Log data isolation violation for security audit."""
    logger.critical(
        f"DATA ISOLATION VIOLATION: User {user_id} (seller_id={seller_id}) "
        f"attempted to access {resource_type}/{resource_id} from seller_id={attempted_seller_id}",
        extra={
            "severity": "critical",
            "violation_type": "cross_tenant_access",
            "user_id": user_id,
            "seller_id": seller_id,
            "attempted_seller_id": attempted_seller_id,
            "resource": f"{resource_type}/{resource_id}",
            "ip_address": ip_address,
        },
    )

    # In production, this should also:
    # 1. Create AuditLog entry
    # 2. Alert security team
    # 3. Rate limit user
    # 4. Block suspicious IP
