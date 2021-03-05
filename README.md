# eventkit-py
![ci-badge](https://github.com/outcome-co/eventkit-py/workflows/Release/badge.svg?branch=v0.3.2) ![version-badge](https://img.shields.io/badge/version-0.3.2-brightgreen)

A toolkit for emitting and handling events, following the CloudEvent spec.

## Installation

```sh
poetry add outcome-eventkit
```

## Usage

It's a good idea to be familiar with the [CloudEvent v1.0 spec](https://github.com/cloudevents/spec/blob/v1.0/spec.md) before using this library.

The library implements the following (but is extensible):

- [The Core Event object](https://github.com/cloudevents/spec/blob/v1.0/spec.md)
- [A JSON formatter](https://github.com/cloudevents/spec/blob/v1.0/json-format.md)
- [The HTTP Protocol Bindings (Structured and Binary)](https://github.com/cloudevents/spec/blob/v1.0/http-protocol-binding.md)

### Event Example
```py
from outcome.eventkit import CloudEvent, CloudEventData
from outcome.eventkit.formats.json import JSONCloudEventFormat
from outcome.eventkit.protocol_bindings.http import StructuredHTTPBinding, BinaryHTTPBinding

import requests

# Create a payload, specifying how it will be encoded
data = CloudEventData(
    data_content_type='application/json',
    data={
        'hello': 'world'
    }
)

# Create an event
event = CloudEvent(type='co.outcome.events.sample', source='example', data=data)

# Create a JSON representation of the event
serialised_event = JSONCloudEventFormat.encode(event)

# Or...

# Create a HTTP message with the event
http_message = BinaryHTTPBinding.to_http(event)

# Or...

# Create a structured HTTP message with the event and a JSON formatter
http_message = StructuredHTTPBinding.to_http(event, JSONCloudEventFormat)

# Post the event somewhere...
requests.post('http://example.org', headers=http_message.headers, data=http_message.body)
```

### Dispatch Example
```py
from outcome.eventkit import dispatch, CloudEvent

# You can register event handlers that will be called
# when a corresponding event is dispatched

# Explicitly
def my_event_handler(event: CloudEvent) -> None:
    ...

# Register a handler for an event type
dispatch.register_handler('co.outcome.event', my_event_handler)


# Or via a decorator
@dispatch.handles_events('co.outcome.event', 'co.outcome.other-event')
def my_other_handler(event: CloudEvent) -> None:
    ...


# Then notify all registered handlers of an event
ev = CloudEvent(type='co.outcome.event', source='example')
dispatch.dispatch(ev)
```

By default, all handlers are stored in a single registry, but you can provide your own registry to the `register_handler`/`handles_events`/`dispatch` methods with the `registry` keyword argument.

```py
from outcome.eventkit import dispatch
from collections import defaultdict

my_registry: dispatch.CloudEventHandlerRegistry = defaultdict(list)

@dispatch.handles_events('co.outcome.event', registry=my_registry)
def my_handler(event: CloudEvent) -> None:
    ...

ev = CloudEvent(type='co.outcome.event', source='example')
dispatch.dispatch(ev, registry=my_registry)
```

## Development

Remember to run `./pre-commit.sh` when you clone the repository.
