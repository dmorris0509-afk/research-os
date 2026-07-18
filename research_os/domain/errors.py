class DomainError(RuntimeError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class ExternalServiceError(DomainError):
    pass
