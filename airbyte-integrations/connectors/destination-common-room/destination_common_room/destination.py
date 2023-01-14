#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Iterable, Mapping

from airbyte_cdk import AirbyteLogger
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, AirbyteLogMessage, Level, ConfiguredAirbyteCatalog, Status, Type
from concurrent.futures import ThreadPoolExecutor, as_completed
from destination_common_room.client import CommonRoomClient
from requests.exceptions import HTTPError
from time import sleep
from traceback import TracebackException


class DestinationCommonRoom(Destination):
    def do_write(self, message: AirbyteMessage, client: CommonRoomClient):
        data = message.record.data
        email = data[client.email_field]
        try:
            [response] = client.member(email)
            for (source, api) in client.member_fields:
                if data.get(source) and response.get(api) != data.get(source):
                    raise HTTPError(f"Mismatch for {source} ({message})")
        except (ValueError, HTTPError):  # GET failed, so we create the member
            try:
                client.member(email, {
                    api: data.get(source) for (source, api) in client.member_fields
                })
            except HTTPError as e:
                log = AirbyteLogMessage(
                    level=Level.WARN,
                    message=f"Error adding user ({message}).",
                    stack_trace="".join(TracebackException.from_exception(e).format()))
                # Can't create member, so skip custom fields
                return [AirbyteMessage(type=Type.LOG, log=log)]
        logs = []
        for (source, field) in client.custom_fields:
            try:
                client.memberField(email, field, data.get(source))
            except HTTPError as e:
                log = AirbyteLogMessage(
                    level=Level.WARN,
                    message=f"Error setting custom field {repr(field)} ({message}).",
                    stack_trace="".join(TracebackException.from_exception(e).format()))
                logs.append(AirbyteMessage(type=Type.LOG, log=log))
        return logs

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
        with ThreadPoolExecutor(max_workers=20) as executor:
            client = CommonRoomClient(config)
            futures = []

            for message in input_messages:
                if message.type == Type.STATE:
                    for result in as_completed(futures):
                        for log in result.result():
                            yield log
                    futures = []
                    yield message
                elif message.type == Type.RECORD:
                    futures.append(executor.submit(
                        self.do_write, message, client))

            for result in as_completed(futures):
                for log in result.result():
                    yield log

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
            client = CommonRoomClient(config)
            existing = set(f["name"] for f in client.fields())
            configured = set(f["api"] for f in config["custom_fields"])
            misconfigured = configured - existing
            if len(misconfigured) > 0:
                return AirbyteConnectionStatus(status=Status.FAILED, message=f"Misconfigured fields {repr(set(misconfigured))} not present in {repr(existing)}")
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")
