from dishka import Provider, Scope, provide

from src.infra.db.uow import UnitOfWork
from src.services.places import PlacesService


class PlacesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_places_service(self, uow: UnitOfWork) -> PlacesService:
        return PlacesService(uow)
