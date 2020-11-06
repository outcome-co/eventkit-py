from typing import Optional

import pendulum
import pytest
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.data.coder import DataCoder, DecodedData, EncodedData, MIMETypeDict
from outcome.eventkit.event import CloudEvent
from outcome.eventkit.formats import CloudEventFormat

JSONCloudEventFormat = CloudEventFormat.format_content_types['application/cloudevents+json']


def test_encode_no_data():
    ce = CloudEvent(
        type='co.outcome.type',
        source='test',
        id='c6cc55e8-3bf6-4fd5-9271-43116b03ee27',
        time=pendulum.datetime(2020, 11, 4),  # noqa: WPS432
    )
    encoded = JSONCloudEventFormat.encode(ce)

    assert (
        encoded
        == '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "time": "2020-11-04T00:00:00+00:00"}'  # noqa: E501
    )


def test_encode_no_timestamp():
    ce = CloudEvent(type='co.outcome.type', source='test', id='c6cc55e8-3bf6-4fd5-9271-43116b03ee27', time=None)
    encoded = JSONCloudEventFormat.encode(ce)

    assert (
        encoded
        == '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type"}'
    )


def test_encode_json_data():
    cd = CloudEventData(data_content_type='application/json', data={'hello': 'world'})
    ce = CloudEvent(type='co.outcome.type', source='test', id='c6cc55e8-3bf6-4fd5-9271-43116b03ee27', time=None, data=cd)
    encoded = JSONCloudEventFormat.encode(ce)

    assert (
        encoded
        == '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "datacontenttype": "application/json;charset=utf-8", "data": {"hello": "world"}}'  # noqa: E501
    )


class StringCoder(DataCoder):
    @classmethod
    def encode(cls, data: DecodedData, content_type: str) -> EncodedData:
        return 'a string'

    @classmethod
    def validate(cls, data: DecodedData, content_type: str, schema_name: Optional[str]) -> None:
        ...


class BinaryCoder(DataCoder):
    @classmethod
    def encode(cls, data: DecodedData, content_type: str) -> EncodedData:
        return b'some bytes'

    @classmethod
    def decode(cls, encoded_data: EncodedData, content_type: str) -> DecodedData:
        return 'some decoded bytes'

    @classmethod
    def validate(cls, data: DecodedData, content_type: str, schema_name: Optional[str]) -> None:
        ...


@pytest.fixture
def test_encoders():
    original_encoders = DataCoder.data_content_types
    DataCoder.data_content_types = MIMETypeDict[DataCoder]()

    DataCoder.data_content_types['application/test+string'] = StringCoder
    DataCoder.data_content_types['application/test+binary'] = BinaryCoder

    yield

    DataCoder.data_content_types = original_encoders


@pytest.mark.usefixtures('test_encoders')
def test_encode_non_json_str_data():
    cd = CloudEventData(data_content_type='application/test+string', data='hello')
    ce = CloudEvent(type='co.outcome.type', source='test', id='c6cc55e8-3bf6-4fd5-9271-43116b03ee27', time=None, data=cd)
    encoded = JSONCloudEventFormat.encode(ce)

    assert (
        encoded
        == '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "datacontenttype": "application/test+string;charset=utf-8", "data": "a string"}'  # noqa: E501
    )


@pytest.mark.usefixtures('test_encoders')
def test_encode_non_json_binary_data():
    cd = CloudEventData(data_content_type='application/test+binary', data='hello')
    ce = CloudEvent(type='co.outcome.type', source='test', id='c6cc55e8-3bf6-4fd5-9271-43116b03ee27', time=None, data=cd)
    encoded = JSONCloudEventFormat.encode(ce)

    assert (
        encoded
        == '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "datacontenttype": "application/test+binary;charset=utf-8", "data_base64": "c29tZSBieXRlcw=="}'  # noqa: E501
    )


def test_decode_no_data():
    raw = '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "time": "2020-11-04T00:00:00+00:00"}'  # noqa: E501

    ce = JSONCloudEventFormat.decode(raw)

    assert ce.id == 'c6cc55e8-3bf6-4fd5-9271-43116b03ee27'
    assert ce.source == 'test'
    assert ce.type == 'co.outcome.type'
    assert ce.time == pendulum.datetime(2020, 11, 4)  # noqa: WPS432
    assert ce.data is None


@pytest.mark.usefixtures('test_encoders')
def test_decode_non_json_data():
    raw = '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "datacontenttype": "application/test+binary;charset=utf-8", "data_base64": "c29tZSBieXRlcw=="}'  # noqa: E501

    ce = JSONCloudEventFormat.decode(raw)

    assert ce.data.data_schema is None
    assert ce.data.data_content_type == 'application/test+binary;charset=utf-8'
    assert ce.data.data == 'some decoded bytes'


def test_decode_json_data():
    raw = '{"id": "c6cc55e8-3bf6-4fd5-9271-43116b03ee27", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "datacontenttype": "application/json;charset=utf-8", "data": {"hello": "world"}}'  # noqa: E501

    ce = JSONCloudEventFormat.decode(raw)

    assert ce.data.data_schema is None
    assert ce.data.data_content_type == 'application/json;charset=utf-8'
    assert ce.data.data == {'hello': 'world'}
