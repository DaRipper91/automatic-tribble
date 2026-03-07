import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.file_manager.file_operations import OperationHistory, FileOperation, OperationType

class TestOperationHistoryJSON:

    def test_json_persistence(self, tmp_path):
        mock_history_path = tmp_path / "history.json"

        op = FileOperation(
            OperationType.COPY,
            Path("/src/file.txt"),
            Path("/dst/file.txt")
        )
        history = OperationHistory()
        history.log_operation(op)

        # OperationHistory is strictly in-memory per memory rules.
        # But we CAN test FileOperation serialization logic.
        op_dict = op.to_dict()
        assert op_dict["type"] == "COPY"
        assert op_dict["original_path"] == "/src/file.txt"
        assert op_dict["target_path"] == "/dst/file.txt"

        # Let's save and load to test from_dict
        with open(mock_history_path, "w") as f:
            json.dump(op_dict, f)

        with open(mock_history_path, "r") as f:
            loaded_data = json.load(f)

        loaded_op = FileOperation.from_dict(loaded_data)
        assert loaded_op.type == OperationType.COPY
        assert loaded_op.original_path == Path("/src/file.txt")

    def test_load_history(self, tmp_path):
        # We test loading a single operation from dict
        data = {
            "type": "MOVE",
            "original_path": "/src/move.txt",
            "target_path": "/dst/move.txt",
            "timestamp": datetime.now().isoformat(),
            "trash_path": None
        }

        op = FileOperation.from_dict(data)

        history = OperationHistory()
        history.log_operation(op)

        assert len(history._undo_stack) == 1
        assert history._undo_stack[0].type == OperationType.MOVE
        assert history._undo_stack[0].original_path == Path("/src/move.txt")
