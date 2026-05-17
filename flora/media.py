from typing import Any


def collect_images(value: Any) -> list[str]:
    images: list[str] = []
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return [value]
    if isinstance(value, list):
        for item in value:
            images.extend(collect_images(item))
    if isinstance(value, dict):
        for key, item in value.items():
            if "image" in key.lower() or "photo" in key.lower() or isinstance(item, (dict, list)):
                images.extend(collect_images(item))
    return list(dict.fromkeys(images))
