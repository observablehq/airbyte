#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, Mapping
from requests.exceptions import HTTPError
from time import sleep
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

    def member(self, email: str, data: Mapping[str, Any] = None):
        """
        API docs:
          GET https://api.commonroom.io/docs/community.html#tag/Members/paths/~1members~1:query/get
          POST https://api.commonroom.io/docs/community.html#operation/createOrUpdateCommunityMember
        """
        if data == None:
            return self._request("GET", "members", params={"email": email})
        else:
            for n in range(0, 3):
                try:
                    sleep(2 * n)
                    return self._request("POST", "members", dict({
                        "socials": [{"type": "email", "value": email}],
                        "source": "Recurring import"},
                        **data
                    ))
                except HTTPError:
                    if n == 2:
                        raise

    def memberField(self, email: str, field: Mapping[str, Any], value: Any):
        """
        API docs: https://api.commonroom.io/docs/community.html#operation/setMemberCustomFieldValue
        field comes from fields()

        Common Room raises 404 not found soon after creating a member, so retry
        for a bit.
        """
        if value:
            for n in range(0, 3):
                try:
                    sleep(2 * n)
                    return self._request("POST", "members/customFields", {
                        "socialType": "email",
                        "value": email,
                        "customFieldId": field["id"],
                        "customFieldValue": {"type": field["type"], "value": value}
                    })
                except HTTPError:
                    if n == 2:
                        raise

    def _request_headers(self) -> Mapping[str, Any]:
        return {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}

    def _request(
        self, http_method: str, path: str, json: Mapping[str, Any] = None, params: Mapping[str, Any] = None
    ) -> requests.Response:
        url = f"{self.base_url}/{path}"
        headers = {"Accept": "application/json", **self._request_headers()}

        response = requests.request(
            method=http_method, url=url, headers=headers, json=json, params=params)

        if not response.ok:
            raise HTTPError(response.text, response=response)

        return response.json()
