from outcome.eventkit.data import CloudEventData
from outcome.eventkit.data import json as json_data_coder
from outcome.eventkit.data.coder import DataCoder
from outcome.eventkit.event import CloudEvent
from outcome.eventkit.formats import CloudEventFormat
from outcome.eventkit.formats import json as json_format

# Register known data content types
DataCoder.data_content_types[json_data_coder.content_type_name] = json_data_coder.coder


# Register known cloud event format types
CloudEventFormat.format_content_types[json_format.content_type_name] = json_format.cloud_event_format

__all__ = ['CloudEventData', 'CloudEvent']
