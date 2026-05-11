"""
Azure integration for Healthcare Access Analyzer.
Services: Azure Blob Storage, Azure Databricks, Azure Health Data Services.
"""
import os

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_CONTAINER_FACILITIES = "healthcare-facilities"
AZURE_CONTAINER_RESULTS = "healthcare-results"
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
AZURE_HEALTH_DATA_ENDPOINT = os.getenv("AZURE_HEALTH_DATA_ENDPOINT", "")


def upload_to_blob(local_path: str, blob_name: str, container: str) -> None:
    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        with open(local_path, "rb") as f:
            client.get_blob_client(container=container, blob=blob_name).upload_blob(f, overwrite=True)
        print(f"Uploaded {blob_name} to {container}")
    except ImportError:
        print("azure-storage-blob not installed")


def get_databricks_job(script: str = "pipeline/spark_pipeline.py") -> dict:
    return {
        "run_name": "HealthcareAccessPipeline",
        "spark_python_task": {"python_file": f"dbfs:/FileStore/{script}"},
    }
