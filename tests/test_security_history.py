import json
import pytest
from unittest.mock import patch
from pathlib import Path
from src.file_manager.file_operations import OperationHistory, FileOperation, OperationType

class TestSecurityHistory:

    @pytest.fixture
    def tfm_dir(self, tmp_path):
        d = tmp_path / ".tfm"
        d.mkdir()
        return d

    def test_history_is_json(self, tfm_dir):
        with patch("pathlib.Path.home", return_value=tfm_dir.parent):
            history = OperationHistory()
            op = FileOperation(OperationType.COPY, Path("/src"), Path("/dst"))
            history.log_operation(op)

            history_file = tfm_dir / "history.json"
            assert history_file.exists()

            # Verify it's valid JSON and has the expected structure
            with open(history_file, "r") as f:
                data = json.load(f)
                assert "undo" in data
                assert "redo" in data
                assert len(data["undo"]) == 1
                assert data["undo"][0]["type"] == "COPY"
                assert data["undo"][0]["original_path"] == "/src"
                assert data["undo"][0]["target_path"] == "/dst"

    def test_pickle_not_used(self, tfm_dir):
        with patch("pathlib.Path.home", return_value=tfm_dir.parent):
            # We want to ensure pickle is not imported or used
            # We can check sys.modules or mock pickle and check calls
            with patch("pickle.load") as mock_pickle_load, \
                 patch("pickle.dump") as mock_pickle_dump:

                history = OperationHistory()
                op = FileOperation(OperationType.DELETE, Path("/file"))
                history.log_operation(op)

                # Try to load again
                new_history = OperationHistory()

                assert mock_pickle_load.call_count == 0
                assert mock_pickle_dump.call_count == 0

    def test_cleanup_pickle_on_init(self, tfm_dir):
        old_file = tfm_dir / "history.pkl"
        old_file.write_text("malicious pickle data")

        with patch("pathlib.Path.home", return_value=tfm_dir.parent):
            assert old_file.exists()
            history = OperationHistory()
            # The insecure file should be deleted upon initialization
            assert not old_file.exists()
