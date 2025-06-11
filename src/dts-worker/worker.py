import asyncio
import logging
import os
from typing import Any, Generator
from azure.identity import DefaultAzureCredential
from durabletask import task
from durabletask.azuremanaged.worker import DurableTaskSchedulerWorker
from durabletask_containerapps import container_apps_job_suborchestrator, start_container_apps_job_execution, get_container_apps_job_execution_status

from dotenv import load_dotenv
import requests
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Orchestrator function
def video_transcript_fan_out_fan_in_orchestrator(ctx: task.OrchestrationContext, session_codes: list) -> Generator[Any, Any, Any]:

    logger.info(f"Starting fan out/fan in orchestration with {len(session_codes)} items")
    
    # subscription_id = "ef90e930-9d7f-4a60-8a99-748e0eea69de"
    # resource_group = "20250609-dts-jobs"
    # job_name = "transcribe-video-job"

    subscription_id = os.getenv("SUBSCRIPTION_ID")
    resource_group = os.getenv("RESOURCE_GROUP")
    job_name = os.getenv("JOB_NAME")
    
    logger.info(f"Using subscription_id: {subscription_id}, resource_group: {resource_group}, job_name: {job_name}")

    videos = yield ctx.call_activity("get_video_urls", input=session_codes)
    
    # fan out: start a container apps job for each video
    parallel_tasks = []
    for video in videos:
        transcript_path = f"transcripts-{ctx.instance_id}/{video['session_code']}.txt"
        video["transcript_path"] = transcript_path
        
        parallel_tasks.append(ctx.call_sub_orchestrator(container_apps_job_suborchestrator, input={
            "subscription_id": subscription_id,
            "resource_group": resource_group,
            "job_name": job_name,
            "env": [
                {"name": "VIDEO_URL", "value": video["video_url"]},
                {"name": "STORAGE_BLOB_NAME", "value": f"{transcript_path}"},
            ]
        }))
    
    # Wait for all tasks to complete
    logger.info(f"Waiting for {len(parallel_tasks)} parallel tasks to complete")
    results = yield task.when_all(parallel_tasks)
    
    return videos


# Activity function to fetch video URLs
def get_video_urls(ctx, session_codes: list[str]) -> list[str]:
    videos = []
    for code in session_codes:
        code = code.upper()
        logger.info(f"Processing session code: {code}")
        info_url = f"https://api-v2.build.microsoft.com/api/session/en-US-{code}"
        response = requests.get(info_url)
        if response.status_code == 200:
            data = response.json()
            download_link = data.get("downloadVideoLink")
            if download_link:
                videos.append({
                    "session_code": code,
                    "video_url": download_link
                })
        else:
            logger.warning(f"Failed to fetch {info_url}: {response.status_code}")
    return videos


async def main():
    """Main entry point for the worker process."""
    logger.info("Starting Fan Out/Fan In pattern worker...")
    
    # Get environment variables for taskhub and endpoint with defaults
    taskhub_name = os.getenv("TASKHUB", "default")
    endpoint = os.getenv("ENDPOINT", "http://localhost:8080")

    print(f"Using taskhub: {taskhub_name}")
    print(f"Using endpoint: {endpoint}")

    # Set credential to None for emulator, or DefaultAzureCredential for Azure
    credential = None if endpoint == "http://localhost:8080" else DefaultAzureCredential()
    
    # Create a worker using Azure Managed Durable Task and start it with a context manager
    with DurableTaskSchedulerWorker(
        host_address=endpoint, 
        secure_channel=endpoint != "http://localhost:8080",
        taskhub=taskhub_name, 
        token_credential=credential
    ) as worker:
        
        worker.add_orchestrator(video_transcript_fan_out_fan_in_orchestrator)
        worker.add_activity(get_video_urls)

        worker.add_activity(start_container_apps_job_execution)
        worker.add_activity(get_container_apps_job_execution_status)
        worker.add_orchestrator(container_apps_job_suborchestrator)
        
        # Start the worker (without awaiting)
        worker.start()
        
        try:
            # Keep the worker running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutdown initiated")
            
    logger.info("Worker stopped")

if __name__ == "__main__":
    asyncio.run(main())