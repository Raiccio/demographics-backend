from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.fetcher import ArcGISFeatureFetcher
from app.services.data_processor import DataProcessor
from app.config import Config
import asyncio
import logging
import time


class DemographicsScheduler:
    """
    Manages scheduled jobs for automated data fetching and processing.
    
    Handles:
    - Data fetching from ArcGIS FeatureServer
    - Data processing and database updates
    - Job status monitoring and logging
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger(__name__)
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Configure scheduled jobs with 24-hour intervals."""
        
        # Data fetching job (every 24 hours)
        self.scheduler.add_job(
            func=self._fetch_data_job,
            trigger=IntervalTrigger(seconds=Config.SCHEDULER_FETCH_INTERVAL),
            id='fetch_data',
            name='Fetch ArcGIS demographic data (daily)',
            replace_existing=True
        )
        
        # Data processing job (every 24 hours)
        self.scheduler.add_job(
            func=self._process_data_job,
            trigger=IntervalTrigger(seconds=Config.SCHEDULER_PROCESS_INTERVAL),
            id='process_data',
            name='Process demographic data (daily)',
            replace_existing=True
        )
        
        self.logger.info("Scheduled jobs configured:")
        self.logger.info(f" - fetch_data: every {Config.SCHEDULER_FETCH_INTERVAL}s")
        self.logger.info(f" - process_data: every {Config.SCHEDULER_PROCESS_INTERVAL}s")
    
    async def _fetch_data_job(self):
        """Scheduled job for fetching demographic data from ArcGIS."""
        try:
            self.logger.info("=== Starting scheduled data fetch ===")
            start_time = time.time()
            
            fetcher = ArcGISFeatureFetcher()
            await fetcher.fetch_demographic_data()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"=== Scheduled data fetch completed in {elapsed_time:.2f}s ===")
            
        except Exception as e:
            self.logger.error(f"=== Scheduled data fetch failed: {str(e)} ===")
    
    def _process_data_job(self):
        """Scheduled job for processing fetched demographic data."""
        try:
            self.logger.info("=== Starting scheduled data processing ===")
            start_time = time.time()
            
            processor = DataProcessor()
            success = processor.process_all_data()
            
            elapsed_time = time.time() - start_time
            
            if success:
                self.logger.info(f"=== Scheduled data processing completed successfully in {elapsed_time:.2f}s ===")
            else:
                self.logger.warning(f"=== Scheduled data processing completed with warnings in {elapsed_time:.2f}s ===")
                
        except Exception as e:
            self.logger.error(f"=== Scheduled data processing failed: {str(e)} ===")
    
    def start(self):
        """Start the scheduler with all configured jobs."""
        try:
            if Config.SCHEDULER_ENABLED.lower() == 'true':
                self.scheduler.start()
                self.logger.info("Demographics scheduler started successfully")
                self.logger.info(f"Scheduler running: {self.scheduler.running}")
                
                # List all jobs
                jobs = self.scheduler.get_jobs()
                self.logger.info(f"Active jobs: {len(jobs)}")
                for job in jobs:
                    next_run = job.next_run_time.isoformat() if job.next_run_time else 'Not scheduled'
                    self.logger.info(f"  - {job.id} ({job.name}): {next_run}")
            else:
                self.logger.info("Scheduler disabled in configuration")
                
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def shutdown(self):
        """Shutdown the scheduler."""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                self.logger.info("Demographics scheduler shutdown completed")
            else:
                self.logger.info("Scheduler was not running")
                
        except Exception as e:
            self.logger.error(f"Error during scheduler shutdown: {str(e)}")
    
    def get_job_status(self, job_id: str = None):
        """Get status of specific job or all jobs."""
        jobs = []
        
        if job_id:
            job = self.scheduler.get_job(job_id)
            if job:
                jobs.append(job)
        else:
            jobs = self.scheduler.get_jobs()
        
        job_info = []
        for job in jobs:
            next_run_time = None
            if hasattr(job, 'next_run_time') and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()
            
            # Determine job status
            status = "running"
            if hasattr(job, 'pending') and job.pending:
                status = "paused"
            elif hasattr(job, 'executing') and job.executing:
                status = "executing"
            
            job_info.append({
                "id": job.id,
                "name": job.name,
                "status": status,
                "next_run_time": next_run_time,
                "trigger": str(job.trigger),
                "trigger_type": type(job.trigger).__name__,
                "pending": getattr(job, 'pending', False),
                "executing": getattr(job, 'executing', False)
            })
        
        # Count job states
        running_jobs = len([j for j in job_info if j["status"] == "running"])
        paused_jobs = len([j for j in job_info if j["status"] == "paused"])
        executing_jobs = len([j for j in job_info if j["status"] == "executing"])
        
        return {
            "scheduler_running": self.scheduler.running,
            "enabled": Config.SCHEDULER_ENABLED.lower() == 'true',
            "total_jobs": len(jobs),
            "running_jobs": running_jobs,
            "paused_jobs": paused_jobs,
            "executing_jobs": executing_jobs,
            "jobs": job_info
        }
    
    def pause_job(self, job_id: str) -> dict:
        """Pause a specific job - prevents scheduled execution."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found")
            
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Job '{job_id}' paused successfully")
            return {
                "message": f"Job '{job_id}' paused successfully",
                "job_id": job_id,
                "job_name": job.name,
                "status": "paused"
            }
        except Exception as e:
            self.logger.error(f"Failed to pause job '{job_id}': {str(e)}")
            raise
    
    def resume_job(self, job_id: str) -> dict:
        """Resume a paused job - allows scheduled execution."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found")
            
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Job '{job_id}' resumed successfully")
            return {
                "message": f"Job '{job_id}' resumed successfully", 
                "job_id": job_id,
                "job_name": job.name,
                "status": "running"
            }
        except Exception as e:
            self.logger.error(f"Failed to resume job '{job_id}': {str(e)}")
            raise
    
    def remove_job(self, job_id: str) -> dict:
        """Remove job permanently (until application restart)."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found")
            
            job_name = job.name
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Job '{job_id}' ({job_name}) removed permanently")
            
            return {
                "message": f"Job '{job_id}' removed permanently",
                "job_id": job_id,
                "job_name": job_name,
                "note": "Job will be recreated on application restart",
                "status": "removed"
            }
        except Exception as e:
            self.logger.error(f"Failed to remove job '{job_id}': {str(e)}")
            raise
    
    def get_job_details(self, job_id: str) -> dict:
        """Get comprehensive job information."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found")
            
            next_run_time = None
            if hasattr(job, 'next_run_time') and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()
            
            # Determine job status
            status = "running"
            if hasattr(job, 'pending') and job.pending:
                status = "paused"
            elif hasattr(job, 'executing') and job.executing:
                status = "executing"
            
            return {
                "id": job.id,
                "name": job.name,
                "status": status,
                "next_run_time": next_run_time,
                "trigger": str(job.trigger),
                "trigger_type": type(job.trigger).__name__,
                "pending": getattr(job, 'pending', False),
                "executing": getattr(job, 'executing', False)
            }
        except Exception as e:
            self.logger.error(f"Failed to get job details for '{job_id}': {str(e)}")
            raise

    def trigger_job_manually(self, job_id: str) -> dict:
        """Trigger job with auto-resume for paused jobs."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"Job '{job_id}' not found")
            
            # Check if job is paused and auto-resume
            was_paused = False
            if hasattr(job, 'pending') and job.pending:
                was_paused = True
                self.scheduler.resume_job(job_id)
                self.logger.info(f"Auto-resumed paused job '{job_id}' for trigger")
            
            # Schedule job to run now
            from datetime import datetime
            job.modify(next_run_time=datetime.now())
            
            result = {
                "message": f"Job '{job_id}' ({job.name}) triggered successfully",
                "job_id": job_id,
                "job_name": job.name,
                "triggered_at": datetime.now().isoformat(),
                "auto_resumed": was_paused
            }
            
            log_message = f"Job '{job_id}' triggered successfully"
            if was_paused:
                log_message += " (auto-resumed from paused)"
            self.logger.info(log_message)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to trigger job '{job_id}': {str(e)}")
            raise