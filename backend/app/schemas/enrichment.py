import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel


class EntityResponse(BaseModel):
    id: uuid.UUID
    text: str
    normalized_text: str
    label: str
    frequency: int

    model_config = {"from_attributes": True}


class EntityListResponse(BaseModel):
    entities: List[EntityResponse]
    total_entities: int
    by_type: Dict[str, int]


class KeywordResponse(BaseModel):
    keyword: str
    keyword_type: str
    frequency: int
    tfidf_score: Optional[float] = None
    growth_rate: Optional[float] = None


class KeywordListResponse(BaseModel):
    items: List[KeywordResponse]
    total: int


class HashtagResponse(BaseModel):
    hashtag: str
    frequency: int
    growth_rate: Optional[float] = None


class HashtagListResponse(BaseModel):
    hashtags: List[HashtagResponse]
    total: int
