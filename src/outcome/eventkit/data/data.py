"""A class to represent data that can be encoded."""

from typing import Any, Optional

import pydantic
from outcome.eventkit.data.coder import DataCoder, DecodedData, EncodedData
from outcome.eventkit.mime import parse_mime_type


class CloudEventData(pydantic.BaseModel):
    # What is the data payload's format?
    # This is a MIME type that can be used to retrieve the decoder/encoder/validator functions
    # It's important to note that the event's payload can be in a completely different format
    # to the rest of the event data. For example, the event can be sent in JSON format, with
    # the data payload being encoded as a B64 XML string inside the JSON

    class Config:
        validate_all = True
        validate_assignment = True
        extra = pydantic.Extra.forbid

    data_content_type: Optional[str] = None
    data_schema: Optional[str] = None

    # The data itself, in a decoded form
    data: DecodedData = None

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, CloudEventData):  # pragma: no cover
            return False

        return o.data == self.data and o.data_content_type == self.data_content_type and o.data_schema == self.data_schema

    @pydantic.validator('data_content_type')
    def validate_data_content_type(cls, value) -> str:  # noqa: N805
        if value is None:
            return None
        return parse_mime_type(value).name

    @property
    def encoded_data(self) -> EncodedData:
        if self.data is None:
            return None

        if self.data_content_type is None:
            raise ValueError('Cannot encode data without content type')

        coder = self.get_coder(self.data_content_type)

        return coder.encode(self.data, self.data_content_type)

    @classmethod
    def from_encoded(
        cls, encoded_data: EncodedData, data_content_type: str, data_schema: Optional[str] = None,
    ) -> 'CloudEventData':
        data_content_type = parse_mime_type(data_content_type).name
        coder = cls.get_coder(data_content_type)
        decoded_data = coder.decode(encoded_data, data_content_type)

        if data_schema:
            coder.validate(decoded_data, data_content_type, data_schema)

        return cls(data=decoded_data, data_content_type=data_content_type, data_schema=data_schema)

    @staticmethod
    def get_coder(data_content_type: str) -> DataCoder:  # noqa: WPS602
        try:
            return DataCoder.data_content_types[data_content_type]
        except KeyError:
            raise ValueError(f'Unknown content type {data_content_type}')

    def validate_data(self) -> None:
        if self.data_content_type:
            coder = self.get_coder(self.data_content_type)
            coder.validate(self.data, self.data_content_type, self.data_schema)
