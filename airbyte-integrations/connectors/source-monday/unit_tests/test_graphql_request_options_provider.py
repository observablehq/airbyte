import pytest
from source_monday import GraphQLRequestOptionsProvider


nested_schema = {
    "key_a": {
        "type": ["null", "string"],
        "properties": {
            "key_a_1": {
                "type": ["null", "string"],
                "properties": {
                    "key_a_2": {"type": ["null", "string"]}
                }
            }
        }
    },
    "key_b": {"type": ["null", "string"]},
    "key_c": {"type": ["null", "string"]},
}

@pytest.mark.parametrize(
    ("input_schema", "graphql_query", "stream_name"),
    [
        pytest.param(
            nested_schema,
            {"query": "query { test_stream (limit:100,page:2) { key_a{key_a_1{key_a_2}},key_b,key_c } }"},
            "test_stream",
            id="test_get_request_params_produces_graphql_string_for_items"
        )
    ]
)
def test_get_request_params(mocker, input_schema, graphql_query, stream_name):
    mocker.patch.object(GraphQLRequestOptionsProvider, "_get_schema_root_properties", return_value=input_schema)
    provider = GraphQLRequestOptionsProvider(
        limit="{{ options['items_per_page'] }}",
        options={"name": stream_name, "items_per_page": 100}
    )
    assert provider.get_request_params(
        stream_state={},
        stream_slice={},
        next_page_token={"next_page_token": 2}
    ) == graphql_query
