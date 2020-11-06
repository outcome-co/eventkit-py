import pendulum
import pytest
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.event import CloudEvent
from outcome.eventkit.formats.json import JSONCloudEventFormat
from outcome.eventkit.protocol_bindings import http


@pytest.fixture
def event():
    return CloudEvent(
        id='0870f425-c26f-44af-a0e0-be469e9aa305',
        type='co.outcome.type',
        source='test',
        subject='subject?',
        time=pendulum.datetime(year=2020, month=11, day=5),  # noqa: WPS432
    )


@pytest.fixture
def event_with_data(event):
    event.data = CloudEventData(data_content_type='application/json', data={'hello': 'world'}, data_schema='schema')
    return event


@pytest.fixture
def expected_headers():
    return {
        'ce-id': '0870f425-c26f-44af-a0e0-be469e9aa305',
        'ce-source': 'test',
        'ce-specversion': '1.0',
        'ce-type': 'co.outcome.type',
        'ce-subject': 'subject?',
        'ce-time': '2020-11-05T00:00:00+00:00',
    }


def test_attributes_to_headers(event_with_data, expected_headers):
    headers = http.attributes_to_headers({**event_with_data.attributes})

    # We need to convert it to a dict, since the underlying implementation
    # is a dict-like structure that doesn't handle equality
    assert dict(headers) == {**expected_headers, 'ce-dataschema': 'schema'}


@pytest.fixture
def http_event(expected_headers):
    return http.HTTPEvent(headers=expected_headers)


class TestBinaryBinding:
    def test_to_http(self, event_with_data, expected_headers):
        http_event = http.BinaryHTTPBinding.to_http(event_with_data)

        assert dict(http_event.headers) == {
            **expected_headers,
            'Content-Type': 'application/json;charset=utf-8',
            'ce-dataschema': 'schema',
        }
        assert http_event.body == '{"hello": "world"}'

    def test_to_http_no_data(self, event, expected_headers):
        http_event = http.BinaryHTTPBinding.to_http(event)

        assert dict(http_event.headers) == expected_headers
        assert http_event.body is None

    def test_to_http_no_data_content_type(self, event_with_data):
        event_with_data.data.data_content_type = None

        with pytest.raises(ValueError):
            http.BinaryHTTPBinding.to_http(event_with_data)

    def test_from_http_no_data(self, http_event, event):
        received_event = http.BinaryHTTPBinding.from_http(http_event)

        assert event == received_event

    @pytest.mark.parametrize(
        'meta', [(('data_schema', 'ce-dataschema', 'schema')), (('data_content_type', 'Content-Type', 'application/json'))],
    )
    def test_from_http_no_data_with_data_meta(self, http_event, event, meta):
        prop, prop_header, value = meta

        data = CloudEventData(**{prop: value})
        event.data = data

        http_event.headers[prop_header] = value

        received_event = http.BinaryHTTPBinding.from_http(http_event)

        assert event == received_event

    def test_from_http(self, http_event, event_with_data):
        http_event.body = '{"hello": "world"}'
        http_event.headers['Content-Type'] = 'application/json'
        http_event.headers['ce-dataschema'] = 'schema'

        received_event = http.BinaryHTTPBinding.from_http(http_event)

        assert event_with_data == received_event

    def test_from_http_missing_content_type(self, http_event):
        http_event.body = '{"hello": "world"}'
        http_event.headers['ce-dataschema'] = 'schema'

        with pytest.raises(ValueError):
            http.BinaryHTTPBinding.from_http(http_event)


class TestStructuredBinding:
    def test_to_http(self, event_with_data):
        http_event = http.StructuredHTTPBinding.to_http(event_with_data, JSONCloudEventFormat)

        assert dict(http_event.headers) == {'Content-Type': JSONCloudEventFormat.format_content_type}
        assert (
            http_event.body
            == '{"id": "0870f425-c26f-44af-a0e0-be469e9aa305", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "subject": "subject?", "time": "2020-11-05T00:00:00+00:00", "datacontenttype": "application/json;charset=utf-8", "dataschema": "schema", "data": {"hello": "world"}}'  # noqa: E501
        )

    def test_to_http_include_headers(self, event_with_data, expected_headers):
        http_event = http.StructuredHTTPBinding.to_http(event_with_data, JSONCloudEventFormat, include_attributes_in_headers=True)

        assert dict(http_event.headers) == {
            **expected_headers,
            'Content-Type': JSONCloudEventFormat.format_content_type,
            'ce-dataschema': 'schema',
        }
        assert (
            http_event.body
            == '{"id": "0870f425-c26f-44af-a0e0-be469e9aa305", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "subject": "subject?", "time": "2020-11-05T00:00:00+00:00", "datacontenttype": "application/json;charset=utf-8", "dataschema": "schema", "data": {"hello": "world"}}'  # noqa: E501
        )

    def test_from_http(self, event_with_data):
        body = '{"id": "0870f425-c26f-44af-a0e0-be469e9aa305", "source": "test", "specversion": "1.0", "type": "co.outcome.type", "subject": "subject?", "time": "2020-11-05T00:00:00+00:00", "datacontenttype": "application/json;charset=utf-8", "dataschema": "schema", "data": {"hello": "world"}}'  # noqa: E501

        http_event = http.HTTPEvent(body=body, headers={'Content-Type': JSONCloudEventFormat.format_content_type})

        event = http.StructuredHTTPBinding.from_http(http_event)

        assert event == event_with_data

    def test_from_http_missing_header(self):
        http_event = http.HTTPEvent()
        with pytest.raises(ValueError):
            http.StructuredHTTPBinding.from_http(http_event)

    def test_from_http_unknown_content_type(self):
        http_event = http.HTTPEvent(headers={'Content-Type': 'text/xml'})
        with pytest.raises(ValueError):
            http.StructuredHTTPBinding.from_http(http_event)


def test_looks_like_binary_true_binary(event_with_data):
    http_event = http.BinaryHTTPBinding.to_http(event_with_data)
    assert http.looks_like_binary(http_event)


def test_looks_like_binary_structured_no_headers(event_with_data):
    http_event = http.StructuredHTTPBinding.to_http(event_with_data, JSONCloudEventFormat)
    assert not http.looks_like_binary(http_event)


def test_looks_like_binary_structured_with_headers(event_with_data):
    http_event = http.StructuredHTTPBinding.to_http(event_with_data, JSONCloudEventFormat, include_attributes_in_headers=True)
    assert not http.looks_like_binary(http_event)


def test_from_http_structured(event_with_data):
    http_event = http.StructuredHTTPBinding.to_http(event_with_data, JSONCloudEventFormat)
    event = http.from_http(http_event)
    assert event == event_with_data


def test_from_http_binary(event_with_data):
    http_event = http.BinaryHTTPBinding.to_http(event_with_data)
    event = http.from_http(http_event)
    assert event == event_with_data
