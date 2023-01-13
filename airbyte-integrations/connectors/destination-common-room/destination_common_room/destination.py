#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import json
from typing import Any, Iterable, Mapping, Optional

from airbyte_cdk import AirbyteLogger
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, AirbyteLogMessage, Level, ConfiguredAirbyteCatalog, Status, Type
from destination_common_room.client import CommonRoomClient
from time import sleep
from requests.exceptions import HTTPError
from traceback import TracebackException


class DestinationCommonRoom(Destination):
    def write(
        self, config: Mapping[str, Any], configured_catalog: ConfiguredAirbyteCatalog, input_messages: Iterable[AirbyteMessage]
    ) -> Iterable[AirbyteMessage]:
        """
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
        email_field = config["email_field"]
        member_fields = [
            (f["source"], f["api"]) for f in config["member_fields"]
        ]

        client = CommonRoomClient(config["bearer_token"])
        existing = {f["name"]: f for f in client.fields()}
        custom_fields = [
            (f["source"], existing[f["api"]]) for f in config["custom_fields"]
        ]

        for message in input_messages:
            if message.type == Type.STATE:
                yield message
            elif message.type == Type.RECORD:
                data = message.record.data
                email = data[email_field]
                try:
                    client.member(email)
                except HTTPError:  # GET failed, so we create the member
                    try:
                        client.member(email, {
                            api: data.get(source) for (source, api) in member_fields
                        })
                    except HTTPError as e:
                        log = AirbyteLogMessage(
                            level=Level.WARN,
                            message=f"Error adding user ({email}).",
                            stack_trace="".join(TracebackException.from_exception(e).format()))
                        yield AirbyteMessage(type=Type.LOG, log=log)
                        continue  # Can't create member, so skip custom fields
                for (source, field) in custom_fields:
                    try:
                        client.memberField(email, field, data.get(source))
                    except HTTPError as e:
                        log = AirbyteLogMessage(
                            level=Level.WARN,
                            message=f"Error setting custom field {repr(field)} ({email}).",
                            stack_trace="".join(TracebackException.from_exception(e).format()))
                        yield AirbyteMessage(type=Type.LOG, log=log)

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
            client = CommonRoomClient(config["bearer_token"])
            existing = set(f["name"] for f in client.fields())
            configured = set(f["api"] for f in config["custom_fields"])
            misconfigured = configured - existing
            if len(misconfigured) > 0:
                return AirbyteConnectionStatus(status=Status.FAILED, message=f"Misconfigured fields {repr(set(misconfigured))} not present in {repr(existing)}")
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")
