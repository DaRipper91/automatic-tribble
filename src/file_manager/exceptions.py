"""
Custom exceptions for TFM.
"""

class TFMError(Exception):
    """Base exception for TFM errors."""
    pass

class TFMPermissionError(TFMError):
    """Raised when an operation fails due to insufficient permissions."""
    def __init__(self, path: str, message: str = "Permission denied"):
        self.path = path
        super().__init__(f"{message}: {path}")

class TFMPathNotFoundError(TFMError):
    """Raised when a required path does not exist."""
    def __init__(self, path: str, message: str = "Path not found"):
        self.path = path
        super().__init__(f"{message}: {path}")

class TFMOperationConflictError(TFMError):
    """Raised when an operation conflicts with existing state (e.g. file exists)."""
    def __init__(self, path: str, message: str = "Operation conflict"):
        self.path = path
        super().__init__(f"{message}: {path}")

class TFMConfigError(TFMError):
    """Raised when there is a configuration error."""
    pass
