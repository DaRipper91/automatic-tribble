import pytest
import json
from unittest.mock import patch
from pathlib import Path
from src.file_manager.file_operations import OperationHistory, FileOperation, OperationType

class TestOperationHistory:

    @pytest.fixture
    def history_file(self, tmp_path):
        return tmp_path / "history.json"

    @pytest.fixture
    def history(self, history_file):
        with patch("pathlib.Path.home", return_value=history_file.parent):
             # It expects .tfm subdir
            (history_file.parent / ".tfm").mkdir(parents=True, exist_ok=True)
            h = OperationHistory()
            # Verify it uses the correct path
            assert h.history_file == history_file.parent / ".tfm" / "history.json"
            return h

    def test_log_operation(self, history):
        op = FileOperation(OperationType.COPY, Path("/src"), Path("/dst"))
        history.log_operation(op)

        assert len(history._undo_stack) == 1
        assert len(history._redo_stack) == 0
        assert history._undo_stack[0] == op

    def test_undo_last(self, history):
        op = FileOperation(OperationType.MOVE, Path("/src"), Path("/dst"))
        history.log_operation(op)

        undone_op = history.undo_last()
        assert undone_op == op
        assert len(history._undo_stack) == 0
        assert len(history._redo_stack) == 1
        assert history._redo_stack[0] == op

    def test_redo_last(self, history):
        op = FileOperation(OperationType.DELETE, Path("/src"), trash_path=Path("/trash"))
        history.log_operation(op)
        history.undo_last()

        redone_op = history.redo_last()
        assert redone_op == op
        assert len(history._undo_stack) == 1
        assert len(history._redo_stack) == 0

    def test_persistence_json(self, history, history_file):
        op = FileOperation(OperationType.CREATE_DIR, Path("/new_dir"))
        history.log_operation(op)

        # Verify file exists and is JSON
        json_path = history_file.parent / ".tfm" / "history.json"
        assert json_path.exists()

        with open(json_path, "r") as f:
            data = json.load(f)
            assert "undo" in data
            assert len(data["undo"]) == 1
            assert data["undo"][0]["type"] == "CREATE_DIR"
            assert data["undo"][0]["original_path"] == str(Path("/new_dir"))

        # Create a new instance and verify it loads
        with patch("pathlib.Path.home", return_value=history_file.parent):
            new_history = OperationHistory()
            assert len(new_history._undo_stack) == 1
            assert new_history._undo_stack[0].type == OperationType.CREATE_DIR
            assert new_history._undo_stack[0].original_path == Path("/new_dir")

    def test_cleanup_old_history(self, tmp_path):
        # Create a dummy .tfm/history.pkl
        tfm_dir = tmp_path / ".tfm"
        tfm_dir.mkdir()
        old_pickle = tfm_dir / "history.pkl"
        old_pickle.touch()

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Instantiating OperationHistory should trigger cleanup
            OperationHistory()

            assert not old_pickle.exists()

    def test_clear(self, history):
        op = FileOperation(OperationType.RENAME, Path("/old"), Path("/new"))
        history.log_operation(op)
        history.clear()

        assert len(history._undo_stack) == 0
        assert len(history._redo_stack) == 0

    def test_empty_undo_redo(self, history):
        assert history.undo_last() is None
        assert history.redo_last() is None

    def test_log_clears_redo_stack(self, history):
        op1 = FileOperation(OperationType.COPY, Path("/1"), Path("/2"))
        history.log_operation(op1)
        history.undo_last()
        assert len(history._redo_stack) == 1

        op2 = FileOperation(OperationType.MOVE, Path("/3"), Path("/4"))
        history.log_operation(op2)
        assert len(history._redo_stack) == 0
        assert len(history._undo_stack) == 1
        assert history._undo_stack[0] == op2

    def test_corrupted_json(self, history, history_file):
        # Write corrupted JSON
        json_path = history_file.parent / ".tfm" / "history.json"
        json_path.write_text("{invalid json")

        with patch("pathlib.Path.home", return_value=history_file.parent):
            # Should not crash, just start empty
            h = OperationHistory()
            assert len(h._undo_stack) == 0
