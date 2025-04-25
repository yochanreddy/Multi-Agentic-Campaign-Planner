import os
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from creative_planner.utils.error_handler import NyxAIException
from creative_planner.utils.utils import get_required_env_var
from creative_planner.utils.logger import get_logger
from google.auth import exceptions
from google import auth
from google.auth.transport import requests

logger = get_logger(__name__)

def save_image_to_azure(image_data, blob_name):
    """Save image to Azure Blob Storage."""
    logger.info(f"Attempting to save image to Azure: {blob_name}")
    try:
        connection_string = get_required_env_var("AZURE_STORAGE_CONNECTION_STRING")
        container_name = get_required_env_var("AZURE_CONTAINER_NAME")
        
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        blob_client.upload_blob(image_data, overwrite=True)
        
        account_name = get_required_env_var("AZURE_STORAGE_ACCOUNT")
        azure_image_url = f'https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}'
        logger.info(f"Image successfully saved to Azure: {azure_image_url}")
        return azure_image_url
    
    except Exception as e:
        logger.error(f"3001: Failed to save image to Azure: {str(e)}")
        raise NyxAIException(
            internal_code=3001,
            message=f"Failed to save image to Azure: {str(e)}",
            http_status_code=500
        )

def save_image_to_gcp(image_data, gcp_blob_name):
    """Save image to Google Cloud Storage."""
    logger.info(f"Attempting to save image to GCP: {gcp_blob_name}")
    try:
        credentials = get_gcp_credentials()
        storage_client = storage.Client.from_service_account_info(credentials)
        gcp_bucket_name = get_required_env_var("BRAND_GCP_BUCKET_NAME")
        bucket = storage_client.get_bucket(gcp_bucket_name)
        blob = bucket.blob(gcp_blob_name)
        
        logger.debug("Uploading image data to GCP")
        blob.upload_from_string(image_data)
        
        gcp_image_url = f'https://storage.googleapis.com/{gcp_bucket_name}/{gcp_blob_name}'
        logger.info(f"Image successfully saved to GCP: {gcp_image_url}")
        return gcp_image_url
    
    except DefaultCredentialsError:
        logger.critical("2009: GCP credentials not available")
        raise NyxAIException(
            internal_code=2009,
            message="GCP credentials not available",
            http_status_code=500
        )
    except Exception as e:
        logger.error(f"2010: Failed to save image to GCP: {str(e)}")
        raise NyxAIException(
            internal_code=2010,
            message=f"Failed to save image to GCP: {str(e)}",
            http_status_code=500
        )

def save_image(image_data, blob_name):
    """Save image to the configured storage provider."""
    storage_provider = get_required_env_var("STORAGE_PROVIDER", "GCP").upper()
    logger.info(f"the platform to save the image is : {storage_provider}")
    
    if storage_provider == "AZURE":
        return save_image_to_azure(image_data, blob_name)
    elif storage_provider == "GCP":
        return save_image_to_gcp(image_data, blob_name)
    else:
        logger.error(f"3002: Invalid storage provider: {storage_provider}")
        raise NyxAIException(
            internal_code=3002,
            message=f"Invalid storage provider: {storage_provider}. Must be either 'GCP' or 'AZURE'",
            http_status_code=500
        )

