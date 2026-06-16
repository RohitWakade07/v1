import logging
from typing import Optional

from aiobotocore.session import get_session
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.endpoint_url = settings.MINIO_ENDPOINT.strip() if settings.MINIO_ENDPOINT else None
        self.access_key = settings.MINIO_ACCESS_KEY.strip() if settings.MINIO_ACCESS_KEY else ""
        self.secret_key = settings.MINIO_SECRET_KEY.strip() if settings.MINIO_SECRET_KEY else ""
        self.bucket_name = settings.MINIO_BUCKET_SUBMISSIONS.strip() if settings.MINIO_BUCKET_SUBMISSIONS else ""
        self.bucket_submissions = settings.MINIO_BUCKET_SUBMISSIONS.strip() if settings.MINIO_BUCKET_SUBMISSIONS else ""
        self.use_ssl = settings.MINIO_USE_SSL
        self.region_name = getattr(settings, "MINIO_REGION", "us-east-1")

        if self.endpoint_url:
            # Force SSL for known cloud S3 providers regardless of default config
            if "backblazeb2.com" in self.endpoint_url or "amazonaws.com" in self.endpoint_url or "r2.cloudflarestorage.com" in self.endpoint_url:
                self.use_ssl = True

            # Sync SSL setting with URL scheme
            if self.endpoint_url.startswith("https://"):
                self.use_ssl = True
            elif self.endpoint_url.startswith("http://") and self.use_ssl:
                self.endpoint_url = self.endpoint_url.replace("http://", "https://", 1)
            elif not self.endpoint_url.startswith("http"):
                scheme = "https://" if self.use_ssl else "http://"
                self.endpoint_url = f"{scheme}{self.endpoint_url}"

            # Auto-detect region for Backblaze B2 if user forgot to set MINIO_REGION
            if "backblazeb2.com" in self.endpoint_url and self.region_name == "us-east-1":
                import re
                match = re.search(r's3\.([^.]+)\.backblazeb2\.com', self.endpoint_url)
                if match:
                    self.region_name = match.group(1)

            # Strip trailing slash from endpoint to avoid signature mismatch
            self.endpoint_url = self.endpoint_url.rstrip("/")

        # Backblaze B2 Application Keys restricted to a single bucket REQUIRE
        # virtual-hosted style addressing. Because B2 is a custom endpoint,
        # boto3 defaults to path-style unless explicitly forced to virtual.
        self.config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"}
        )

    async def _create_client(self):
        session = get_session()
        return session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=self.config,
            use_ssl=True if not self.endpoint_url else self.use_ssl,
        )

    async def ensure_bucket(self) -> None:
        import botocore.exceptions
        async with await self._create_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except botocore.exceptions.ClientError as e:
                error_code = str(e.response.get("Error", {}).get("Code", ""))
                # 404 means it definitely doesn't exist, so try creating it
                if error_code == "404" or error_code == "NoSuchBucket":
                    logger.info("Creating bucket %s", self.bucket_name)
                    try:
                        await client.create_bucket(Bucket=self.bucket_name)
                    except Exception as create_err:
                        logger.warning("Failed to create bucket %s: %s", self.bucket_name, create_err)
                else:
                    # 403 Forbidden or SignatureDoesNotMatch typically happens with
                    # bucket-restricted Application Keys in Backblaze B2/MinIO.
                    # We assume the bucket already exists and proceed.
                    logger.info(
                        "Bucket check returned %s for %s. Assuming bucket exists and proceeding.",
                        error_code, self.bucket_name
                    )
            except Exception as e:
                logger.warning("Unexpected error checking bucket %s: %s. Assuming it exists.", self.bucket_name, e)

    async def upload_submission_zip(self, key: str, contents: bytes) -> str:
        import sys
        async with await self._create_client() as client:
            await self.ensure_bucket()

            debug_msg = (
                f"\n=== S3 DEBUG INFO ===\n"
                f"Endpoint: {self.endpoint_url}\n"
                f"Region: {self.region_name}\n"
                f"Bucket: {self.bucket_name}\n"
                f"Access Key ID length: {len(str(self.access_key)) if self.access_key else 0}\n"
                f"Access Key ID prefix: {str(self.access_key)[:8] if self.access_key else 'None'}\n"
                f"Secret Key length: {len(str(self.secret_key)) if self.secret_key else 0}\n"
                f"=====================\n"
            )
            print(debug_msg, file=sys.stderr)
            sys.stderr.flush()
            logger.warning(debug_msg)

            await client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=contents,
                ContentType="application/zip",
            )
        return key

    async def delete_object(self, key: str) -> None:
        """Delete an object from the submissions bucket.

        ATOMICITY FIX — compensating action for the transactional outbox
        pattern applied to object storage.

        Context: SubmissionService.submit_assignment() uploads the
        student's ZIP to B2 BEFORE the database transaction commits
        (the upload itself cannot be part of the SQL transaction). If the
        subsequent db.commit() fails for any reason, the B2 object would
        otherwise be orphaned — left in the bucket with no Submission row
        pointing to it.

        This method is called from that failure path to delete the
        just-uploaded object, restoring consistency between B2 and
        Postgres: either both the object and the DB row exist, or neither
        does.
        """
        async with await self._create_client() as client:
            try:
                await client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info("Deleted object %s from bucket %s", key, self.bucket_name)
            except Exception as e:
                logger.error("Failed to delete object %s: %s", key, e)
                raise

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
