"""
Pagination utilities
"""

from typing import Tuple, Any
from sqlalchemy.orm import Query
from math import ceil


def paginate_query(query: Query, page: int = 1, per_page: int = 20) -> Tuple[Any, dict]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
    
    Returns:
        Tuple of (items, pagination_info)
    """
    # Ensure page is at least 1
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Limit max per_page to 100
    
    # Get total count
    total = query.count()
    
    # Calculate pagination info
    total_pages = ceil(total / per_page) if total > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    # Get items for current page
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    pagination_info = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": page - 1 if has_prev else None,
        "next_page": page + 1 if has_next else None
    }
    
    return items, pagination_info
