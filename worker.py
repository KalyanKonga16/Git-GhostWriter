from celery import Celery
from config import REDIS_URL
from agent import run_documentation_agent # ensure this import is correct
import traceback # Import traceback

celery = Celery(
    'jobs',
    broker=REDIS_URL,
    backend=REDIS_URL,
    task_track_started=True
)

celery.conf.update(
    task_time_limit=1800, # 30 minute maximum job runtime
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    broker_connection_retry_on_startup=True, # Added this for explicit retry on startup
    # task_soft_time_limit=1500, # Removed as it's not supported on Windows prefork pool
)

@celery.task(bind=True)
def process_repo(self, github_url):
    print(f"\n--- Worker: Task {self.request.id} received for {github_url} ---")
    self.update_state(state='PROGRESS', meta={'stage': 'Starting task'})
    
    def progress_callback(stage, progress=None):
        print(f"Worker: Task {self.request.id} - Progress: {stage} ({progress or 'N/A'}%)")
        self.update_state(state='PROGRESS', meta={
            'stage': stage,
            'progress': progress
        })
    
    try:
        result_dict = run_documentation_agent(github_url, progress_callback)
        print(f"Worker: Task {self.request.id} completed. Result: {result_dict}")
        return result_dict
    except Exception as e:
        print(f"Worker: Task {self.request.id} - An unexpected error occurred: {e}")
        tb_str = traceback.format_exc()
        print(tb_str)
        # Return a dictionary with error details instead of re-raising
        # Celery will still mark the task as FAILED if an exception occurs,
        # but this allows more graceful frontend display if it accesses job.get()
        return {"public_url": None, "error": str(e), "traceback": tb_str}