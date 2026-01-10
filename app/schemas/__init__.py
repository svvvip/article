from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field


class ArticleQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)
    keyword: Optional[str] = None
    publish_date_range: Optional[List[date]] = None
    section: Optional[str] = None
    sub_type: Optional[str] = None