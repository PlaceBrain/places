import logging
from uuid import UUID

import grpc
from dishka import FromDishka
from dishka.integrations.grpcio import inject
from placebrain_contracts.places_pb2 import (
    AddMemberRequest,
    AddMemberResponse,
    CreatePlaceRequest,
    CreatePlaceResponse,
    DeletePlaceRequest,
    DeletePlaceResponse,
    GetPlaceRequest,
    GetPlaceResponse,
    ListMembersRequest,
    ListMembersResponse,
    ListPlacesRequest,
    ListPlacesResponse,
    MemberInfo,
    PlaceSummary,
    RemoveMemberRequest,
    RemoveMemberResponse,
    UpdateMemberRoleRequest,
    UpdateMemberRoleResponse,
    UpdatePlaceRequest,
    UpdatePlaceResponse,
)
from placebrain_contracts.places_pb2_grpc import PlacesServiceServicer

from src.infra.db.models.place_member import PlaceRole
from src.services.places import PlacesService

logger = logging.getLogger(__name__)

_ROLE_TO_PROTO = {
    PlaceRole.OWNER: 1,
    PlaceRole.ADMIN: 2,
    PlaceRole.VIEWER: 3,
}

_PROTO_TO_ROLE = {
    1: PlaceRole.OWNER,
    2: PlaceRole.ADMIN,
    3: PlaceRole.VIEWER,
}


class PlacesHandler(PlacesServiceServicer):
    @inject
    async def CreatePlace(  # type: ignore[override]
        self,
        request: CreatePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> CreatePlaceResponse:
        logger.info("CreatePlace called by user: %s", request.user_id)
        place_id = await places_service.create_place(
            UUID(request.user_id), request.name, request.description
        )
        return CreatePlaceResponse(place_id=place_id)

    @inject
    async def GetPlace(  # type: ignore[override]
        self,
        request: GetPlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> GetPlaceResponse:
        logger.info("GetPlace called for place: %s", request.place_id)
        try:
            place, role = await places_service.get_place(
                UUID(request.user_id), UUID(request.place_id)
            )
            return GetPlaceResponse(
                place_id=str(place.id),
                name=place.name,
                description=place.description,
                user_role=_ROLE_TO_PROTO[role],
            )
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def ListPlaces(  # type: ignore[override]
        self,
        request: ListPlacesRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> ListPlacesResponse:
        logger.info("ListPlaces called by user: %s", request.user_id)
        places = await places_service.list_places(UUID(request.user_id))
        return ListPlacesResponse(
            places=[
                PlaceSummary(
                    place_id=str(place.id),
                    name=place.name,
                    description=place.description,
                    user_role=_ROLE_TO_PROTO[role],
                )
                for place, role in places
            ]
        )

    @inject
    async def UpdatePlace(  # type: ignore[override]
        self,
        request: UpdatePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> UpdatePlaceResponse:
        logger.info("UpdatePlace called for place: %s", request.place_id)
        try:
            place_id = await places_service.update_place(
                UUID(request.user_id),
                UUID(request.place_id),
                request.name,
                request.description,
            )
            return UpdatePlaceResponse(place_id=place_id)
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def DeletePlace(  # type: ignore[override]
        self,
        request: DeletePlaceRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> DeletePlaceResponse:
        logger.info("DeletePlace called for place: %s", request.place_id)
        try:
            success = await places_service.delete_place(
                UUID(request.user_id), UUID(request.place_id)
            )
            return DeletePlaceResponse(success=success)
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def AddMember(  # type: ignore[override]
        self,
        request: AddMemberRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> AddMemberResponse:
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
            return AddMemberResponse(success=success)
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(e))
            raise

    @inject
    async def RemoveMember(  # type: ignore[override]
        self,
        request: RemoveMemberRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> RemoveMemberResponse:
        logger.info("RemoveMember called for place: %s", request.place_id)
        try:
            success = await places_service.remove_member(
                UUID(request.user_id),
                UUID(request.place_id),
                UUID(request.target_user_id),
            )
            return RemoveMemberResponse(success=success)
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def UpdateMemberRole(  # type: ignore[override]
        self,
        request: UpdateMemberRoleRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> UpdateMemberRoleResponse:
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
            return UpdateMemberRoleResponse(success=success)
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
        except ValueError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            raise

    @inject
    async def ListMembers(  # type: ignore[override]
        self,
        request: ListMembersRequest,
        context: grpc.aio.ServicerContext,
        places_service: FromDishka[PlacesService],
    ) -> ListMembersResponse:
        logger.info("ListMembers called for place: %s", request.place_id)
        try:
            members = await places_service.list_members(
                UUID(request.user_id), UUID(request.place_id)
            )
            return ListMembersResponse(
                members=[
                    MemberInfo(
                        user_id=str(m.user_id),
                        role=_ROLE_TO_PROTO[m.role],
                    )
                    for m in members
                ]
            )
        except PermissionError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            raise
