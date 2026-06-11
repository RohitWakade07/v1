import logging
from typing import Optional

from aiobotocore.session import get_session
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.endpoint_url = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_SUBMISSIONS
        self.bucket_submissions = settings.MINIO_BUCKET_SUBMISSIONS
        self.use_ssl = settings.MINIO_USE_SSL
        self.region_name = getattr(settings, "MINIO_REGION", "us-east-1")
        self.config = Config(signature_version="s3v4")

    async def _create_client(self):
        session = get_session()
        return session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=self.config,
            use_ssl=self.use_ssl,
        )

    async def ensure_bucket(self) -> None:
        async with await self._create_client() as client:
            buckets = await client.list_buckets()
            names = [bucket["Name"] for bucket in buckets.get("Buckets", [])]
            if self.bucket_name not in names:
                logger.info("Creating MinIO bucket %s", self.bucket_name)
                await client.create_bucket(Bucket=self.bucket_name)

    async def upload_submission_zip(self, key: str, contents: bytes) -> str:
        async with await self._create_client() as client:
            await self.ensure_bucket()
            await client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=contents,
                ContentType="application/zip",
            )
        return key

    async def get_object_url(self, key: str, expires: int = 3600) -> Optional[str]:
        async with await self._create_client() as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires,
            )

    async def download_file(self, bucket: str, key: str, local_path: str) -> None:
        async with await self._create_client() as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            with open(local_path, 'wb') as f:
                async for chunk in response['Body']:
                    f.write(chunk)
