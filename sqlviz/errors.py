"""Custom exceptions for SQL visualization."""


class SQLVizError(Exception):
    """Base exception for SQL visualization errors."""

    pass


class UnsupportedSQLError(SQLVizError):
    """Raised when unsupported SQL syntax is detected."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ParseError(SQLVizError):
    """Raised when SQL parsing fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
