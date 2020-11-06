"""A bare-bones implementation of a JSON data payload coder."""

import json
from typing import Optional

from outcome.eventkit.data.coder import DataCoder, DecodedData, EncodedData


class JSONDataCoder(DataCoder):
    @classmethod
    def encode(cls, data: DecodedData, content_type: str) -> str:
        return json.dumps(data)

    @classmethod
    def decode(cls, encoded_data: EncodedData, content_type: str) -> DecodedData:
        return json.loads(encoded_data)

    @classmethod
    def validate(cls, data: DecodedData, content_type: str, schema_name: Optional[str]) -> None:  # pragma: no cover
        ...


content_type_name = 'application/json'
coder = JSONDataCoder
