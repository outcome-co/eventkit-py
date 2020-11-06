"""An abstract data encoder/decoder used to serialize the data payload."""

from typing import Any, ClassVar, Optional, Union

from outcome.eventkit.mime import MIMETypeDict

EncodedData = Optional[Union[str, bytes]]
DecodedData = Optional[Any]


class DataCoder:

    # This is a mapping of data payload content types to the class that can handle the data payload
    # Content types can be added to this dict
    data_content_types: ClassVar[MIMETypeDict['DataCoder']] = MIMETypeDict['DataCoder']()

    @classmethod
    def encode(cls, data: DecodedData, content_type: str) -> EncodedData:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def decode(cls, encoded_data: EncodedData, content_type: str) -> DecodedData:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def validate(cls, data: DecodedData, content_type: str, schema_name: Optional[str] = None) -> None:  # pragma: no cover
        raise NotImplementedError
