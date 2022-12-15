#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, Iterable, List, Mapping, Tuple, Union
import requests


class CommonRoomClient:
    base_url = "https://api.commonroom.io/community/v1/"

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    def fields(self):
        """
        API docs: https://api.commonroom.io/docs/community.html#tag/Members/paths/~1members~1customFields/get
        """
        return self._request("GET", "members/customFields")

    def member(self, data):
        """
        API docs: https://api.commonroom.io/docs/community.html#operation/createOrUpdateCommunityMember
        """
        return self._request("POST", "members", {
            "socials": [{"type": "email", "value": "visnu@observablehq.com"}],
            # "fullName": "Visnu Pitiyanuvath",
            # "avatarUrl": "",
            "description": "Testing",
            "source": "Recurring import"
        })

    def memberField(self, data):
        """
        API docs: https://api.commonroom.io/docs/community.html#operation/setMemberCustomFieldValue
        """
        return {"socialType": "email", "value": "visnu@observablehq.com", "customFieldId": 0, "customFieldValue": ""}

    def _request_headers(self) -> Mapping[str, Any]:
        return {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}

    def _request(
        self, http_method: str, path: str, json: Mapping[str, Any] = None
    ) -> requests.Response:
        url = f"{self.base_url}/{path}"
        headers = {"Accept": "application/json", **self._request_headers()}

        response = requests.request(
            method=http_method, url=url, headers=headers, json=json)

        response.raise_for_status()
        return response.json()
