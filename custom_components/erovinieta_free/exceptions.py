"""Excepții pentru integrarea CNAIR eRovinieta Free."""


class ErovinietaError(Exception):
    """Excepție de bază."""


class ErovinietaApiError(ErovinietaError):
    """Eroare generală API."""


class ErovinietaAuthError(ErovinietaError):
    """Eroare de autentificare."""


class ErovinietaConnectionError(ErovinietaError):
    """Eroare de conexiune."""