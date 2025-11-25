from minio import Minio

bucketName = "application" #minio桶名
minio_client = Minio(
    endpoint="10.120.24.109:19000",  # MinIO服务器地址和端口
    access_key="admin",   # 访问密钥
    secret_key="admin123456",   # 秘密密钥
    secure=False  # 设置为True如果使用HTTPS；False则使用HTTP[citation:7]
)
headers = {
            "Authorization": "aaab26be-c720-44e0-b10a-73948a3ec247"
}

