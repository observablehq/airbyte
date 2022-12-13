#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Iterable, Mapping, Optional

import requests
from airbyte_cdk import AirbyteLogger
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, ConfiguredAirbyteCatalog, Status


class CommonRoomStream(HttpStream):
    url_base = "https://api.commonroom.io/community/v1/"
    primary_key = "id"

    def __init__(self, bearer_token: str, **kwargs):
        super().__init__(**kwargs)
        self.bearer_token = bearer_token

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_headers(self, **kwargs) -> Mapping[str, Any]:
        if self.bearer_token:
            return {"Authorization": f"Bearer {self.bearer_token}"}
        return {}

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        response_json = response.json()
        if not isinstance(response_json, list):
            response_json = [response_json]
        yield from response_json


class CustomFields(CommonRoomStream):
    """
    API docs: https://api.commonroom.io/docs/community.html#tag/Members/paths/~1members~1customFields/get
    """

    def path(self, **kwargs) -> str:
        return "members/customFields"


class Member(CommonRoomStream):
    """
    API docs: https://api.commonroom.io/docs/community.html#operation/createOrUpdateCommunityMember
    """
    http_method = "POST"

    def path(self, **kwargs) -> str:
        return "members"


class MemberCustomField(CommonRoomStream):
    """
    API docs: https://api.commonroom.io/docs/community.html#operation/setMemberCustomFieldValue
    """
    http_method = "POST"

    def path(self, **kwargs) -> str:
        return "members/customFields"


class DestinationCommonRoom(Destination):
    def write(
        self, config: Mapping[str, Any], configured_catalog: ConfiguredAirbyteCatalog, input_messages: Iterable[AirbyteMessage]
    ) -> Iterable[AirbyteMessage]:
        """
        TODO
        Reads the input stream of messages, config, and catalog to write data to the destination.

        This method returns an iterable (typically a generator of AirbyteMessages via yield) containing state messages received
        in the input message stream. Outputting a state message means that every AirbyteRecordMessage which came before it has been
        successfully persisted to the destination. This is used to ensure fault tolerance in the case that a sync fails before fully completing,
        then the source is given the last state message output from this method as the starting point of the next sync.

        :param config: dict of JSON configuration matching the configuration declared in spec.json
        :param configured_catalog: The Configured Catalog describing the schema of the data being received and how it should be persisted in the
                                    destination
        :param input_messages: The stream of input messages received from the source
        :return: Iterable of AirbyteStateMessages wrapped in AirbyteMessage structs
        """
        print("hi")

        pass

    def check(self, logger: AirbyteLogger, config: Mapping[str, Any]) -> AirbyteConnectionStatus:
        """
        Tests if the input configuration can be used to successfully connect to the destination with the needed permissions
            e.g: if a provided API token or password can be used to connect and write to the destination.

        :param logger: Logging object to display debug/info/error to the logs
            (logs will not be accessible via airbyte UI if they are not passed to this logger)
        :param config: Json object containing the configuration of this destination, content of this json is as specified in
        the properties of the spec.json file

        :return: AirbyteConnectionStatus indicating a Success or Failure
        """
        try:
            # TODO: members/customFields
            api = CustomFields(config["bearer_token"])
            for r in api.read_records("full_refresh"):
                print(r)

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")
