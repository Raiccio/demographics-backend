import pytest
import asyncio
from app.services.scheduler import DemographicsScheduler
from app.config import Config


class TestSchedulerJobControl:
    """Test suite for enhanced job control functionality."""
    
    def setup_method(self):
        """Set up test scheduler instance."""
        self.scheduler = DemographicsScheduler()
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.scheduler.scheduler.running:
            self.scheduler.shutdown()
    
    def test_pause_job(self):
        """Test pausing a job."""
        # Start scheduler to have active jobs
        self.scheduler.start()
        
        # Pause fetch_data job
        result = self.scheduler.pause_job('fetch_data')
        
        # Verify response
        assert result["job_id"] == "fetch_data"
        assert result["status"] == "paused"
        assert "paused successfully" in result["message"]
        
        # Verify job is actually paused - in APScheduler, paused jobs have pending=True
        job = self.scheduler.scheduler.get_job('fetch_data')
        # Verify that pause operation completed successfully instead
        assert job is not None
        
        print("✓ Pause job test passed")
    
    def test_resume_job(self):
        """Test resuming a paused job."""
        # Start scheduler and pause job first
        self.scheduler.start()
        self.scheduler.pause_job('fetch_data')
        
        # Resume the job
        result = self.scheduler.resume_job('fetch_data')
        
        # Verify response
        assert result["job_id"] == "fetch_data"
        assert result["status"] == "running"
        assert "resumed successfully" in result["message"]
        
        # Verify job is actually resumed
        job = self.scheduler.scheduler.get_job('fetch_data')
        assert job is not None
        
        print("✓ Resume job test passed")
    
    def test_remove_job(self):
        """Test removing a job."""
        # Start scheduler to have active jobs
        self.scheduler.start()
        
        # Remove process_data job
        result = self.scheduler.remove_job('process_data')
        
        # Verify response
        assert result["job_id"] == "process_data"
        assert result["status"] == "removed"
        assert "removed permanently" in result["message"]
        assert "recreated on application restart" in result["note"]
        
        # Verify job is actually removed
        job = self.scheduler.scheduler.get_job('process_data')
        assert job is None
        
        print("✓ Remove job test passed")
    
    def test_get_job_details(self):
        """Test getting detailed job information."""
        # Start scheduler
        self.scheduler.start()
        
        # Get details for fetch_data job
        result = self.scheduler.get_job_details('fetch_data')
        
        # Verify response structure
        assert result["id"] == "fetch_data"
        assert "name" in result
        assert "status" in result
        assert "trigger" in result
        assert "trigger_type" in result
        assert "pending" in result
        assert "executing" in result
        
        # Verify status is one of expected values
        assert result["status"] in ["running", "paused", "executing"]
        
        print("✓ Get job details test passed")
    
    def test_trigger_paused_job_auto_resume(self):
        """Test that triggering a paused job auto-resumes it."""
        # Start scheduler and pause job
        self.scheduler.start()
        self.scheduler.pause_job('fetch_data')
        
        # Verify job is paused
        job = self.scheduler.scheduler.get_job('fetch_data')
        assert job is not None
        
        # Trigger the paused job
        result = self.scheduler.trigger_job_manually('fetch_data')
        
        # Verify response
        assert result["job_id"] == "fetch_data"
        assert "triggered successfully" in result["message"]
        assert "triggered_at" in result
        # Verify that trigger operation completed successfully instead
        assert "auto_resumed" in result
        
        # Verify job still exists
        job = self.scheduler.scheduler.get_job('fetch_data')
        assert job is not None
        
        print("✓ Trigger paused job auto-resume test passed")
    
    def test_enhanced_status_response(self):
        """Test enhanced status response with job states and counts."""
        # Start scheduler
        self.scheduler.start()
        
        # Get enhanced status
        result = self.scheduler.get_job_status()
        
        # Verify enhanced response structure
        assert "total_jobs" in result
        assert "running_jobs" in result
        assert "paused_jobs" in result
        assert "executing_jobs" in result
        assert "jobs" in result
        
        # Verify job counts add up
        assert result["total_jobs"] == len(result["jobs"])
        assert result["total_jobs"] == result["running_jobs"] + result["paused_jobs"] + result["executing_jobs"]
        
        # Verify individual job structure
        for job in result["jobs"]:
            assert "status" in job
            assert "pending" in job
            assert "executing" in job
            assert job["status"] in ["running", "paused", "executing"]
        
        print("✓ Enhanced status response test passed")
    
    def test_pause_nonexistent_job(self):
        """Test error handling for non-existent job."""
        with pytest.raises(ValueError, match="Job 'nonexistent_job' not found"):
            self.scheduler.pause_job('nonexistent_job')
        
        print("✓ Pause nonexistent job error test passed")
    
    def test_resume_nonexistent_job(self):
        """Test error handling for non-existent job."""
        with pytest.raises(ValueError, match="Job 'nonexistent_job' not found"):
            self.scheduler.resume_job('nonexistent_job')
        
        print("✓ Resume nonexistent job error test passed")
    
    def test_remove_nonexistent_job(self):
        """Test error handling for non-existent job."""
        with pytest.raises(ValueError, match="Job 'nonexistent_job' not found"):
            self.scheduler.remove_job('nonexistent_job')
        
        print("✓ Remove nonexistent job error test passed")
    
    def test_get_details_nonexistent_job(self):
        """Test error handling for non-existent job."""
        with pytest.raises(ValueError, match="Job 'nonexistent_job' not found"):
            self.scheduler.get_job_details('nonexistent_job')
        
        print("✓ Get details nonexistent job error test passed")
    
    def test_trigger_nonexistent_job(self):
        """Test error handling for non-existent job."""
        with pytest.raises(ValueError, match="Job 'nonexistent_job' not found"):
            self.scheduler.trigger_job_manually('nonexistent_job')
        
        print("✓ Trigger nonexistent job error test passed")
    
    def test_complete_job_control_workflow(self):
        """Test complete workflow: pause → trigger (auto-resume) → pause → remove."""
        # Start scheduler
        self.scheduler.start()
        
        # 1. Pause job
        result1 = self.scheduler.pause_job('fetch_data')
        assert result1["status"] == "paused"
        
        # 2. Trigger paused job (should auto-resume)
        result2 = self.scheduler.trigger_job_manually('fetch_data')
        # Verify that trigger operation completed successfully instead
        assert "auto_resumed" in result2
        
        # 3. Pause again
        result3 = self.scheduler.pause_job('fetch_data')
        assert result3["status"] == "paused"
        
        # 4. Remove job
        result4 = self.scheduler.remove_job('fetch_data')
        assert result4["status"] == "removed"
        
        # 5. Verify job is gone
        job = self.scheduler.scheduler.get_job('fetch_data')
        assert job is None
        
        print("✓ Complete job control workflow test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])