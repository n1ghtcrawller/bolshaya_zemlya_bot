class BotError(Exception):
    """Base exception for application-level errors."""


class UserNotFoundError(BotError):
    pass


class InvalidRoleError(BotError):
    pass


class N8nUnavailableError(BotError):
    pass


class BitrixUnavailableError(BotError):
    pass
