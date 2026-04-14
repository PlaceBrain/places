class PlacesServiceError(Exception):
    """Base for all places domain exceptions."""


class NotFoundError(PlacesServiceError): ...


class AlreadyExistsError(PlacesServiceError): ...


class PermissionDeniedError(PlacesServiceError): ...
