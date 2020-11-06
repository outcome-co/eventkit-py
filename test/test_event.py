import datetime

import pydantic
import pytest
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.event import CloudEvent


def test_required_fields():
    with pytest.raises(pydantic.ValidationError) as ex:
        CloudEvent()

    required_fields = {e['loc'][0] for e in ex.value.errors() if e['type'] == 'value_error.missing'}  # noqa: WPS441

    assert required_fields == {'type', 'source'}

    with pytest.raises(pydantic.ValidationError):
        CloudEvent(type='  ', source='')


def test_required_id():
    ce = CloudEvent(type='co.outcome.type', source='test')

    assert ce.id is not None
    with pytest.raises(pydantic.ValidationError):
        ce.id = None  # noqa: WPS125


def test_fixed_spec_version():
    ce = CloudEvent(type='co.outcome.type', source='test')

    assert ce.spec_version == '1.0'

    with pytest.raises(pydantic.ValidationError):
        ce.spec_version = '1.1'


def test_default_time():
    ce = CloudEvent(type='co.outcome.type', source='test')
    assert isinstance(ce.time, datetime.datetime)


def test_no_data():
    ce = CloudEvent(type='co.outcome.type', source='test')

    assert ce.data_content_type is None
    assert ce.data is None
    assert ce.data_schema is None


def test_data():
    cd = CloudEventData(data_content_type='application/json', data_schema='schema', data={'hello': 'world'})
    ce = CloudEvent(type='co.outcome.type', source='test', data=cd)

    assert ce.data_content_type == 'application/json;charset=utf-8'
    assert ce.data == cd
    assert ce.data_schema == 'schema'


def test_attributes():
    cd = CloudEventData(data_content_type='application/json', data_schema='schema', data={'hello': 'world'})
    ce = CloudEvent(type='co.outcome.type', source='test', data=cd, subject='subject')

    attributes = ce.attributes

    assert attributes['datacontenttype'] == cd.data_content_type
    assert attributes['dataschema'] == cd.data_schema

    assert set(attributes.keys()) == {'time', 'type', 'source', 'id', 'specversion', 'subject', 'dataschema', 'datacontenttype'}


def test_attributes_no_data():
    ce = CloudEvent(type='co.outcome.type', source='test', subject='subject')
    attributes = ce.attributes
    assert set(attributes.keys()) == {'time', 'type', 'source', 'id', 'specversion', 'subject'}


@pytest.mark.parametrize(
    'data,attr',
    [
        (CloudEventData(data_content_type='application/json'), 'datacontenttype'),
        (CloudEventData(data_schema='schema'), 'dataschema'),
    ],
)
def test_attributes_partial_data(data, attr):
    ce = CloudEvent(type='co.outcome.type', source='test', subject='subject', data=data)
    attributes = ce.attributes
    assert set(attributes.keys()) == {'time', 'type', 'source', 'id', 'specversion', 'subject', attr}
