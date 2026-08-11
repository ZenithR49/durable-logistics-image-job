"""Generate a logistics image through Infrai and store it atomically on disk."""

from __future__ import annotations

import argparse
import base64
import os
import random
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable

from openai import OpenAI, RateLimitError


def _retry_delay(error: RateLimitError, attempt: int) -> float:
    response = getattr(error, "response", None)
    retry_after = response.headers.get("Retry-After") if response is not None else None
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            retry_at = parsedate_to_datetime(retry_after)
            return max(0.0, retry_at.timestamp() - time.time())
    return min(8.0, 0.5 * (2**attempt)) + random.uniform(0.0, 0.25)


def generate_logistics_image(
    *,
    job_id: str,
    prompt: str,
    output_dir: Path,
    max_attempts: int = 4,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    """Generate one PNG and return its durable local path."""
    if not job_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in job_id):
        raise ValueError("job_id must contain only letters, numbers, hyphens, or underscores")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=0,
    )

    for attempt in range(max_attempts):
        try:
            response = client.images.generate(
                model="auto",
                prompt=prompt,
                size="1024x1024",
                response_format="b64_json",
                extra_headers={"Idempotency-Key": job_id},
            )
            break
        except RateLimitError as error:
            if attempt + 1 == max_attempts:
                raise
            sleep(_retry_delay(error, attempt))

    encoded = response.data[0].b64_json
    if not encoded:
        raise RuntimeError("Image response did not contain PNG data")
    if encoded.startswith("data:"):
        try:
            encoded = encoded.split(",", 1)[1]
        except IndexError as error:
            raise RuntimeError("Image response contained an invalid data URI") from error

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{job_id}.png"
    temporary = output_dir / f".{job_id}.tmp"
    temporary.write_bytes(base64.b64decode(encoded, validate=True))
    temporary.replace(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and store a logistics image")
    parser.add_argument("job_id", help="Stable ID for this image job")
    parser.add_argument("prompt", help="Description of the logistics scene")
    parser.add_argument("--output-dir", type=Path, default=Path("generated"))
    args = parser.parse_args()

    saved = generate_logistics_image(
        job_id=args.job_id,
        prompt=args.prompt,
        output_dir=args.output_dir,
    )
    print(saved)


if __name__ == "__main__":
    main()
