from typing import AsyncIterable

from heekkr.resolver_pb2 import (
    GetLibrariesRequest,
    GetLibrariesResponse,
    SearchRequest,
    SearchResponse,
)
from heekkr.library_pb2 import Library
from heekkr.resolver_pb2_grpc import ResolverServicer

from .core import Library as ServiceLibrary, services


class Resolver(ResolverServicer):
    async def GetLibraries(
        self, request: GetLibrariesRequest, context
    ) -> GetLibrariesResponse:
        return GetLibrariesResponse(
            libraries=[
                convert_library(library, name)
                for name, service in services.items()
                for library in await service.get_libraries()
            ]
        )

    async def Search(
        self, request: SearchRequest, context
    ) -> AsyncIterable[SearchResponse]:
        library_ids = set(request.library_ids or ())
        service_ids = set(library_id.split(":")[0] for library_id in library_ids)
        for name, service in services.items():
            if name in service_ids:
                yield SearchResponse(
                    entities=[
                        entity
                        async for entity in service.search(
                            request.term,
                            (
                                library_id
                                for library_id in library_ids
                                if library_id.startswith(f"{name}:")
                            ),
                        )
                    ]
                )


def convert_library(lib: ServiceLibrary, name: str) -> Library:
    return Library(
        id=lib.id,
        name=lib.name,
        resolver_id=f"simple:{name}",
    )
