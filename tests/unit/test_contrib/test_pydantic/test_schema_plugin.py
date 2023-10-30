from typing import Dict, Generic, Optional, Type, TypeVar, Union

import pydantic as pydantic_v2
import pytest
from pydantic.v1.generics import GenericModel
from typing_extensions import Annotated

from litestar._openapi.schema_generation.schema import (
    SchemaCreator,
    _get_type_schema_name,
)
from litestar.contrib.pydantic.pydantic_schema_plugin import PydanticSchemaPlugin
from litestar.openapi.spec import OpenAPIType
from litestar.openapi.spec.schema import Schema
from litestar.typing import FieldDefinition
from litestar.utils.helpers import get_name

T = TypeVar("T")


class PydanticV1Generic(GenericModel, Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


class PydanticV2Generic(pydantic_v2.BaseModel, Generic[T]):
    foo: T
    optional_foo: Optional[T]
    annotated_foo: Annotated[T, object()]


@pytest.mark.parametrize("model", [PydanticV1Generic, PydanticV2Generic])
def test_schema_generation_with_generic_classes(model: Type[Union[PydanticV1Generic, PydanticV2Generic]]) -> None:
    cls = model[int]  # type: ignore[index]
    field_definition = FieldDefinition.from_kwarg(name=get_name(cls), annotation=cls)

    schemas: Dict[str, Schema] = {}
    SchemaCreator(schemas=schemas, plugins=[PydanticSchemaPlugin()]).for_field_definition(field_definition)

    name = _get_type_schema_name(field_definition)
    properties = schemas[name].properties
    expected_foo_schema = Schema(type=OpenAPIType.INTEGER)
    expected_optional_foo_schema = Schema(one_of=[Schema(type=OpenAPIType.NULL), Schema(type=OpenAPIType.INTEGER)])

    assert properties
    assert properties["foo"] == expected_foo_schema
    assert properties["annotated_foo"] == expected_foo_schema
    assert properties["optional_foo"] == expected_optional_foo_schema