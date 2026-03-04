import pytest
from pathlib import Path
from src.file_manager.file_operations import OperationHistory, FileOperation, OperationType

class TestOperationHistory:

    @pytest.fixture
    def history_file(self, tmp_path):
        return tmp_path / "history.json"

    @pytest.fixture
    def history(self):
        h = OperationHistory()
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
