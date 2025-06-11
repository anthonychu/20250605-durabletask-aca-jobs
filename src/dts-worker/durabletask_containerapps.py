import logging
from datetime import timedelta
from typing import Any, Generator

from azure.identity import DefaultAzureCredential
from azure.mgmt.appcontainers import ContainerAppsAPIClient
from azure.mgmt.appcontainers.models import EnvironmentVar
from durabletask import task

from utils import ReplaySafeLogger


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


replay_safe_logger = ReplaySafeLogger(logger)

job_credential = DefaultAzureCredential()


# Suborchestrator function to run a Container Apps job execution

def container_apps_job_suborchestrator(ctx: task.OrchestrationContext, input) -> Generator[Any, Any, Any]:
    """
    Suborchestrator that starts a Container Apps job and waits for its completion.
    """

    replay_safe_logger.info(ctx, f"Starting execution for Container Apps job: {input.get('job_name')}")
    
    # Start the job execution
    job_execution_name = yield ctx.call_activity("start_container_apps_job_execution", input=input)
    
    job_execution = {
        "subscription_id": input.get("subscription_id"),
        "resource_group": input.get("resource_group"),
        "job_name": input.get("job_name"),
        "execution_name": job_execution_name
    }

    # Wait for the job to complete
    while True:
        status = yield ctx.call_activity("get_container_apps_job_execution_status", input=job_execution)
        if status not in ['Running', 'Processing']:
            logger.info(f"Container Apps job execution {job_execution_name} finished with status: {status}")
            break
        else:
            logger.info(f"Container Apps job execution {job_execution_name} is still running, waiting...")
            yield ctx.create_timer(timedelta(seconds=10))
    
    return status


# Activity functions to start and monitor Container Apps job executions

def start_container_apps_job_execution(ctx, input) -> str:
    subscription_id = input.get("subscription_id")
    resource_group = input.get("resource_group")
    job_name = input.get("job_name")
    env: list[dict[str, str]] = input.get("env", [])

    client = ContainerAppsAPIClient(job_credential, subscription_id)
    job_template = None

    # if there are environment variables to override
    if len(env) > 0:
        logger.info(f"Overriding environment variables for job {job_name} in resource group {resource_group}")
        job_template = client.jobs.get(resource_group, job_name).template
        if not job_template or not job_template.containers:
            raise Exception(f"Job template for {job_name} in resource group {resource_group} is not valid or does not contain containers.")
        first_container = job_template.containers[0]
        if not first_container.env:
            first_container.env = []
        for env_var in env:
            existing_env_var = next((e for e in first_container.env if e.name == env_var["name"]), None)
            if existing_env_var:
                existing_env_var.value = env_var["value"]
            else:
                first_container.env.append(EnvironmentVar(name=env_var["name"], value=env_var["value"]))

    result = client.jobs.begin_start(resource_group, job_name, job_template).result() # type: ignore
    
    if not result or not result.name:
        raise Exception(f"Failed to start job {job_name} in resource group {resource_group}")
    
    return result.name


def get_container_apps_job_execution_status(ctx, input: dict) -> str:
    subscription_id = input.get("subscription_id") or ""
    resource_group = input.get("resource_group") or ""
    job_name = input.get("job_name") or ""
    execution_name = input.get("execution_name") or ""
    
    client = ContainerAppsAPIClient(job_credential, subscription_id)
    job_execution = client.job_execution(resource_group, job_name, execution_name)

    logger.info(f"job_execution object: {job_execution}")
    status = job_execution.status or "Unknown"
    return status
