# --------------------------------------------------------------------------- #
# Custom Exceptions
# --------------------------------------------------------------------------- #
class AppError(Exception):
    pass


class NotFound(AppError):
    pass


class AppValidationError(AppError):
    pass


class ConflictError(AppError):
    pass


class BusinessRuleError(AppError):
    pass
