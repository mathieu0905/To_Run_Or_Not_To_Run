#!/usr/bin/env python3
"""
Test Runner module
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import (
    extract_patch,
    get_instance_info,
    run_experiment,
    save_result,
    print_summary,
    ExperimentResult
)
from agent_caller import AgentTrace


class TestExtractPatch:
    """Test patch extraction functionality"""

    def test_extract_simple_patch(self):
        """Test extracting simple git diff patch"""
        output = """
Some text before
diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def foo():
+    print("hello")
     pass
Some text after
"""
        patch = extract_patch(output)
        assert "diff --git" in patch
        assert "--- a/test.py" in patch
        assert "+++ b/test.py" in patch
        assert "@@" in patch

    def test_extract_no_patch(self):
        """Test case with no patch"""
        output = "Just some regular text without any patch"
        patch = extract_patch(output)
        assert patch == ""

    def test_extract_multiple_files(self):
        """Test extracting multi-file patch"""
        output = """
diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1 +1 @@
-old line
+new line
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
"""
        patch = extract_patch(output)
        assert "file1.py" in patch
        assert "file2.py" in patch


class TestGetInstanceInfo:
    """Test get instance information functionality"""

    @patch('runner.load_dataset')
    def test_get_instance_info_success(self, mock_load_dataset):
        """Test successfully getting instance information"""
        # Mock dataset
        mock_dataset = [
            {"instance_id": "test-1", "problem_statement": "Problem 1"},
            {"instance_id": "test-2", "problem_statement": "Problem 2"},
        ]
        mock_load_dataset.return_value = mock_dataset

        instance = get_instance_info("test-2")
        assert instance["instance_id"] == "test-2"
        assert instance["problem_statement"] == "Problem 2"

    @patch('runner.load_dataset')
    def test_get_instance_info_not_found(self, mock_load_dataset):
        """Test case when instance doesn't exist"""
        mock_dataset = [
            {"instance_id": "test-1", "problem_statement": "Problem 1"},
        ]
        mock_load_dataset.return_value = mock_dataset

        with pytest.raises(ValueError, match="not found in dataset"):
            get_instance_info("nonexistent")


class TestRunExperiment:
    """Test run experiment functionality"""

    @patch('runner.get_instance_info')
    @patch('runner.PromptBuilder.build_prompt')
    @patch('runner.AgentCaller')
    def test_run_experiment_run_free(self, mock_caller_class, mock_build_prompt, mock_get_instance):
        """Test Run-Free mode"""
        # Mock instance information
        mock_get_instance.return_value = {
            "instance_id": "test-1",
            "problem_statement": "Fix the bug",
            "repo": "test/repo"
        }

        # Mock prompt
        mock_build_prompt.return_value = "Test prompt"

        # Mock agent trace
        mock_trace = AgentTrace(
            agent_type="claude_code",
            prompt="Test prompt",
            output="diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py",
            tokens_used=100,
            exec_count=0,
            duration_sec=5.0,
            raw_trace=[],
            error=None
        )

        mock_caller = Mock()
        mock_caller.call.return_value = mock_trace
        mock_caller_class.return_value = mock_caller

        # Run experiment
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                result = run_experiment("test-1", "run_free")

        # Verify results
        assert result.instance_id == "test-1"
        assert result.mode == "run_free"
        assert result.k is None
        assert result.tokens_used == 100
        assert result.exec_count == 0
        assert result.success is True
        assert "diff --git" in result.patch

    @patch('runner.get_instance_info')
    @patch('runner.PromptBuilder.build_prompt')
    @patch('runner.AgentCaller')
    def test_run_experiment_run_less(self, mock_caller_class, mock_build_prompt, mock_get_instance):
        """Test Run-Less mode"""
        mock_get_instance.return_value = {
            "instance_id": "test-2",
            "problem_statement": "Fix the bug",
            "repo": "test/repo"
        }

        mock_build_prompt.return_value = "Test prompt with k=2"

        mock_trace = AgentTrace(
            agent_type="claude_code",
            prompt="Test prompt",
            output="diff --git a/test.py b/test.py",
            tokens_used=200,
            exec_count=2,
            duration_sec=10.0,
            raw_trace=[],
            error=None
        )

        mock_caller = Mock()
        mock_caller.call.return_value = mock_trace
        mock_caller_class.return_value = mock_caller

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                result = run_experiment("test-2", "run_less", k=2)

        assert result.mode == "run_less"
        assert result.k == 2
        assert result.exec_count == 2

    @patch('runner.get_instance_info')
    @patch('runner.PromptBuilder.build_prompt')
    @patch('runner.AgentCaller')
    def test_run_experiment_with_error(self, mock_caller_class, mock_build_prompt, mock_get_instance):
        """Test experiment failure case"""
        mock_get_instance.return_value = {
            "instance_id": "test-3",
            "problem_statement": "Fix the bug",
            "repo": "test/repo"
        }

        mock_build_prompt.return_value = "Test prompt"

        mock_trace = AgentTrace(
            agent_type="claude_code",
            prompt="Test prompt",
            output="",
            tokens_used=50,
            exec_count=0,
            duration_sec=2.0,
            raw_trace=[],
            error="Timeout"
        )

        mock_caller = Mock()
        mock_caller.call.return_value = mock_trace
        mock_caller_class.return_value = mock_caller

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                result = run_experiment("test-3", "run_free")

        assert result.success is False
        assert result.error == "Timeout"
        assert result.patch == ""


