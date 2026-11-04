"""The framework for writing Micro services."""

from micro.errors import RemoteError, ServiceError
from micro.queue import WorkQueue

from ._client import Client
from ._event import DispatchSchema, EventSchema
from ._request import RequestSchema
from ._service import (
  DuplicateRequestHandlerError,
  DuplicateWorkHandlerError,
  EventHandler,
  EventPredicate,
  RequestHandler,
  Service,
)

__all__ = (
  "Client",
  "DispatchSchema",
  "DuplicateRequestHandlerError",
  "DuplicateWorkHandlerError",
  "EventHandler",
  "EventPredicate",
  "EventSchema",
  "RemoteError",
  "RequestHandler",
  "RequestSchema",
  "Service",
  "ServiceError",
  "WorkQueue",
)
