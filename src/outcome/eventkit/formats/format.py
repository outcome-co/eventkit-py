"""An abstract implementation of the CloudEvent format spec."""

from typing import ClassVar, Optional, Type, TypeVar, Union

from outcome.eventkit.event import CloudEvent
from outcome.eventkit.mime import MIMETypeDict, parse_mime_type

T = TypeVar('T')

CloudEventFormatMIMETypeDict = MIMETypeDict[Type['CloudEventFormat']]


class CloudEventFormatMeta(type):
    # Using a metaclass, we can implement class-level properties
    @property
    def format_content_type(cls) -> Optional[str]:  # noqa: N805
        try:
            return cls._format_content_type
        except AttributeError:
            return None

    @format_content_type.setter
    def format_content_type(cls, content_type: Optional[str]) -> None:  # noqa: N805
        if content_type:
            cls._format_content_type = parse_mime_type(content_type).name
        else:
            cls._format_content_type = None


class CloudEventFormat(metaclass=CloudEventFormatMeta):
    # The registry of all known format_content_types
    format_content_types: ClassVar[CloudEventFormatMIMETypeDict] = CloudEventFormatMIMETypeDict()

    @classmethod
    def encode(cls, event: CloudEvent) -> Union[bytes, str]:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def decode(cls, raw_event: Union[bytes, str]) -> CloudEvent:  # pragma: no cover
        raise NotImplementedError
