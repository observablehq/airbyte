from source_monday import GraphQLRequestOptionsProvider


def test_get_request_params(mocker):
    schema = {
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
    mocker.patch.object(GraphQLRequestOptionsProvider, "get_schema_root_properties", return_value=schema)
    provider = GraphQLRequestOptionsProvider(
        limit="{{ options['items_per_page'] }}",
        options={"name": "items", "items_per_page": 100}
    )
    assert provider.get_request_params(
        stream_state=mocker.MagicMock(),
        stream_slice=mocker.MagicMock(),
        next_page_token={"next_page_token": 2}
    ) == {"query": "query { items (limit:100,page:2) { key_a{key_a_1{key_a_2}},key_b,key_c } }"}
