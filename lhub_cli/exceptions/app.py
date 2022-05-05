from .base import LhCliBaseException


class BaseAppError(LhCliBaseException):
    """Base exception for failures from interacting with LogicHub itself, including custom HTTP errors"""
    message = "An application exception has occurred"

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message=message, *args, **kwargs)


class UnexpectedOutput(BaseAppError):
    """Authentication Failed"""
    message = "Unexpected output returned"

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message=message, *args, **kwargs)


class InvalidUserInput(BaseAppError):
    """Exception caused by user input"""
    message = "Invalid input from user"

    def __init__(self, input_var=None, message=None, *args, **kwargs):
        super().__init__(message=message, input_var=input_var, *args, **kwargs)


class PathNotFound(InvalidUserInput):
    """File path not found"""
    message = "File or directory not found"

    def __init__(self, path, message=None, *args, **kwargs):
        self.path = path
        super().__init__(message=message, input_var=path, *args, **kwargs)


class ColumnNotFound(InvalidUserInput):
    """Batch ID not found"""
    message = "Column not found"

    def __init__(self, column_name=None, message=None, *args, **kwargs):
        super().__init__(message=message, input_var=column_name, *args, **kwargs)


class UserGroupNotFound(InvalidUserInput):
    """User group not found"""
    message = "User group not found"

    def __init__(self, user_group, message=None, *args, **kwargs):
        super().__init__(message=message, input_var=user_group, *args, **kwargs)


class UserNotFound(InvalidUserInput):
    """User not found"""
    message = "User not found"

    def __init__(self, user, message=None, *args, **kwargs):
        super().__init__(message=message, input_var=user, *args, **kwargs)