def get_gcp_credentials():
    """Get GCP credentials from environment variables."""
    logger.info("Retrieving GCP credentials")
    try:
        credentials = {
            "type": get_required_env_var("GCP_TYPE"),
            "project_id": get_required_env_var("GCP_PROJECT_ID"),
            "private_key_id": get_required_env_var("GCP_PRI_KEY_ID"),
            "private_key": get_required_env_var("GCP_PRI_KEY").replace('\\n', '\n'),  
            "client_email": get_required_env_var("GCP_CLIENT_EMAIL"),
            "client_id": get_required_env_var("GCP_CLIENT_ID"),
            "auth_uri": get_required_env_var("GCP_AUTH_URI"),
            "token_uri": get_required_env_var("GCP_TOKEN_URI"),
            "auth_provider_x509_cert_url": get_required_env_var("GCP_AUTH_PROVIDER"),
            "client_x509_cert_url": get_required_env_var("GCP_CLIENT_CERT_URL"),
            "universe_domain": get_required_env_var("GCP_UNIVERSE_DOMAIN")
        }

        for key in credentials:
            if credentials[key] is None:
                logger.critical(f"2011: Missing critical GCP credential: {key}")
                raise NyxAIException(
                    internal_code=2011,
                    message=f"Missing environment variable for {key}",
                    http_status_code=500
                )

        logger.info("GCP credentials successfully retrieved")
        return credentials
    except NyxAIException:
        raise
    except Exception as e:
        logger.critical(f"2012: Failed to get GCP credentials: {str(e)}")
        raise NyxAIException(
            internal_code=2012,
            message=f"Failed to get GCP credentials: {str(e)}",
            http_status_code=500
        )

def generate_signed_url_gcp(bucket_name, object_key, expiration_time=3600):
    """Generate a signed URL for GCP storage object."""
    logger.info(f"Generating signed URL for {bucket_name}/{object_key}")
    try:
        credentials = get_gcp_credentials()
        client = storage.Client.from_service_account_info(credentials)
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(object_key)

        try:
            url = blob.generate_signed_url(version="v4", expiration=expiration_time, method="GET")
            logger.info("Signed URL generated successfully")
            return url
        except exceptions.RefreshError:
            logger.warning("Token refresh required, attempting to refresh credentials")
            credentials, project_id = auth.default()
            credentials.refresh(requests.Request())
            url = blob.generate_signed_url(expiration=expiration_time)
            logger.info("Signed URL generated after credential refresh")
            return url

    except DefaultCredentialsError:
        logger.critical("2011: Failed to generate signed URL: Credentials not available")
        raise NyxAIException(
            internal_code=2011,
            message="Failed to generate signed URL: Credentials not available",
            http_status_code=500
        )
    except Exception as e:
        logger.error(f"2013: Failed to generate signed URL: {str(e)}")
        raise NyxAIException(
            internal_code=2013,
            message=f"Failed to generate signed URL: {str(e)}",
            http_status_code=500
        )

def generate_signed_url_azure(blob_name, expiration_time=3600):
    """Generate a SAS token URL for Azure Blob Storage."""
    logger.info(f"Generating SAS token URL for blob: {blob_name}")
    try:
        account_name = get_required_env_var("AZURE_STORAGE_ACCOUNT")
        account_key = get_required_env_var("AZURE_STORAGE_KEY")
        container_name = get_required_env_var("AZURE_CONTAINER_NAME")

        # Calculate start and expiry times
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(seconds=expiration_time)

        # Create SAS token with read permission
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            start=start_time,
            expiry=expiry_time
        )

        # Construct the full URL with SAS token
        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        logger.info("SAS token URL generated successfully")
        return sas_url

    except Exception as e:
        logger.error(f"3003: Failed to generate Azure SAS token: {str(e)}")
        raise NyxAIException(
            internal_code=3003,
            message=f"Failed to generate Azure SAS token: {str(e)}",
            http_status_code=500
        )

def get_signed_url(blob_name, expiration_time=3600):
    """Get a signed URL for the blob based on the configured storage provider."""
    storage_provider = get_required_env_var("STORAGE_PROVIDER", "GCP").upper()
    logger.info(f"the platform to save the signed url is: {storage_provider}")
    
    if storage_provider == "AZURE":
        return generate_signed_url_azure(blob_name, 2592000)#30 days
    elif storage_provider == "GCP":
        bucket_name = get_required_env_var("BRAND_GCP_BUCKET_NAME")
        return generate_signed_url_gcp(bucket_name, blob_name, expiration_time)
    else:
        logger.error(f"3002: Invalid storage provider: {storage_provider}")
        raise NyxAIException(
            internal_code=3002,
            message=f"Invalid storage provider: {storage_provider}. Must be either 'GCP' or 'AZURE'",
            http_status_code=500
        ) 