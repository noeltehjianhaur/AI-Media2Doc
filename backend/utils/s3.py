# -*- coding: UTF-8 -*-
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

import env


def get_s3_client():
    """获取 S3 客户端实例"""
    # 确保 endpoint 包含协议前缀
    endpoint = env.STORAGE_ENDPOINT
    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"https://{endpoint}"

    return boto3.client(
        "s3",
        aws_access_key_id=env.STORAGE_ACCESS_KEY,
        aws_secret_access_key=env.STORAGE_SECRET_KEY,
        endpoint_url=endpoint,
        region_name=env.STORAGE_REGION,
        use_ssl=True,
        verify=True,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},  # TOS 要求使用 Virtual-Hosted-Style
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def generate_download_url(file_name: str):
    """生成文件下载 URL (使用 S3 兼容协议)"""
    s3_client = get_s3_client()

    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": env.STORAGE_BUCKET, "Key": file_name},
        ExpiresIn=3600,
    )


def generate_upload_url(file_name: str):
    """生成文件上传 URL (使用 S3 兼容协议)"""
    s3_client = get_s3_client()

    return s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": env.STORAGE_BUCKET, "Key": file_name},
        ExpiresIn=3600,
    )


def upload_bytes(file_name: str, data: bytes, content_type: str = "audio/mpeg"):
    """服务端直传对象到存储桶"""
    get_s3_client().put_object(
        Bucket=env.STORAGE_BUCKET,
        Key=file_name,
        Body=data,
        ContentType=content_type,
    )
    return file_name


def delete_object(file_name: str):
    """Delete one temporary object from the configured storage bucket."""
    get_s3_client().delete_object(Bucket=env.STORAGE_BUCKET, Key=file_name)


def delete_objects_by_prefix(prefix: str):
    """Delete every object under a task-owned prefix and return the delete count."""
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    deleted = 0
    for page in paginator.paginate(Bucket=env.STORAGE_BUCKET, Prefix=prefix):
        objects = [{"Key": item["Key"]} for item in page.get("Contents", [])]
        if not objects:
            continue
        client.delete_objects(
            Bucket=env.STORAGE_BUCKET,
            Delete={"Objects": objects, "Quiet": True},
        )
        deleted += len(objects)
    return deleted


def configure_temporary_lifecycle(days: int = 1):
    """Ensure task-owned temporary objects expire without replacing unrelated rules."""
    client = get_s3_client()
    try:
        current = client.get_bucket_lifecycle_configuration(Bucket=env.STORAGE_BUCKET)
        rules = current.get("Rules", [])
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code not in {"NoSuchLifecycleConfiguration", "NoSuchLifecycle"}:
            raise
        rules = []
    rule_id = "ai-media2doc-temporary-cleanup"
    rules = [rule for rule in rules if rule.get("ID") != rule_id]
    rules.append(
        {
            "ID": rule_id,
            "Status": "Enabled",
            "Filter": {"Prefix": "temporary/"},
            "Expiration": {"Days": days},
            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": days},
        }
    )
    client.put_bucket_lifecycle_configuration(
        Bucket=env.STORAGE_BUCKET,
        LifecycleConfiguration={"Rules": rules},
    )
