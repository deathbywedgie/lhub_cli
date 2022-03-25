#!/usr/bin/env python3

import lhub_cli
import sys

cli = lhub_cli.LogicHubCLI(sys.argv[1])
cli.actions.list_users()
