#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from dataclasses import InitVar, dataclass
from typing import Any, List, Mapping, Union

import dpath.util
import requests
from airbyte_cdk.sources.declarative.decoders.decoder import Decoder
from airbyte_cdk.sources.declarative.decoders.json_decoder import JsonDecoder
from airbyte_cdk.sources.declarative.extractors.record_extractor import RecordExtractor
from airbyte_cdk.sources.declarative.interpolation.interpolated_string import InterpolatedString
from airbyte_cdk.sources.declarative.types import Config, Record
from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class DpathStringExtractor(RecordExtractor, JsonSchemaMixin):
    field_pointer: Union[InterpolatedString, str]
    config: Config
    options: InitVar[Mapping[str, Any]]
    decoder: Decoder = JsonDecoder(options={})

    def __post_init__(self, options: Mapping[str, Any]):
        self.field_pointer = InterpolatedString.create(self.field_pointer, options=options)
        self.field_pointer = self.field_pointer.eval(self.config)

    def extract_records(self, response: requests.Response) -> List[Record]:
        response_body = self.decoder.decode(response)
        return dpath.util.values(response_body, self.field_pointer)
