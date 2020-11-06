"""Tools to build HTTP messages from CloudEvents."""

import re
import urllib
from typing import Any, Dict, List, Optional, Type, Union, cast

import pendulum
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.event import CloudEvent
from outcome.eventkit.formats import CloudEventFormat
from outcome.eventkit.mime import parse_mime_type
from requests.structures import CaseInsensitiveDict
from requests.utils import check_header_validity

HeaderDict = Dict[str, str]


_header_attribute_prefix = 'ce-'
_header_attribute_prefix_pattern = r'^ce-'

_content_type_header = 'Content-Type'


class HTTPEvent:
    """A basic container for HTTP headers and a body."""

    headers: HeaderDict
    body: Optional[Union[bytes, str]]

    def __init__(self, body: Optional[Union[bytes, str]] = None, headers: Optional[HeaderDict] = None) -> None:
        self.headers: HeaderDict = CaseInsensitiveDict(headers or {})
        self.body = body


def attributes_to_headers(attributes: Dict[str, Any]) -> HeaderDict:
    """Constructs a header dict from the attributes of an event.

    `data` and `datacontenttype` are excluded.

    Args:
        attributes (Dict[str, Any]): The event attributes.

    Returns:
        HeaderDict: The header dict.
    """
    exclude_from_headers = {'datacontenttype'}

    headers = CaseInsensitiveDict()

    for attr, value in attributes.items():
        if attr not in exclude_from_headers:
            # Time is the only attribute in the spec that isn't represented
            # by a python str-like object
            if attr == 'time':
                value = pendulum.instance(value).isoformat()

            header = f'{_header_attribute_prefix}{attr.lower()}'

            check_header_validity((header, value))

            headers[header] = value

    return headers


# Method to attempt to parse a cloud event from either a binary or structured HTTP message
def from_http(http_event: HTTPEvent) -> CloudEvent:
    if looks_like_binary(http_event):
        return BinaryHTTPBinding.from_http(http_event)

    return StructuredHTTPBinding.from_http(http_event)


def looks_like_binary(http_event: HTTPEvent) -> bool:
    # Not an exact science, but we can check for some headers
    expected_headers = {'Content-Type', 'ce-specversion', 'ce-id', 'ce-type', 'ce-source'}

    # We can't use set intersection, since http_event.headers does additional case-insensitive checking
    if not all(header in http_event.headers for header in expected_headers):
        return False

    # The presence of the headers is not sufficient, since structured HTTP bindings can also contain the
    # headers, instead we must check the Content-Type header to ensure it's not of the type application/cloudevents
    # which is mandated by the spec
    content_type = parse_mime_type(http_event.headers['Content-Type'])

    return not (content_type.type == 'application' and content_type.subtype == 'cloudevents')


class BinaryHTTPBinding:
    """Creates a HTTP message in binary format.

    - Event `datacontenttype` is mapped to `Content-Type`
    - Other event attributes are mapped to HTTP headers, prefixed with `ce-`
    - Event data is serialized and used as the HTTP body

    See more at https://github.com/cloudevents/spec/blob/v1.0/http-protocol-binding.md#31-binary-content-mode
    """

    @staticmethod
    def to_http(event: CloudEvent) -> HTTPEvent:  # noqa: WPS602
        if event.data is not None and event.data_content_type is None:
            raise ValueError('Cannot construct a binary HTTP message from an event without a data content type')

        headers = attributes_to_headers(event.attributes)
        body = None

        if event.data:
            headers[_content_type_header] = event.data_content_type
            body = event.data.encoded_data

        return HTTPEvent(body, headers)

    @staticmethod
    def from_http(http_event: HTTPEvent) -> CloudEvent:  # noqa: WPS602
        # We don't want to add data_schema as an attribute of the event itself
        # since its attached to the CloudEventData instance instead
        excluded_attributes = {'ce-dataschema'}

        # We want to ignore case, since we don't know what case we're dealing with
        attributes = {
            re.sub(_header_attribute_prefix_pattern, '', attr, flags=re.I): urllib.parse.unquote(value)
            for attr, value in http_event.headers.items()
            if attr.lower().startswith(_header_attribute_prefix) and attr.lower() not in excluded_attributes
        }

        data = None
        data_content_type = http_event.headers.get(_content_type_header)
        data_schema = http_event.headers.get('ce-dataschema')

        if http_event.body is not None:
            if data_content_type is None:
                raise ValueError('Cannot create event from binary HTTP message without a Content-Type header')

            coder = CloudEventData.get_coder(data_content_type)
            decoded_data = coder.decode(http_event.body, data_content_type)

            data = CloudEventData(data=decoded_data, data_content_type=data_content_type, data_schema=data_schema)

        if data is None and (data_content_type or data_schema):
            data = CloudEventData(data_content_type=data_content_type, data_schema=data_schema)

        return CloudEvent(**{'data': data, **attributes})


class StructuredHTTPBinding:
    """Creates a structured HTTP message.

    The entire event is transmitted in the HTTP body.
    The provided `event_format` determines how the event is serialized.
    """

    @staticmethod
    def to_http(  # noqa: WPS602
        event: CloudEvent, event_format: Type[CloudEventFormat], include_attributes_in_headers: bool = False,
    ) -> HTTPEvent:

        if event_format.format_content_type is None:  # pragma: no cover
            raise ValueError('Event format needs to specify a content type')

        if include_attributes_in_headers:
            headers = attributes_to_headers(event.attributes)
        else:
            headers = cast(HeaderDict, CaseInsensitiveDict())

        headers[_content_type_header] = event_format.format_content_type
        body = event_format.encode(event)

        return HTTPEvent(body, headers)

    @staticmethod
    def from_http(http_event: HTTPEvent) -> List[CloudEvent]:  # noqa: WPS602
        try:
            format_content_type = http_event.headers[_content_type_header]
        except KeyError:
            raise ValueError('The HTTP event does not contain a content-type')

        try:
            event_format = CloudEventFormat.format_content_types[format_content_type]
        except KeyError:
            raise ValueError(f'Unknown format content type {format_content_type}')

        return event_format.decode(http_event.body)
