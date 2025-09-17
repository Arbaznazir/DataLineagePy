import boto3
from datalineagepy.core import LineageTracker


class S3Connector:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name, lineage_tracker=None):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.lineage_tracker = lineage_tracker or LineageTracker()

    def upload_file(self, file_path, bucket, key):
        self.s3.upload_file(file_path, bucket, key)
        self.lineage_tracker.track_operation(
            operation_type='s3_upload',
            inputs=[],
            outputs=[],
            metadata={'file_path': file_path, 'bucket': bucket, 'key': key}
        )

    def download_file(self, bucket, key, file_path):
        self.s3.download_file(bucket, key, file_path)
        self.lineage_tracker.track_operation(
            operation_type='s3_download',
            inputs=[],
            outputs=[],
            metadata={'file_path': file_path, 'bucket': bucket, 'key': key}
        )
