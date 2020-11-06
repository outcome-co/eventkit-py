"""An implementation of the CloudEvent spec."""

import datetime
import typing
import uuid

import pendulum
import pydantic
from outcome.eventkit.data import CloudEventData

non_empty_string = pydantic.constr(strip_whitespace=True, min_length=1)


def generate_event_id() -> str:
    return str(uuid.uuid4())


class CloudEventV1_0(pydantic.BaseModel):  # noqa: N801, WPS214
    """This is an implementation of the v1.0 cloud event spec.

    https://github.com/cloudevents/spec/blob/v1.0/spec.md
    """

    class Config:
        title = 'CloudEvent@V1.0'
        validate_all = True
        allow_population_by_field_name = False
        validate_assignment = True
        extra = pydantic.Extra.forbid

    # The event's unique ID
    id: non_empty_string = pydantic.Field(default_factory=generate_event_id)  # noqa: WPS125, A003
    # The event's origin
    source: non_empty_string

    # Hardcoded to 1.0
    spec_version: typing.Literal['1.0'] = pydantic.Field('1.0', alias='specversion')

    # The event type, used to provide semantic meaning to the event
    type: non_empty_string  # noqa: WPS125, A003

    @property
    def data_content_type(self) -> typing.Optional[str]:
        if self.data:
            return self.data.data_content_type
        return None

    @property
    def data_schema(self) -> typing.Optional[str]:
        if self.data:
            return self.data.data_schema
        return None

    subject: typing.Optional[non_empty_string] = None
    time: typing.Optional[datetime.datetime] = pydantic.Field(default_factory=pendulum.now)

    @pydantic.validator('time')
    def validate_time(cls, value) -> typing.Optional[datetime.datetime]:  # noqa: N805
        if value is None:
            return None
        return pendulum.instance(value)

    # Data in its decoded form, i.e. some object
    data: typing.Optional[CloudEventData] = None

    @pydantic.validator('data')
    def validate_data(cls, value, values) -> CloudEventData:  # noqa: N805
        if value is not None:
            value.validate_data()
        return value

    @property
    def attributes(self) -> typing.Dict[str, typing.Any]:
        non_attribute_keys = {'data'}
        attributes = {
            attr: value for attr, value in self.dict(by_alias=True, exclude_none=True).items() if attr not in non_attribute_keys
        }

        if self.data:
            if self.data.data_content_type is not None:
                attributes['datacontenttype'] = self.data.data_content_type
            if self.data.data_schema is not None:
                attributes['dataschema'] = self.data.data_schema

        return attributes


CloudEvent = CloudEventV1_0
