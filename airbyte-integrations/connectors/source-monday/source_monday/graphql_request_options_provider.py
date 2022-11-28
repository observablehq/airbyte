import json
import os
from dataclasses import dataclass
from typing import Optional, Mapping, Any, Union, MutableMapping

from airbyte_cdk.sources.declarative.interpolation import InterpolatedString
from airbyte_cdk.sources.declarative.requesters.request_options import InterpolatedRequestOptionsProvider
from airbyte_cdk.sources.declarative.types import StreamState, StreamSlice


@dataclass
class CustomOptionsProviderMixin:
    limit: Union[InterpolatedString, str] = None


@dataclass
class GraphQLRequestOptionsProvider(CustomOptionsProviderMixin, InterpolatedRequestOptionsProvider):
    NEXT_PAGE_TOKEN_FIELD_NAME = "next_page_token"

    def __post_init__(self, options: Mapping[str, Any]):
        super(GraphQLRequestOptionsProvider, self).__post_init__(options)

        self.limit = InterpolatedString.create(self.limit, options=options)
        self.name = options.get('name', '').lower()

    def _get_schema_root_properties(self):
        schema_path = os.path.join(os.path.abspath(os.curdir), "source_monday", f"schemas/{self.name}.json")
        with open(schema_path) as f:
            schema_dict = json.load(f)
            return schema_dict["properties"]

    def _get_query_by_stream_properties(self, props: dict):
        if self.name == "teams" and self.config.get("debug"):
            return "id,name,picture_url,users(limit:100){id}"
        query = ','.join([f'{col}' + (f'{{{self._get_query_by_stream_properties(props[col]["properties"])}}}' if 'properties' in props[col] else '') for col in props])
        return query

    def get_request_params(self, *, stream_state: Optional[StreamState] = None, stream_slice: Optional[StreamSlice] = None,
                           next_page_token: Optional[Mapping[str, Any]] = None) -> MutableMapping[str, Any]:
        graphql_params = {}
        limit = self.limit.eval(self.config)
        if limit:
            graphql_params["limit"] = limit
        if next_page_token:
            graphql_params["page"] = next_page_token[self.NEXT_PAGE_TOKEN_FIELD_NAME]

        graphql_query = ",".join([f"{k}:{v}" for k, v in graphql_params.items()])
        # Monday uses a query string to pass in environments
        if self.name == "items":
            params = {"query": f"query {{ boards ({graphql_query}) {{ {self.name}(limit:100){{ {self._get_query_by_stream_properties(self._get_schema_root_properties())} }} }} }}"}
        else:
            params = {"query": f"query {{ {self.name} ({graphql_query}) {{ {self._get_query_by_stream_properties(self._get_schema_root_properties())} }} }}"}
        return params
