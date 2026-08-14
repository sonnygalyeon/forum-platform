from uuid import UUID
from django.core.exceptions import ValidationError

MAX_BLOCKS = 500
MAX_TOTAL_TEXT_LENGTH = 500_000

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
    return "\n".join(part.strip() for part in parts if part.strip())
