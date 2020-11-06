"""Basic tools to register event handlers and dispatch events."""

from collections import defaultdict
from typing import Callable, Dict, List

from outcome.eventkit.event import CloudEvent

CloudEventHandler = Callable[[CloudEvent], None]
CloudEventHandlerRegistry = Dict[str, List[CloudEventHandler]]

cloud_event_handler_registry: CloudEventHandlerRegistry = defaultdict(list)


def register_handler(
    event_type: str, handler: CloudEventHandler, registry: CloudEventHandlerRegistry = cloud_event_handler_registry,
) -> None:
    """Register a handler for an event type.

    Args:
        event_type (str): The event type
        handler (CloudEventHandler): The event handler.
        registry (CloudEventHandlerRegistry): The handler registry. Defaults to the global registry.
    """
    registry[event_type].append(handler)


def handles_events(*event_types: str, registry: CloudEventHandlerRegistry = cloud_event_handler_registry):
    """A decorator that registers the decorated function as a handler for the specified event types.

    Args:
        event_types (*str): The event types.
        registry (CloudEventHandlerRegistry): The handler registry. Defaults to the global registry.

    Returns:
        Callable[[CloudEventHandler], CloudEventHandler]: The decorator.
    """

    def handles_events_decorator(fn: CloudEventHandler) -> CloudEventHandler:
        for event_type in event_types:
            register_handler(event_type, fn, registry)

        return fn

    return handles_events_decorator


def dispatch(event: CloudEvent, registry: CloudEventHandlerRegistry = cloud_event_handler_registry) -> None:
    """Send an event to all of the registered handlers.

    Args:
        event (CloudEvent): The event to dispatch.
        registry (CloudEventHandlerRegistry): The handler registry. Defaults to the global registry.
    """
    for handler in cloud_event_handler_registry[event.type]:
        handler(event)
