class TeslaAppError(Exception):
    """Base application error."""


class TeslaAuthError(TeslaAppError):
    """Authentication/token related error."""


class TeslaPartnerAccountError(TeslaAppError):
    """Partner account related error."""


class TeslaOAuthError(TeslaAppError):
    """OAuth flow related error."""
