import pytest
import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.services.data_processor import DataProcessor


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir) / "data"
        storage_dir = Path(temp_dir) / "storage"
        data_dir.mkdir()
        storage_dir.mkdir()
        
        # Create subdirectories
        (data_dir / "processed").mkdir()
        (data_dir / "error").mkdir()
        
        yield data_dir, storage_dir


@pytest.fixture
def sample_demographic_data():
    """Sample demographic data for testing."""
    return [
        {
            "attributes": {
                "STATE_NAME": "California",
                "POPULATION": 1000000
            }
        },
        {
            "attributes": {
                "STATE_NAME": "California", 
                "POPULATION": 2000000
            }
        },
        {
            "attributes": {
                "STATE_NAME": "Texas",
                "POPULATION": 500000
            }
        }
    ]


@pytest.fixture
def data_processor(temp_dirs):
    """Create DataProcessor instance with temporary directories."""
    data_dir, storage_dir = temp_dirs
    return DataProcessor(str(data_dir), str(storage_dir))


class TestDataProcessor:
    
    def test_init_creates_directories(self, temp_dirs):
        """Test that initialization creates necessary directories."""
        data_dir, storage_dir = temp_dirs
        
        processor = DataProcessor(str(data_dir), str(storage_dir))
        
        assert (data_dir / "processed").exists()
        assert (data_dir / "error").exists()
        assert (storage_dir / "demographics.db").exists()
    
    def test_find_demographic_files(self, data_processor, temp_dirs):
        """Test finding demographic data files."""
        data_dir, _ = temp_dirs
        
        # Create test files - only valid timestamp format should match
        (data_dir / "demographic_data_20260124_120000.json").touch()
        (data_dir / "demographic_data_20260124_130000.json").touch()
        (data_dir / "other_file.json").touch()
        (data_dir / "demographic_data_invalid.json").touch()
        (data_dir / "demographic_data_20260124_140000.json").touch()  # Another valid file
        
        files = data_processor.find_demographic_files()
        
        assert len(files) == 3  # Only files with YYYYMMDD_HHMMSS format
        assert any("120000.json" in f for f in files)
        assert any("130000.json" in f for f in files)
        assert any("140000.json" in f for f in files)
        assert not any("other_file.json" in f for f in files)
        assert not any("invalid.json" in f for f in files)
    
    def test_extract_timestamp(self, data_processor):
        """Test timestamp extraction from filename."""
        timestamp = data_processor.extract_timestamp("demographic_data_20260124_153045.json")
        
        assert timestamp.year == 2026
        assert timestamp.month == 1
        assert timestamp.day == 24
        assert timestamp.hour == 15
        assert timestamp.minute == 30
        assert timestamp.second == 45
    
    def test_extract_timestamp_invalid_format(self, data_processor):
        """Test timestamp extraction with invalid filename."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            data_processor.extract_timestamp("invalid_filename.json")
    
    def test_find_latest_file(self, data_processor, temp_dirs):
        """Test finding the latest file by timestamp."""
        data_dir, _ = temp_dirs
        
        # Create test files with different timestamps
        old_file = str(data_dir / "demographic_data_20260124_120000.json")
        new_file = str(data_dir / "demographic_data_20260124_150000.json")
        
        Path(old_file).touch()
        Path(new_file).touch()
        
        latest = data_processor.find_latest_file([old_file, new_file])
        
        assert latest == new_file
    
    def test_aggregate_by_state(self, data_processor, sample_demographic_data):
        """Test state population aggregation."""
        result = data_processor.aggregate_by_state(sample_demographic_data)
        
        assert result["California"] == 3000000  # 1000000 + 2000000
        assert result["Texas"] == 500000
        assert len(result) == 2
    
    def test_update_database(self, data_processor):
        """Test database update with aggregated data."""
        test_data = {"California": 3000000, "Texas": 500000}
        source_file = "test_file.json"
        
        updated_count = data_processor.update_database(test_data, source_file)
        
        assert updated_count == 2
        
        # Verify database content
        with sqlite3.connect(data_processor.db_path) as conn:
            cursor = conn.execute("SELECT state_name, total_population FROM state_populations")
            rows = cursor.fetchall()
            
            states = {row[0]: row[1] for row in rows}
            assert states["California"] == 3000000
            assert states["Texas"] == 500000
    
    def test_archive_files(self, data_processor, temp_dirs):
        """Test file archiving to processed directory."""
        data_dir, _ = temp_dirs
        
        # Create test files
        file1 = str(data_dir / "file1.json")
        file2 = str(data_dir / "file2.json")
        
        Path(file1).write_text("test1")
        Path(file2).write_text("test2")
        
        data_processor.archive_files([file1, file2])
        
        # Files should be moved
        assert not Path(file1).exists()
        assert not Path(file2).exists()
        assert (data_dir / "processed" / "file1.json").exists()
        assert (data_dir / "processed" / "file2.json").exists()
    
    def test_validate_json_file_valid(self, data_processor, sample_demographic_data, temp_dirs):
        """Test validation of valid JSON file."""
        data_dir, _ = temp_dirs
        
        test_file = data_dir / "valid.json"
        test_file.write_text(json.dumps(sample_demographic_data))
        
        assert data_processor.validate_json_file(str(test_file)) is True
    
    def test_validate_json_file_invalid_structure(self, data_processor, temp_dirs):
        """Test validation of JSON file with invalid structure."""
        data_dir, _ = temp_dirs
        
        # File without required fields
        test_file = data_dir / "invalid.json"
        test_file.write_text(json.dumps([{"test": "data"}]))
        
        assert data_processor.validate_json_file(str(test_file)) is False
    
    def test_validate_json_file_corrupted(self, data_processor, temp_dirs):
        """Test validation of corrupted JSON file."""
        data_dir, _ = temp_dirs
        
        test_file = data_dir / "corrupted.json"
        test_file.write_text("invalid json content")
        
        assert data_processor.validate_json_file(str(test_file)) is False
    
    def test_get_log_filename(self, data_processor):
        """Test log filename generation."""
        log_file = data_processor.get_log_filename()
        
        assert "processed_data_" in log_file
        assert datetime.now().strftime("%Y%m") in log_file
    
    @patch('builtins.open', create=True)
    @patch('builtins.print')
    def test_log_processing(self, mock_print, mock_open, data_processor):
        """Test logging functionality."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        data_processor.log_processing("Test message")
        
        # Check file write
        mock_file.write.assert_called_once()
        written_content = mock_file.write.call_args[0][0]
        assert "Test message" in written_content
        assert datetime.now().strftime("%Y-%m-%d %H:%M:%S") in written_content
        
        # Check console output
        mock_print.assert_called_once()
    
    def test_process_all_data_success(self, data_processor, sample_demographic_data, temp_dirs):
        """Test successful data processing."""
        data_dir, _ = temp_dirs
        
        # Create test data file
        test_file = data_dir / "demographic_data_20260124_120000.json"
        test_file.write_text(json.dumps(sample_demographic_data))
        
        result = data_processor.process_all_data()
        
        assert result is True
        
        # File should be archived
        assert not test_file.exists()
        assert (data_dir / "processed" / "demographic_data_20260124_120000.json").exists()
        
        # Database should be updated
        with sqlite3.connect(data_processor.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM state_populations")
            count = cursor.fetchone()[0]
            assert count == 2  # California and Texas
    
    def test_process_all_data_no_files(self, data_processor):
        """Test processing when no files are found."""
        result = data_processor.process_all_data()
        
        assert result is False
    
    def test_process_all_data_with_error_files(self, data_processor, temp_dirs):
        """Test processing with mixed valid and invalid files."""
        data_dir, _ = temp_dirs
        
        # Create valid file
        valid_data = [
            {"attributes": {"STATE_NAME": "California", "POPULATION": 1000}}
        ]
        valid_file = data_dir / "demographic_data_20260124_120000.json"
        valid_file.write_text(json.dumps(valid_data))
        
        # Create invalid file
        invalid_file = data_dir / "demographic_data_20260124_130000.json"
        invalid_file.write_text("invalid json")
        
        result = data_processor.process_all_data()
        
        assert result is True
        
        # Valid file should be processed and archived
        assert not valid_file.exists()
        assert (data_dir / "processed" / "demographic_data_20260124_120000.json").exists()
        
        # Invalid file should be moved to error
        assert not invalid_file.exists()
        assert (data_dir / "error" / "demographic_data_20260124_130000.json").exists()


if __name__ == "__main__":
    pytest.main([__file__])