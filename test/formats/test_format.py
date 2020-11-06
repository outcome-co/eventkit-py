from outcome.eventkit.formats import CloudEventFormat


class DerivedFormatA(CloudEventFormat):
    ...


class DerivedFormatB(CloudEventFormat):
    ...


class DerivedFormatC(DerivedFormatB):
    ...


def test_assign_format_content_type():  # noqa: WPS218
    assert CloudEventFormat.format_content_type is None
    assert DerivedFormatA.format_content_type is None
    assert DerivedFormatB.format_content_type is None
    assert DerivedFormatC.format_content_type is None

    DerivedFormatB.format_content_type = 'application/json;charset=utf-8'

    assert CloudEventFormat.format_content_type is None
    assert DerivedFormatA.format_content_type is None
    assert DerivedFormatB.format_content_type == 'application/json;charset=utf-8'
    assert DerivedFormatC.format_content_type == 'application/json;charset=utf-8'

    DerivedFormatC.format_content_type = 'text/xml;charset=utf-8'

    assert CloudEventFormat.format_content_type is None
    assert DerivedFormatA.format_content_type is None
    assert DerivedFormatB.format_content_type == 'application/json;charset=utf-8'
    assert DerivedFormatC.format_content_type == 'text/xml;charset=utf-8'

    DerivedFormatB.format_content_type = None

    assert CloudEventFormat.format_content_type is None
    assert DerivedFormatA.format_content_type is None
    assert DerivedFormatB.format_content_type is None
    assert DerivedFormatC.format_content_type == 'text/xml;charset=utf-8'
