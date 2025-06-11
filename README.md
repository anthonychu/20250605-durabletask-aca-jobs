# Durable Task Scheduler with Azure Container Apps Jobs

This project demonstrates how to use the Durable Task Scheduler with Azure Container Apps Jobs to implement a fan-out/fan-in pattern for video transcription at scale.

## Architecture

The solution consists of two main components:

### 1. DTS Worker (`src/dts-worker/`)
A Durable Task Scheduler worker that orchestrates the video transcription workflow:
- **Orchestrator**: Implements a fan-out/fan-in pattern to process multiple videos in parallel
- **Activity Functions**: Fetch video URLs and manage Azure Container Apps job executions
- **Suborchestrator**: Manages individual Container Apps job lifecycles

### 2. Transcribe Video Job (`src/transcribe-video-job/`)
A containerized job that performs the actual video transcription:
- Downloads videos from provided URLs
- Uses OpenAI Whisper for speech-to-text transcription
- Stores transcripts in Azure Blob Storage

## Workflow

1. The orchestrator receives a list of session codes
2. It fetches video URLs for each session code from the Microsoft Build API
3. For each video, it starts an Azure Container Apps job execution
4. Each job downloads the video, transcribes it using Whisper, and stores the transcript
5. The orchestrator waits for all parallel jobs to complete
6. Returns the processed video information with transcript paths

## Prerequisites

- Python 3.10+ (for dts-worker) and Python 3.12+ (for transcribe-video-job)
- [uv](https://docs.astral.sh/uv/) for Python dependency management
- Docker for containerization
- Azure subscription with the following resources:
  - Azure Container Apps Environment
  - Azure Container Apps Job
  - Azure Storage Account
  - Azure Durable Task Hub (or local emulator for development)

## Environment Variables

### DTS Worker
- `TASKHUB`: Durable Task hub name (default: "default")
- `ENDPOINT`: Durable Task endpoint (default: "http://localhost:8080" for emulator)
- `SUBSCRIPTION_ID`: Azure subscription ID
- `RESOURCE_GROUP`: Azure resource group containing the Container Apps job
- `JOB_NAME`: Name of the Azure Container Apps job

### Transcribe Video Job
- `VIDEO_URL`: URL of the video to transcribe
- `STORAGE_ACCOUNT_URL`: Azure Storage account URL
- `STORAGE_CONTAINER_NAME`: Blob container name (default: "videos")
- `STORAGE_BLOB_NAME`: Output blob name for the transcript

## Local Development

### Running the DTS Worker

1. Navigate to the dts-worker directory:
   ```bash
   cd src/dts-worker
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables (create `.env` file):
   ```bash
   TASKHUB=default
   ENDPOINT=http://localhost:8080
   SUBSCRIPTION_ID=your-subscription-id
   RESOURCE_GROUP=your-resource-group
   JOB_NAME=your-container-apps-job-name
   ```

4. Run the worker:
   ```bash
   uv run worker.py
   ```

### Running the Transcribe Video Job Locally

1. Navigate to the transcribe-video-job directory:
   ```bash
   cd src/transcribe-video-job
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables:
   ```bash
   export VIDEO_URL="https://example.com/video.mp4"
   export STORAGE_ACCOUNT_URL="https://yourstorageaccount.blob.core.windows.net"
   export STORAGE_CONTAINER_NAME="videos"
   export STORAGE_BLOB_NAME="transcript.txt"
   ```

4. Run the job:
   ```bash
   uv run main.py
   ```

## Docker Deployment

### Building Images

Build the DTS worker image:
```bash
cd src/dts-worker
docker build -t dts-worker .
```

Build the transcribe video job image:
```bash
cd src/transcribe-video-job
docker build -t transcribe-video-job .
```

### Azure Container Apps Deployment

1. Deploy the transcribe video job as an Azure Container Apps Job
2. Deploy the DTS worker as an Azure Container Apps application or run it elsewhere
3. Configure the appropriate environment variables for each component
4. Ensure the DTS worker has permissions to start and monitor the Container Apps job

## Usage Example

To start a video transcription workflow, send a request to your Durable Task orchestrator with session codes:

```python
# Example session codes from Microsoft Build sessions
session_codes = ["DEM520", "DEM499", "DEM541", "DEM563"]
```

The orchestrator will:
1. Fetch video URLs for each session code
2. Start parallel Container Apps job executions
3. Wait for all transcriptions to complete
4. Return the results with transcript storage paths

## Key Features

- **Scalable**: Process multiple videos in parallel using Azure Container Apps jobs
- **Resilient**: Durable Task Scheduler provides automatic retries and failure handling
- **Cost-effective**: Container Apps jobs scale to zero when not in use
- **Flexible**: Easy to modify for different video sources or transcription models

## Dependencies

### DTS Worker
- `azure-identity`: Azure authentication
- `azure-mgmt-appcontainers`: Container Apps management
- `durabletask-azuremanaged`: Durable Task Scheduler for Azure
- `python-dotenv`: Environment variable management

### Transcribe Video Job
- `azure-identity`: Azure authentication
- `azure-storage-blob`: Blob storage operations
- `openai-whisper`: Speech-to-text transcription

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is provided as a demonstration and is available under the terms specified by the repository license.