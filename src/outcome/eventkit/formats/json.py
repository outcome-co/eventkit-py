"""An implementation of the CloudEvent JSON format."""

import base64
import json
from typing import Dict, Union

import pendulum
from outcome.eventkit.data import CloudEventData
from outcome.eventkit.event import CloudEvent
from outcome.eventkit.formats import CloudEventFormat
from outcome.eventkit.mime import parse_mime_type

content_type_name = parse_mime_type('application/cloudevents+json').name
json_content_type_name = parse_mime_type('application/json').name


class JSONCloudEventFormat(CloudEventFormat):
    @classmethod
    def encode(cls, event: CloudEvent) -> str:
        payload = event.attributes

        # According to the spec:
        #
        # If the event has data, but has no data content type, then it is assumed
        # that the content type is that of the envelope (in this case JSON).
        # https://github.com/cloudevents/spec/blob/v1.0/spec.md#datacontenttype (second to last paragraph)
        #
        # If the data content type is JSON, we don't encode the data, since it can
        # just be encoded with the rest of the envelope to form one JSON document.
        # https://github.com/cloudevents/spec/blob/v1.0/spec.md#type-system (last paragraph)
        if event.data:
            if event.data_content_type is None or event.data_content_type == json_content_type_name:
                payload['datacontenttype'] = json_content_type_name
                payload['data'] = event.data.data  # noqa: WPS204
            else:
                payload['data'] = event.data.encoded_data

        # If data is binary, we need to encode it and store it
        # in a separate field
        # https://github.com/cloudevents/spec/blob/v1.0/json-format.md#31-handling-of-data
        try:
            if isinstance(payload['data'], bytes):
                payload['data_base64'] = base64.b64encode(payload.pop('data')).decode('utf-8')

            # We handle key errors since data is optional
        except KeyError:
            pass

        try:
            # We use pendulum to ensure timezones are handled correctly
            payload['time'] = pendulum.instance(payload['time']).isoformat()
            # We handle key errors since timestamp is optional
        except KeyError:
            pass

        return json.dumps(payload)

    @classmethod
    def decode(cls, raw_event: Union[bytes, str]) -> CloudEvent:
        payload: Dict[str] = json.loads(raw_event)

        try:
            payload['data'] = base64.b64decode(payload.pop('data_base64')).decode('utf-8')  # noqa: WPS204
        except KeyError:
            pass

        # If we have data, we need to unpack it
        if payload.get('data') is not None:
            data_schema = payload.pop('dataschema', None)

            # if there was no content type, or it was JSON, it's already unpacked
            data_content_type = payload.pop('datacontenttype', json_content_type_name)
            if data_content_type == json_content_type_name:
                payload['data'] = CloudEventData(
                    data=payload['data'], data_content_type=json_content_type_name, data_schema=data_schema,
                )
            else:
                payload['data'] = CloudEventData.from_encoded(
                    payload['data'], data_content_type=data_content_type, data_schema=data_schema,
                )

        # Parse with pendulum to get the timezone right
        try:
            payload['time'] = pendulum.parse(payload['time'])
        except KeyError:
            pass

        return CloudEvent(**payload)


JSONCloudEventFormat.format_content_type = content_type_name
cloud_event_format = JSONCloudEventFormat
