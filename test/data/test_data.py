from unittest.mock import Mock

import pytest
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.data.coder import DataCoder
from outcome.eventkit.mime import MIMETypeDict, parse_mime_type

mock_mime = 'application/mock+mime'
canonical_mime = parse_mime_type(mock_mime).name


@pytest.fixture()
def reset_coders():
    original_coders = DataCoder.data_content_types
    DataCoder.data_content_types = MIMETypeDict[DataCoder]()

    mock_coder = Mock(spec_set=DataCoder)
    DataCoder.data_content_types[mock_mime] = mock_coder

    yield mock_coder

    DataCoder.data_content_types = original_coders


def test_normalize_content_type():
    d = CloudEventData(data_content_type='application/json')
    assert d.data_content_type == 'application/json;charset=utf-8'


def test_get_coder(reset_coders):
    assert CloudEventData.get_coder(mock_mime) == reset_coders


def test_get_unknown_coder():
    with pytest.raises(ValueError):
        CloudEventData.get_coder('unknown/mime')


def test_encoded_data_no_data_type():
    d = CloudEventData(data='somedata')

    with pytest.raises(ValueError):
        d.encoded_data


def test_encoded_data_none():
    d = CloudEventData()
    assert d.encoded_data is None


def test_encoded_data(reset_coders: Mock):
    reset_coders.encode.return_value = 'encodeddata'

    data = 'somedata'

    d = CloudEventData(data=data, data_content_type=mock_mime)
    ed = d.encoded_data

    assert ed == 'encodeddata'
    reset_coders.encode.assert_called_once_with(data, canonical_mime)


def test_from_encoded_no_schema(reset_coders: Mock):
    reset_coders.decode.return_value = 'somedata'

    instance = CloudEventData.from_encoded(encoded_data='encodeddata', data_content_type=mock_mime)

    assert instance.data == 'somedata'
    reset_coders.decode.assert_called_once_with('encodeddata', canonical_mime)
    reset_coders.validate.assert_not_called()


def test_from_encoded_with_schema(reset_coders: Mock):
    reset_coders.decode.return_value = 'somedata'

    instance = CloudEventData.from_encoded(encoded_data='encodeddata', data_content_type=mock_mime, data_schema='schema')

    assert instance.data == 'somedata'
    reset_coders.decode.assert_called_once_with('encodeddata', canonical_mime)
    reset_coders.validate.assert_called_once_with('somedata', canonical_mime, 'schema')


def test_validate(reset_coders: Mock):
    d = CloudEventData(data='somedata', data_content_type=mock_mime, data_schema='schema')
    d.validate_data()

    reset_coders.validate.assert_called_once_with('somedata', canonical_mime, 'schema')
