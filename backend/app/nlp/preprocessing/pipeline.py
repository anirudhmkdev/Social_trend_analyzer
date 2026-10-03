"""Dataset-level canonical preprocessing pipeline."""

import logging
import uuid
from typing import Any, Dict, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post
from app.nlp.preprocessing.cleaner import (
    PREPROCESSING_VERSION,
    PreprocessedText,
    TextPreprocessor,
)

logger = logging.getLogger(__name__)


def run_dataset_preprocessing(
    db: Session,
    dataset_id: uuid.UUID,
    force_reprocess: bool = False,
) -> Dict[str, Any]:
    """Execute canonical preprocessing for all posts in a dataset.

    - Verifies dataset existence.
    - If already preprocessed and not force_reprocess, returns existing state.
    - Processes posts in memory and performs bulk updates.
    - Marks duplicates deterministically across the dataset.
    - Sets dataset.preprocessing_version = "1.0.0" and status = "preprocessed".
    """
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise ValueError(f"Dataset {dataset_id} not found")

    posts = db.execute(
        select(Post).where(Post.dataset_id == dataset_id).order_by(Post.timestamp.asc())
    ).scalars().all()

    if not posts:
        return {
            "dataset_id": str(dataset_id),
            "posts_processed": 0,
            "duplicates_count": 0,
            "preprocessing_version": PREPROCESSING_VERSION,
            "status": dataset.status,
        }

    # Check if already preprocessed
    first_post = posts[0]
    if (
        not force_reprocess
        and first_post.cleaned_text is not None
        and first_post.sentiment_ready_text is not None
        and dataset.preprocessing_version == PREPROCESSING_VERSION
    ):
        logger.info(
            "Dataset %s is already canonically preprocessed. Reusing representations.",
            dataset_id,
        )
        dup_count = sum(1 for p in posts if p.is_duplicate)
        return {
            "dataset_id": str(dataset_id),
            "posts_processed": len(posts),
            "duplicates_count": dup_count,
            "preprocessing_version": PREPROCESSING_VERSION,
            "status": dataset.status,
            "reused_canonical": True,
        }

    preprocessor = TextPreprocessor(version=PREPROCESSING_VERSION)
    seen_hashes: Set[str] = set()

    total_urls = 0
    total_hashtags = 0
    total_mentions = 0
    duplicate_count = 0

    for post in posts:
        res: PreprocessedText = preprocessor.process(
            post.original_text, seen_hashes=seen_hashes
        )
        post.cleaned_text = res.cleaned_text
        post.sentiment_ready_text = res.sentiment_ready_text
        post.hashtags = res.hashtags
        post.mentions = res.mentions
        post.urls = res.urls
        post.is_duplicate = res.is_duplicate
        post.preprocessing_meta = res.preprocessing_meta

        if res.is_duplicate:
            duplicate_count += 1
        total_urls += len(res.urls)
        total_hashtags += len(res.hashtags)
        total_mentions += len(res.mentions)

    dataset.preprocessing_version = PREPROCESSING_VERSION
    dataset.status = "preprocessed"
    db.commit()

    logger.info(
        "Completed canonical preprocessing for dataset %s: %d posts, %d duplicates, %d hashtags",
        dataset_id,
        len(posts),
        duplicate_count,
        total_hashtags,
    )

    return {
        "dataset_id": str(dataset_id),
        "posts_processed": len(posts),
        "duplicates_count": duplicate_count,
        "total_urls": total_urls,
        "total_hashtags": total_hashtags,
        "total_mentions": total_mentions,
        "preprocessing_version": PREPROCESSING_VERSION,
        "status": dataset.status,
        "reused_canonical": False,
    }
