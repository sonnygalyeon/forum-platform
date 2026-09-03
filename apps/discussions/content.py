from django.core.exceptions import ValidationError


MAX_COMMENT_BLOCKS = 100
MAX_COMMENT_TEXT_LENGTH = 50_000


def validate_comment_content(content):
    if not isinstance(content, list):
        raise ValidationError("Comment content must be a list.")

    if not content:
        raise ValidationError("Comment content cannot be empty.")

    if len(content) > MAX_COMMENT_BLOCKS:
        raise ValidationError("Too many comment blocks.")

    total_length = 0

    for index, block in enumerate(content):
        if not isinstance(block, dict):
            raise ValidationError(f"Block {index} must be an object.")

        block_type = block.get("type")

        if block_type in {"paragraph", "quote"}:
            text = block.get("text")
            if not isinstance(text, str):
                raise ValidationError(f"Block {index} must contain text.")
            total_length += len(text)

        elif block_type == "code":
            code = block.get("code")
            if not isinstance(code, str):
                raise ValidationError(f"Block {index} must contain code.")

            language = block.get("language", "")
            if not isinstance(language, str):
                raise ValidationError(f"Block {index} has invalid language.")

            total_length += len(code)

        else:
            raise ValidationError(
                f"Unsupported comment block type: {block_type}"]
            )

    if total_length > MAX_COMMENT_TEXT_LENGTH:
        raise ValidationError("Comment is too large.")


def extract_comment_text(content):
    result = []

    for block in content:
        if block.get("type") in {"paragraph", "quote"}:
            result.append(block.get("text", ""))
        elif block.get("type") == "code":
            result.append(block.get("code", ""))

    return "\n".join(result).strip()
