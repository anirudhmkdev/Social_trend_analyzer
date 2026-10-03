class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(f"{entity_name} with id {entity_id} not found", status_code=404)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
