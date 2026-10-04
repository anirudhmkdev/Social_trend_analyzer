"""
Synthetic demonstration dataset generator.

Generates a deterministic 900-row CSV with:
- 5 meaningful themes (climate, AI, crypto, health, sports)
- 3 platforms (twitter, reddit, instagram)
- 21-day time range
- Varied sentiment (positive/neutral/negative per theme)
- Rising trend: AI
- Declining trend: Crypto
- Stable topic: Sports
- Emerging topic: Health (new spike in last 3 days)
- 1 Background/stable topic: Climate
- Named entities, hashtags, keywords
- Realistic engagement distribution

All timestamps are UTC. Source type: synthetic_demo.
"""

from __future__ import annotations

import csv
import io
import random
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

SEED = 42
random.seed(SEED)

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEMES = {
    "climate": {
        "hashtags": ["climatechange", "globalwarming", "greenenergy", "netzero", "carbonneutral"],
        "entities": ["UN Climate Summit", "IPCC", "Greta Thunberg", "Paris Agreement", "EPA"],
        "keywords": ["emissions", "carbon", "renewable", "fossil fuels", "sustainability"],
        "templates": [
            "New study shows {keyword} impact worsening. #climatechange #greenenergy",
            "{entity} releases report on {keyword} targets. #netzero",
            "Countries must act on {keyword} or face irreversible damage. #climatechange",
            "Renewable energy investments hit record high amid {keyword} concerns. #greenenergy",
            "{entity} summit discusses {keyword} commitments. #climatechange",
            "Scientists warn of {keyword} tipping points. #globalwarming #netzero",
        ],
        "sentiment": "mixed",
        "base_volume_pattern": "stable",
    },
    "ai": {
        "hashtags": ["artificialintelligence", "machinelearning", "chatgpt", "llm", "aitech"],
        "entities": ["OpenAI", "Google DeepMind", "Microsoft", "Meta AI", "Anthropic"],
        "keywords": [  # noqa: E501
            "large language model",
            "neural network",
            "generative AI",
            "automation",
            "deep learning",
        ],
        "templates": [
            "{entity} launches new {keyword} model. #artificialintelligence #llm",
            "How {keyword} is reshaping industry. #aitech #machinelearning",
            "{entity} raises funding for {keyword} research. #artificialintelligence",
            "Debate: will {keyword} replace jobs? #aitech #llm",
            "{entity} open-sources {keyword} framework. #machinelearning #aitech",
            "Breakthrough in {keyword} achieves human-level performance. #artificialintelligence",
            "Researchers at {entity} publish {keyword} paper. #machinelearning",
        ],
        "sentiment": "positive",
        "base_volume_pattern": "rising",
    },
    "crypto": {
        "hashtags": ["bitcoin", "ethereum", "crypto", "blockchain", "defi"],
        "entities": ["Bitcoin", "Ethereum", "Binance", "SEC", "Coinbase"],
        "keywords": ["cryptocurrency", "blockchain", "defi", "NFT", "market crash"],
        "templates": [
            "{entity} price drops amid regulatory concerns. #crypto #bitcoin",
            "{entity} faces {keyword} scrutiny. #blockchain",
            "Investors flee {keyword} market. #crypto #defi",
            "{entity} halts withdrawals — {keyword} crisis deepens. #crypto",
            "Experts warn of {keyword} bubble. #bitcoin #ethereum",
            "{entity} regulatory action impacts {keyword}. #crypto",
        ],
        "sentiment": "negative",
        "base_volume_pattern": "declining",
    },
    "health": {
        "hashtags": ["mentalhealth", "wellness", "healthcare", "publichealth", "nutrition"],
        "entities": ["WHO", "CDC", "NIH", "Mayo Clinic", "NHS"],
        "keywords": ["mental health", "wellness", "vaccine", "pandemic", "healthcare system"],
        "templates": [
            "{entity} releases guidelines on {keyword}. #mentalhealth #publichealth",
            "New research on {keyword} and its impact. #wellness #healthcare",
            "{entity} warns of {keyword} crisis. #publichealth",
            "Access to {keyword} services remains unequal. #healthcare",
            "Study links {keyword} to lifestyle factors. #wellness #nutrition",
            "{entity} approves new {keyword} treatment. #healthcare",
            "Advocates call for better {keyword} funding. #mentalhealth",
        ],
        "sentiment": "positive",
        "base_volume_pattern": "emerging",
    },
    "sports": {
        "hashtags": ["football", "nba", "worldcup", "tennis", "olympics"],
        "entities": ["FIFA", "NBA", "Wimbledon", "IOC", "UEFA"],
        "keywords": [
            "championship",
            "tournament",
            "player transfer",
            "season opener",
            "world record",
        ],
        "templates": [
            "{entity} announces {keyword} schedule. #football #sports",
            "Highlights from the {keyword} last night. #nba #sports",
            "{entity} faces controversy over {keyword}. #worldcup",
            "Record-breaking performance at {keyword}. #olympics",
            "Fans react to {keyword} decision. #football #sports",
            "{entity} confirms {keyword} lineup. #sports",
        ],
        "sentiment": "positive",
        "base_volume_pattern": "stable",
    },
}

PLATFORMS = ["twitter", "reddit", "instagram"]
PLATFORM_WEIGHTS = [0.45, 0.35, 0.20]

# ---------------------------------------------------------------------------
# Volume pattern generators (number of posts per day for 21 days)
# ---------------------------------------------------------------------------


