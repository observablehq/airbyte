#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from destination_common_room import DestinationCommonRoom

if __name__ == "__main__":
    DestinationCommonRoom().run(sys.argv[1:])
