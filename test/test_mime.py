import pytest
from outcome.eventkit import mime

invalid_mime_types = ['app', 'app/type/foo', 'app+suffix', 'application/json suffix']

valid_mime_types = {
    'application/json': {'type': 'application', 'subtype': 'json', 'suffix': None, 'parameters': {'charset': 'utf-8'}},
    'application/cloudevents+json': {
        'type': 'application',
        'subtype': 'cloudevents',
        'suffix': 'json',
        'parameters': {'charset': 'utf-8'},
    },
    'application/cloudevents+json; charset=latin9': {
        'type': 'application',
        'subtype': 'cloudevents',
        'suffix': 'json',
        'parameters': {'charset': 'latin9'},
    },
    'application/cloudevents+json; charset=latin9; param=otherKey': {
        'type': 'application',
        'subtype': 'cloudevents',
        'suffix': 'json',
        'parameters': {'charset': 'latin9', 'param': 'otherkey'},
    },
}


@pytest.fixture(params=invalid_mime_types)
def invalid_mime_type(request):
    return request.param


@pytest.fixture(params=valid_mime_types.keys())
def valid_mime_type(request):
    return (request.param, valid_mime_types[request.param])


def test_invalid_mime_type(invalid_mime_type):
    with pytest.raises(ValueError):
        mime.parse_mime_type(invalid_mime_type)


def test_valid_mime_type(valid_mime_type):
    mime_type, expected_output = valid_mime_type

    mt = mime.parse_mime_type(mime_type)

    for key, value in expected_output.items():
        assert getattr(mt, key) == value


class TestMIMEType:
    @pytest.mark.parametrize(
        'mime_type,name',
        [
            ('application/json', 'application/json;charset=utf-8'),
            ('application/JSON', 'application/json;charset=utf-8'),
            ('application/json ; param=value ; charset=latin9', 'application/json;charset=latin9;param=value'),
            ('application/json+suffix ; param=value ; charset=latin9', 'application/json+suffix;charset=latin9;param=value'),
        ],
    )
    def test_mime_type_name(self, mime_type, name):
        assert mime.parse_mime_type(mime_type).name == name

    def test_mime_type_name_no_charset(self):
        assert mime.parse_mime_type('application/json', default_charset=None).name == 'application/json'

    def test_charset(self):
        assert mime.parse_mime_type('application/json+suffix;charset=latin9').charset == 'latin9'

    @pytest.mark.parametrize(
        'left,right',
        [
            ('application/json', 'application/json;charset=utf-8'),
            ('application/JSON; param=value ; other=val', 'application/json;other=val  ; param=value'),
        ],
    )
    def test_mime_type_equality(self, left, right):
        assert mime.parse_mime_type(left) == mime.parse_mime_type(right)


class TestMIMETypeDict:
    def test_key_identity(self):
        d = mime.MIMETypeDict()

        d['application/json'] = 'bar'

        assert d['application/json;charset=utf-8'] == 'bar'
        assert d.keys() == {'application/json;charset=utf-8'}
