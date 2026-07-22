class DomainError(Exception):
    """Base class for application domain errors."""


class FileNotFound(DomainError):
    """Raised when a file record does not exist."""


class EmptyFile(DomainError):
    """Raised when an uploaded file has no content."""


class StoredFileNotFound(DomainError):
    """Raised when the on-disk artifact for a file record is missing."""


class FileTooLarge(DomainError):
    """Raised when an uploaded file exceeds the allowed size."""
