import asyncio
import logging

import grpc
from dishka import make_async_container
from dishka.integrations.grpcio import DishkaAioInterceptor
from placebrain_contracts.places_pb2_grpc import add_PlacesServiceServicer_to_server

from src.core.config import Settings
from src.dependencies.config import ConfigProvider
from src.dependencies.db import DBProvider
from src.dependencies.places import PlacesProvider
from src.handlers.places import PlacesHandler

logger = logging.getLogger(__name__)


async def serve() -> None:
    container = make_async_container(
        ConfigProvider(),
        DBProvider(),
        PlacesProvider(),
    )
    settings = await container.get(Settings)
    logging.basicConfig(
        level=settings.logging.level_value,
        format=settings.logging.format,
        datefmt=settings.logging.date_format,
    )
    server = grpc.aio.server(interceptors=[DishkaAioInterceptor(container)])
    add_PlacesServiceServicer_to_server(PlacesHandler(), server)
    server.add_insecure_port(f"[::]:{settings.app.port}")

    logger.info("Starting places service on port %s", settings.app.port)

    try:
        await server.start()
        await server.wait_for_termination()
    finally:
        await server.stop(grace=3)
        await container.close()


if __name__ == "__main__":
    asyncio.run(serve())
