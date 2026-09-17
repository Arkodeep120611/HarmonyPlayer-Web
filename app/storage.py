from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def _get_b2_client():
    key_id = os.getenv("B2_KEY_ID")
    application_key = os.getenv("B2_APPLICATION_KEY")
    endpoint = os.getenv("B2_ENDPOINT")

    if not key_id or not application_key or not endpoint:
        raise RuntimeError(
            "B2 storage is not configured. "
            "Set B2_KEY_ID, B2_APPLICATION_KEY, and B2_ENDPOINT."
        )

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=application_key,
        region_name="eu-central-003"
    )


def get_bucket_name() -> str:
    bucket_name = os.getenv("B2_BUCKET_NAME")

    if not bucket_name:
        raise RuntimeError("B2_BUCKET_NAME is not configured.")

    return bucket_name


def upload_file_to_b2(
    file_path: str | Path,
    object_name: str,
    content_type: str | None = None,
) -> None:
    client = _get_b2_client()

    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    try:
        client.upload_file(
            str(file_path),
            get_bucket_name(),
            object_name,
            ExtraArgs=extra_args,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to upload file to B2: {exc}") from exc


def delete_file_from_b2(object_name: str) -> None:
    client = _get_b2_client()

    try:
        client.delete_object(
            Bucket=get_bucket_name(),
            Key=object_name,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to delete file from B2: {exc}") from exc


def generate_download_url(
    object_name: str,
    expires_in: int = 3600,
) -> str:
    client = _get_b2_client()

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": get_bucket_name(),
                "Key": object_name,
            },
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Failed to generate B2 download URL: {exc}"
        ) from exc


def audio_content_type(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    return {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
    }.get(extension, "application/octet-stream")