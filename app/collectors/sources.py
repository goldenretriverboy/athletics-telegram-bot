from pathlib import Path

import yaml

from app.models import SourceConfig


def load_sources(path: str = "config/sources.yaml") -> tuple[list[SourceConfig], list[str]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    sources = [
        SourceConfig(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            url=item["url"],
            priority=int(item.get("priority", 50)),
        )
        for item in data.get("sources", [])
    ]
    return sources, list(data.get("watch_terms", []))