def _stable_pattern(base: int) -> List[int]:
    """Returns ~stable daily volumes with small noise."""
    rng = random.Random(SEED)
    return [max(1, base + rng.randint(-base // 5, base // 5)) for _ in range(21)]


def _rising_pattern(base: int) -> List[int]:
    """Returns steadily rising daily volumes."""
    rng = random.Random(SEED + 1)
    vols = []
    for day in range(21):
        multiplier = 1.0 + (day / 21) * 2.0  # rises to 3× base
        vols.append(max(1, int(base * multiplier + rng.randint(-2, 4))))
    return vols


def _declining_pattern(base: int) -> List[int]:
    """Returns declining daily volumes."""
    rng = random.Random(SEED + 2)
    vols = []
    for day in range(21):
        multiplier = max(0.1, 1.5 - (day / 21) * 1.3)
        vols.append(max(1, int(base * multiplier + rng.randint(-1, 2))))
    return vols


def _emerging_pattern(base: int) -> List[int]:
    """Returns near-zero until last 4 days then spikes sharply."""
    rng = random.Random(SEED + 3)
    vols = []
    for day in range(21):
        if day < 17:
            vols.append(max(0, rng.randint(0, 2)))
        else:
            spike_day = day - 16
            vols.append(max(1, base + spike_day * 6 + rng.randint(0, 5)))
    return vols


PATTERN_GENERATORS = {
    "stable": lambda: _stable_pattern(18),
    "rising": lambda: _rising_pattern(8),
    "declining": lambda: _declining_pattern(22),
    "emerging": lambda: _emerging_pattern(5),
}

# ---------------------------------------------------------------------------
# Engagement distribution by platform
# ---------------------------------------------------------------------------


def _gen_engagement(platform: str, rng: random.Random) -> Tuple[int, int, int]:
    """Generate realistic likes, comments, shares for a post."""
    if platform == "twitter":
        likes = rng.randint(0, 500)
        comments = rng.randint(0, 60)
        shares = rng.randint(0, 200)
    elif platform == "reddit":
        likes = rng.randint(0, 2000)  # upvotes
        comments = rng.randint(0, 300)
        shares = rng.randint(0, 20)
    else:  # instagram
        likes = rng.randint(10, 5000)
        comments = rng.randint(0, 100)
        shares = rng.randint(0, 50)
    return likes, comments, shares


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------


def _make_post_text(theme_name: str, rng: random.Random) -> str:
    theme = THEMES[theme_name]
    template = rng.choice(theme["templates"])
    keyword = rng.choice(theme["keywords"])
    entity = rng.choice(theme["entities"])
    return template.format(keyword=keyword, entity=entity)


def _make_author_id(rng: random.Random) -> str:
    return f"user_{rng.randint(1000, 9999)}"


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_sample_dataset(seed: int = SEED) -> str:
    """
    Generate a deterministic synthetic demonstration dataset as CSV string.

    Returns CSV text content (UTF-8).
    """
    rng = random.Random(seed)
    start_date = datetime(2026, 9, 1, tzinfo=timezone.utc)

    rows: List[dict] = []
    post_id = 1

    # Scale all theme/day allocations together, preserving the intended trajectories.
    allocations = [
        (theme_key, day, volume)
        for theme_key, spec in THEMES.items()
        for day, volume in enumerate(PATTERN_GENERATORS[str(spec["base_volume_pattern"])]())
    ]
    total = sum(volume for _, _, volume in allocations)
    scaled = [volume * 900 / total for _, _, volume in allocations]
    counts = [int(value) for value in scaled]
    remainder = 900 - sum(counts)
    order = sorted(range(len(counts)), key=lambda index: (-(scaled[index] - counts[index]), index))
    for index in order[:remainder]:
        counts[index] += 1
    volumes_by_theme = {theme: [0] * 21 for theme in THEMES}
    for (allocation_theme, day, _), volume in zip(allocations, counts):
        volumes_by_theme[allocation_theme][day] = volume

    for theme_name, theme in THEMES.items():
        daily_volumes = volumes_by_theme[theme_name]

        for day_offset, volume in enumerate(daily_volumes):
            day_start = start_date + timedelta(days=day_offset)

            for _ in range(volume):
                # Random hour within the day
                hour = rng.randint(0, 23)
                minute = rng.randint(0, 59)
                second = rng.randint(0, 59)
                ts = day_start + timedelta(hours=hour, minutes=minute, seconds=second)

                platform = rng.choices(PLATFORMS, weights=PLATFORM_WEIGHTS, k=1)[0]
                text = _make_post_text(theme_name, rng)
                likes, comments, shares = _gen_engagement(platform, rng)
                author_id = _make_author_id(rng)

                # Extract hashtags from text
                import re

                hashtags = ",".join(re.findall(r"#(\w+)", text))

                rows.append(
                    {
                        "id": f"post_{post_id:06d}",
                        "text": text,
                        "created_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "platform": platform,
                        "hashtags": hashtags,
                        "likes": likes,
                        "comments": comments,
                        "shares": shares,
                        "author_id": author_id,
                        "theme": theme_name,  # Extra column for reference
                        "source_type": "synthetic_demo",
                    }
                )
                post_id += 1

    # Shuffle to mix themes
    rng.shuffle(rows)

    # Write CSV
    output = io.StringIO()
    fieldnames = [
        "id",
        "text",
        "created_at",
        "platform",
        "hashtags",
        "likes",
        "comments",
        "shares",
        "author_id",
        "theme",
        "source_type",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()


if __name__ == "__main__":
    import sys

    csv_content = generate_sample_dataset()
    row_count = csv_content.count("\n") - 1  # subtract header
    print(f"Generated {row_count} rows", file=sys.stderr)
    sys.stdout.write(csv_content)
