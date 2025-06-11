import requests
import whisper
import re
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier
import os

def main():
    video_url = os.environ.get('VIDEO_URL', 'https://jobsdemo.z14.web.core.windows.net/azcontainerappup.mp4')

    storage_account_url = os.environ.get("STORAGE_ACCOUNT_URL")
    container_name = os.environ.get("STORAGE_CONTAINER_NAME", "videos")
    blob_name = os.environ.get("STORAGE_BLOB_NAME")

    # Download the video file

    response = requests.get(video_url, stream=True)
    filename = "video.mp4"
    content_disp = response.headers.get("Content-Disposition")
    if content_disp and "filename=" in content_disp:
        match = re.search(r'filename="?([^";]+)"?', content_disp)
        if match:
            filename = match.group(1)
    print(f"Downloading video from {video_url} to {filename}...")
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    model = whisper.load_model("turbo")

    print("Transcribing video...")
    result = model.transcribe(filename)
    print(result["text"])

    print("Saving transcript to blob stroage...")
    
    # Initialize Azure Blob Storage client
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=storage_account_url, credential=credential)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(result["text"], overwrite=True, blob_type="BlockBlob", standard_blob_tier=StandardBlobTier.HOT)

if __name__ == "__main__":
    main()
