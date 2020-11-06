from unittest.mock import Mock, call

import pytest
from outcome.eventkit import CloudEvent
from outcome.eventkit.dispatch import cloud_event_handler_registry, dispatch, handles_events, register_handler


@pytest.fixture(autouse=True)
def reset_cloud_event_handler_registry():
    cloud_event_handler_registry.clear()


# This is to create a spec for the mocks
def handler(event: CloudEvent) -> None:
    ...


def test_handlers():
    m1 = Mock(spec_set=handler)
    m2 = Mock(spec_set=handler)
    m3 = Mock(spec_set=handler)

    register_handler('co.outcome.test', m1)
    register_handler('co.outcome.test', m2)
    register_handler('co.outcome.other', m3)

    ev = CloudEvent(type='co.outcome.test', source='test')

    dispatch(ev)

    m1.assert_called_once_with(ev)
    m2.assert_called_once_with(ev)
    m3.assert_not_called()


def test_handler_decorator():
    m1 = Mock(spec_set=handler)

    handles_events('co.outcome.test', 'co.outcome.test2')(m1)

    ev1 = CloudEvent(type='co.outcome.test', source='test')
    ev2 = CloudEvent(type='co.outcome.test2', source='test')

    dispatch(ev1)
    dispatch(ev2)

    assert m1.call_count == 2
    assert m1.mock_calls == [call(ev1), call(ev2)]
