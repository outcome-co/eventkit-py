from outcome.eventkit.data import CloudEventData

sample_decoded_data = {'hello': 'world'}
sample_encoded_data = '{"hello": "world"}'


def test_encode():
    d = CloudEventData(data=sample_decoded_data, data_content_type='application/json')
    assert d.encoded_data == sample_encoded_data


def test_decode():
    d = CloudEventData.from_encoded(encoded_data=sample_encoded_data, data_content_type='application/json')
    assert d.data == sample_decoded_data
