from config import settings


def bucket_url() -> str:
    return f"s3://{settings.S3_BUCKET}"
