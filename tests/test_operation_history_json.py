import json
import pytest
from unittest.mock import patch
from pathlib import Path
from datetime import datetime
from src.file_manager.file_operations import OperationHistory, FileOperation, OperationType

class TestOperationHistoryJSON:

    @pytest.fixture
    def mock_history_path(self, tmp_path):
        return tmp_path / "history.json"

    @pytest.fixture
    def history(self, mock_history_path):
        # OperationHistory sets self.history_file in __init__, so it's an instance attribute, not class attribute.
        # We should rely on patching Path.home() to redirect the file location.

        with patch("pathlib.Path.home", return_value=mock_history_path.parent):
             # Create .tfm dir
            (mock_history_path.parent / ".tfm").mkdir(parents=True, exist_ok=True)
            h = OperationHistory()
            return h

    def test_json_persistence(self, history, mock_history_path):
        op = FileOperation(
            OperationType.COPY,
            Path("/src/file.txt"),
            Path("/dst/file.txt")
        )
        history.log_operation(op)

        # Check if file exists (path construction is slightly tricky with mocks, but let's verify logic)
        # History file is at mock_history_path.parent / ".tfm" / "history.json"
        expected_file = mock_history_path.parent / ".tfm" / "history.json"

        assert expected_file.exists()

        # Read file manually
        with open(expected_file, "r") as f:
            data = json.load(f)

        assert len(data["undo"]) == 1
        assert data["undo"][0]["type"] == "COPY"
        assert data["undo"][0]["original_path"] == str(Path("/src/file.txt"))

    def test_load_history(self, mock_history_path):
        # Create a history file
        data = {
            "undo": [{
                "type": "MOVE",
                "original_path": "/src/move.txt",
                "target_path": "/dst/move.txt",
                "timestamp": datetime.now().isoformat(),
                "trash_path": None
            }],
            "redo": []
        }

        history_file = mock_history_path.parent / ".tfm" / "history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, "w") as f:
            json.dump(data, f)

        # Create new history instance to load it
        with patch("pathlib.Path.home", return_value=mock_history_path.parent):
            new_history = OperationHistory()

            assert len(new_history._undo_stack) == 1
            assert new_history._undo_stack[0].type == OperationType.MOVE
            assert str(new_history._undo_stack[0].original_path) == str(Path("/src/move.txt"))

    def test_corrupt_history_file(self, mock_history_path):
        history_file = mock_history_path.parent / ".tfm" / "history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, "w") as f:
            f.write("{invalid json")

        with patch("pathlib.Path.home", return_value=mock_history_path.parent):
            new_history = OperationHistory()
            # Should gracefully fail and have empty stacks
            assert len(new_history._undo_stack) == 0

    def test_round_trip_serialization(self):
        op = FileOperation(
            OperationType.DELETE,
            Path("/path/to/delete"),
            trash_path=Path("/trash/path"),
            timestamp=datetime.now()
        )

        data = op.to_dict()
        restored_op = FileOperation.from_dict(data)

        assert restored_op.type == op.type
        assert restored_op.original_path == op.original_path
        assert restored_op.trash_path == op.trash_path
        assert restored_op.timestamp == op.timestamp
