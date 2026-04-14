import logging
from uuid import UUID

import grpc
from dishka import FromDishka
from dishka.integrations.grpcio import inject
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.places_pb2 import ROLE_ADMIN, ROLE_OWNER, ROLE_VIEWER
from placebrain_contracts.places_pb2_grpc import PlacesServiceServicer

from src.core.exceptions import AlreadyExistsError, NotFoundError, PermissionDeniedError
from src.infra.db.models.place_member import PlaceRole
from src.services.places import PlacesService

logger = logging.getLogger(__name__)

_ROLE_TO_PROTO = {
    PlaceRole.OWNER: ROLE_OWNER,
    PlaceRole.ADMIN: ROLE_ADMIN,
    PlaceRole.VIEWER: ROLE_VIEWER,
}

_PROTO_TO_ROLE = {v: k for k, v in _ROLE_TO_PROTO.items()}


class PlacesHandler(PlacesServiceServicer):
    @inject
    async def CreatePlace(  # type: ignore[override]
        self,
        request: places_pb.CreatePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.CreatePlaceResponse:
        logger.info("CreatePlace called by user: %s", request.user_id)
        place_id = await places_service.create_place(
            UUID(request.user_id), request.name, request.description
        )
        return places_pb.CreatePlaceResponse(place_id=place_id)

    @inject
    async def GetPlace(  # type: ignore[override]
        self,
        request: places_pb.GetPlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.GetPlaceResponse:
        logger.info("GetPlace called for place: %s", request.place_id)
        try:
            place = await places_service.get_place(UUID(request.user_id), UUID(request.place_id))
            return places_pb.GetPlaceResponse(
                place_id=str(place.id),
                name=place.name,
                description=place.description,
                user_role=_ROLE_TO_PROTO[place.role],
            )
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except NotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def ListPlaces(  # type: ignore[override]
        self,
        request: places_pb.ListPlacesRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.ListPlacesResponse:
        logger.info("ListPlaces called by user: %s", request.user_id)
        places = await places_service.list_places(UUID(request.user_id))
        return places_pb.ListPlacesResponse(
            places=[
                places_pb.PlaceSummary(
                    place_id=str(p.id),
                    name=p.name,
                    description=p.description,
                    user_role=_ROLE_TO_PROTO[p.role],
                )
                for p in places
            ]
        )

    @inject
    async def UpdatePlace(  # type: ignore[override]
        self,
        request: places_pb.UpdatePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.UpdatePlaceResponse:
        logger.info("UpdatePlace called for place: %s", request.place_id)
        try:
            place_id = await places_service.update_place(
                UUID(request.user_id),
                UUID(request.place_id),
                request.name,
                request.description,
            )
            return places_pb.UpdatePlaceResponse(place_id=place_id)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except NotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def DeletePlace(  # type: ignore[override]
        self,
        request: places_pb.DeletePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.DeletePlaceResponse:
        logger.info("DeletePlace called for place: %s", request.place_id)
        try:
            success = await places_service.delete_place(
                UUID(request.user_id), UUID(request.place_id)
            )
            return places_pb.DeletePlaceResponse(success=success)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except NotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def AddMember(  # type: ignore[override]
        self,
        request: places_pb.AddMemberRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.AddMemberResponse:
        logger.info("AddMember called for place: %s", request.place_id)
        try:
            role = _PROTO_TO_ROLE.get(request.role)
            if not role:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid role")
                raise ValueError("Invalid role")
            success = await places_service.add_member(
                UUID(request.user_id),
                UUID(request.place_id),
                UUID(request.target_user_id),
                role,
            )
            return places_pb.AddMemberResponse(success=success)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except AlreadyExistsError as e:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))
            raise

    @inject
    async def RemoveMember(  # type: ignore[override]
        self,
        request: places_pb.RemoveMemberRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.RemoveMemberResponse:
        logger.info("RemoveMember called for place: %s", request.place_id)
        try:
            success = await places_service.remove_member(
                UUID(request.user_id),
                UUID(request.place_id),
                UUID(request.target_user_id),
            )
            return places_pb.RemoveMemberResponse(success=success)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except NotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def UpdateMemberRole(  # type: ignore[override]
        self,
        request: places_pb.UpdateMemberRoleRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.UpdateMemberRoleResponse:
        logger.info("UpdateMemberRole called for place: %s", request.place_id)
        try:
            role = _PROTO_TO_ROLE.get(request.role)
            if not role:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid role")
                raise ValueError("Invalid role")
            success = await places_service.update_member_role(
                UUID(request.user_id),
                UUID(request.place_id),
                UUID(request.target_user_id),
                role,
            )
            return places_pb.UpdateMemberRoleResponse(success=success)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except NotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def ListMembers(  # type: ignore[override]
        self,
        request: places_pb.ListMembersRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> places_pb.ListMembersResponse:
        logger.info("ListMembers called for place: %s", request.place_id)
        try:
            members = await places_service.list_members(
                UUID(request.user_id), UUID(request.place_id)
            )
            return places_pb.ListMembersResponse(
                members=[
                    places_pb.MemberInfo(
                        user_id=str(m.user_id),
                        role=_ROLE_TO_PROTO[m.role],
                    )
                    for m in members
                ]
            )
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