class TestSaveResult:
    """Test save result functionality"""

    def test_save_result_run_free(self):
        """Test saving Run-Free result"""
        result = ExperimentResult(
            instance_id="test-1",
            mode="run_free",
            k=None,
            patch="diff --git a/test.py",
            tokens_used=100,
            exec_count=0,
            duration_sec=5.0,
            success=True,
            error="",
            agent_type="claude_code"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                save_result(result)

                # Verify file exists
                result_file = Path(tmpdir) / "test-1_run_free_result.json"
                assert result_file.exists()

                # Verify content
                with open(result_file) as f:
                    data = json.load(f)

                assert data["instance_id"] == "test-1"
                assert data["mode"] == "run_free"
                assert data["tokens_used"] == 100

    def test_save_result_run_less(self):
        """Test saving Run-Less result"""
        result = ExperimentResult(
            instance_id="test-2",
            mode="run_less",
            k=2,
            patch="diff --git a/test.py",
            tokens_used=200,
            exec_count=2,
            duration_sec=10.0,
            success=True,
            error="",
            agent_type="claude_code"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                save_result(result)

                result_file = Path(tmpdir) / "test-2_run_less_k2_result.json"
                assert result_file.exists()

                with open(result_file) as f:
                    data = json.load(f)

                assert data["k"] == 2


class TestPrintSummary:
    """Test print summary functionality"""

    def test_print_summary_success(self, capsys):
        """Test printing successful summary"""
        result = ExperimentResult(
            instance_id="test-1",
            mode="run_free",
            k=None,
            patch="diff --git a/test.py",
            tokens_used=100,
            exec_count=0,
            duration_sec=5.5,
            success=True,
            error="",
            agent_type="claude_code"
        )

        print_summary(result)

        captured = capsys.readouterr()
        assert "EXPERIMENT SUMMARY" in captured.out
        assert "test-1" in captured.out
        assert "run_free" in captured.out
        assert "100" in captured.out
        assert "5.50s" in captured.out

    def test_print_summary_with_error(self, capsys):
        """Test printing summary with error"""
        result = ExperimentResult(
            instance_id="test-2",
            mode="run_less",
            k=2,
            patch="",
            tokens_used=50,
            exec_count=0,
            duration_sec=2.0,
            success=False,
            error="Timeout error occurred",
            agent_type="claude_code"
        )

        print_summary(result)

        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Timeout" in captured.out


class TestExperimentResult:
    """Test ExperimentResult dataclass"""

    def test_experiment_result_creation(self):
        """Test creating ExperimentResult"""
        result = ExperimentResult(
            instance_id="test-1",
            mode="run_free",
            k=None,
            patch="test patch",
            tokens_used=100,
            exec_count=0,
            duration_sec=5.0,
            success=True
        )

        assert result.instance_id == "test-1"
        assert result.mode == "run_free"
        assert result.agent_type == "claude_code"  # Default value

    def test_experiment_result_with_k(self):
        """Test ExperimentResult with k parameter"""
        result = ExperimentResult(
            instance_id="test-2",
            mode="run_less",
            k=3,
            patch="test patch",
            tokens_used=200,
            exec_count=3,
            duration_sec=10.0,
            success=True
        )

        assert result.k == 3
        assert result.exec_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
