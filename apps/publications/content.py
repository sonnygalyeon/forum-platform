from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

MAX_BLOCKS = 500
MAX_TOTAL_TEXT_LENGTH = 500_000


def _validate_embed(block, index):
    url = block.get("url")
    title = block.get("title", "")
    description = block.get("description", "")
    if not isinstance(url, str) or not url.strip():
        raise ValidationError(f"Embed block {index} must contain a URL.")
    if len(url) > 2048:
        raise ValidationError(f"Embed block {index} URL is too long.")
    try:
        URLValidator(schemes=["http", "https"])(url.strip())
    except ValidationError as exc:
        raise ValidationError(f"Embed block {index} must use a valid http/https URL.") from exc
    if not isinstance(title, str) or len(title) > 300:
        raise ValidationError(f"Embed block {index} has invalid title.")
    if not isinstance(description, str) or len(description) > 1000:
        raise ValidationError(f"Embed block {index} has invalid description.")
    return len(url) + len(title) + len(description)


def validate_content_blocks(content):
    if not isinstance(content, list):
        raise ValidationError("Content must be a list of blocks.")
    if not content:
        raise ValidationError("Content must contain at least one block.")
    if len(content) > MAX_BLOCKS:
        raise ValidationError(f"Content cannot contain more than {MAX_BLOCKS} blocks.")
    total_length = 0
    for index, block in enumerate(content):
        if not isinstance(block, dict):
            raise ValidationError(f"Block {index} must be an object.")
        block_type = block.get("type")
        if block_type in {"paragraph", "quote"}:
            text = block.get("text")
            if not isinstance(text, str):
                raise ValidationError(f"{block_type} block {index} must contain text.")
            total_length += len(text)
        elif block_type == "heading":
            text = block.get("text")
            level = block.get("level")
            if not isinstance(text, str):
                raise ValidationError(f"Heading block {index} must contain text.")
            if level not in (1, 2, 3, 4):
                raise ValidationError(f"Heading block {index} must have level 1-4.")
            total_length += len(text)
        elif block_type == "code":
            code = block.get("code")
            language = block.get("language", "")
            if not isinstance(code, str):
                raise ValidationError(f"Code block {index} must contain code.")
            if not isinstance(language, str):
                raise ValidationError(f"Code block {index} has invalid language.")
            total_length += len(code)
        elif block_type in {"image", "video", "attachment"}:
            asset_id = block.get("asset_id")
            try:
                UUID(str(asset_id))
            except (ValueError, TypeError, AttributeError):
                raise ValidationError(f"Media block {index} has invalid asset_id.")
            caption = block.get("caption", "")
            if not isinstance(caption, str):
                raise ValidationError(f"Media block {index} has invalid caption.")
            total_length += len(caption)
        elif block_type == "embed":
            total_length += _validate_embed(block, index)
        else:
            raise ValidationError(f"Unsupported block type '{block_type}' at index {index}.")
    if total_length > MAX_TOTAL_TEXT_LENGTH:
        raise ValidationError("Publication content is too large.")


def extract_plain_text(content):
    parts = []
    for block in content:
        block_type = block.get("type")
        if block_type in {"paragraph", "heading", "quote"}:
            parts.append(block.get("text", ""))
        elif block_type == "code":
            parts.append(block.get("code", ""))
        elif block_type in {"image", "video", "attachment"}:
            parts.append(block.get("caption", ""))
        elif block_type == "embed":
            parts.extend([
                block.get("title", ""),
                block.get("description", ""),
                block.get("url", ""),
            ])
    return "\n".join(part.strip() for part in parts if isinstance(part, str) and part.strip())
