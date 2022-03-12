#!/usr/bin/env python3
import json

import sys
import argparse
import re
# import csv
# import os

# from lhub_pw import delete_me, Logger, LogicHub
from lhub_cli import features
from lhub.log import Logger
from tabulate import tabulate_formats
import lhub_cli
import lhub

__version__ = "0.1"
log = Logger()

# log_level = "INFO"


# ToDo:
#   * Add an argparse option for setting the result limit to return. Default is 25.
#   * Rework lhub_pw & this file so that lhub_pw is *only* for stuff that should still be there when this switches to a shell
#   * support api tokens
#   * support direct passing of hostname and token as alternative to credential file
#   * change from credentials.json to "~/.logichub/credentials" like aws
#   * add ability to generate credential entry if it doesn't exist already


def parse_and_validate_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Remotely execute a LogicHub command")

    # Required input
    parser.add_argument("instance", metavar="INSTANCE", type=str, help="Name of the instance as defined in credentials.json")
    parser.add_argument("command", metavar="COMMAND", type=str, help="Name of the remote LogicHub command to execute")

    # Optional input
    parser.add_argument("params", metavar="PARAMS", nargs='*', help="Command parameters (inputs) as key-value pairs")

    parser.add_argument(
        "--log_level",
        type=str,
        default="info",
        choices=log._LOG_LEVELS,
        help="Log level (default: info)"
    )

    output = parser.add_argument_group('output')

    output.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Also write output to a file")

    fields = output.add_mutually_exclusive_group()

    fields.add_argument(
        "--fields",
        type=str,
        metavar="<FIELDS>",
        default="",
        help="Top level fields to display")

    fields.add_argument(
        "--drop",
        type=str,
        metavar="<FIELDS>",
        default="",
        help="Top level fields to drop")

    output.add_argument("--fix_json", action="store_true", help="Automatically fix JSON formatting issues")

    output.add_argument(
        "-o", "--output",
        dest="output_type",
        type=str,
        default="table",
        choices=lhub_cli.features.commands.Command._supported_output_types,
        help="Output style (default: table)")

    # https://github.com/astanin/python-tabulate#table-format
    output.add_argument(
        "--table_format",
        type=str,
        default=None,
        choices=tabulate_formats,
        help="Table format, ignored if output type is not table (\"tablefmt\" from tabulate python package)"
    )

    # auth_mode = parser.add_mutually_exclusive_group()
    # auth_mode.add_argument("-i", "--instance", nargs='?', type=str, dest="instance_name", help="Name of the instance as defined in credentials.json")

    connection = parser.add_argument_group('connection')

    connection.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL warnings")
    connection.add_argument("-t", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")
    connection.add_argument("-tl", "--timeout_logon", metavar="<sec>", type=int, default=20, help="Logon timeout (default: 20)")

    # take in the arguments provided by user
    _args = parser.parse_args()

    # global log_level
    # log_level = _args.log_level

    log.log_level = _args.log_level
    # Logger.default_log_level = _args.log_level

    if not _args.instance:
        log.fatal("Instance cannot be blank")
    if not _args.command:
        log.fatal("command cannot be blank")

    lhub.LogicHub.http_timeout_login = _args.timeout_logon
    log.debug(f"Logon timeout: {_args.timeout_logon}")

    lhub.LogicHub.http_timeout_default = _args.timeout
    log.debug(f"Other HTTP timeout: {_args.timeout}")

    if _args.ignore_ssl:
        log.debug(f"SSL verification disabled")
        # lhub.LogicHub.verify_ssl = False

    return _args


# class Command:
#     __output_type = "json_pretty"
#     _supported_output_types = sorted(["json", "json_pretty", "raw", "raw_pretty", "table", "csv"])
#     verify_ssl = True
#     lhub_hidden_fields = ["lhub_page_num", "lhub_id"]
#
#     def __init__(self, instance, verify_ssl=True, output_type: str = None, table_format: str = None):
#         if output_type:
#             self.output_type = output_type
#         if isinstance(verify_ssl, bool):
#             self.verify_ssl = verify_ssl
#         else:
#             raise TypeError("verify_ssl requires a boolean value")
#         self.table_format = table_format
#         self.session = delete_me.new_session_from_credential_file(instance, verify_ssl=self.verify_ssl)
#
#     @property
#     def output_type(self):
#         return self.__output_type
#
#     @output_type.setter
#     def output_type(self, var):
#         if var not in self._supported_output_types:
#             raise ValueError(f"\"{var}\" is not a supported output type. Supported types are: {self._supported_output_types}")
#         self.__output_type = var
#
#     def __extract_command_results(self, response, fields: list = None, drop: list = None):
#         result = response.pop("result")
#         warnings = result.pop("warnings", [])
#         rows = result['rows']['data']
#         drop_fields = self.lhub_hidden_fields
#         if drop:
#             drop_fields.extend(drop)
#         for row_num in range(len(rows)):
#
#             rows[row_num]['fields'] = {k: v for k, v in rows[row_num]['fields'].items() if k not in drop_fields}
#             if fields:
#                 new_output = {}
#
#                 for _field in fields:
#                     if _field in rows[row_num]['fields']:
#                         new_output[_field] = rows[row_num]['fields'][_field]
#                 if new_output:
#                     rows[row_num]['fields'] = new_output
#                 else:
#                     log.warn(f"None of the provided fields were found in the results. Returning all columns.")
#         log.debug(f"Non-result response: {json.dumps(response)}")
#         return rows, warnings
#
#     def print_command_results(self, results, fields: list = None, drop: list = None, output_file: str = None):
#         def split_id_from_fields(result_list):
#             output = []
#             for row in result_list:
#                 _id = row['id']
#                 _fields = row['fields']
#                 log.debug(f"Processing correlation ID: {_id}")
#                 output.append(_fields)
#             return output
#
#         def _print_json(result_list, pretty=False):
#             indent = 2 if pretty else None
#             output = json.dumps(result_list, indent=indent)
#             log.print(output)
#             if output_file:
#                 with open(output_file, "w+") as _file:
#                     _file.write(output)
#
#         def _print_table(result_list):
#             if self.table_format:
#                 output = tabulate([x.values() for x in result_list], headers=result_list[0].keys(), tablefmt=self.table_format)
#             else:
#                 output = tabulate([x.values() for x in result_list], headers=result_list[0].keys())
#
#             print(output)
#             if output_file:
#                 with open(output_file, "w+") as _file:
#                     _file.write(output)
#
#         def _print_raw(result_list, pretty=False):
#             indent = 2 if pretty else None
#             output = json.dumps(result_list, indent=indent)
#             log.print(output)
#             if output_file:
#                 with open(output_file, "w+") as _file:
#                     _file.write(output)
#
#         def _print_csv(result_list):
#             headers = result_list[0].keys()
#
#             default_temp_file = '.__temp_csv'
#             _output_file = output_file or default_temp_file
#
#             with open(_output_file, 'w') as csv_file:
#                 writer = csv.DictWriter(csv_file, fieldnames=headers)
#                 writer.writeheader()
#                 for data in result_list:
#                     writer.writerow(data)
#
#             with open(_output_file, 'r') as _file:
#                 print(_file.read().strip())
#                 # for _line in _file.readlines():
#                 #     print(_line)
#
#             if _output_file == default_temp_file:
#                 os.remove(_output_file)
#
#         if self.output_type == "raw":
#             _print_raw(results, pretty=False)
#             return
#         elif self.output_type == "raw_pretty":
#             _print_raw(results, pretty=True)
#             return
#
#         output_functions = {
#             "json": (_print_json, {"pretty": False}),
#             "json_pretty": (_print_json, {"pretty": True}),
#             "table": (_print_table, {}),
#             "csv": (_print_csv, {})
#         }
#
#         func, kwargs = output_functions.get(self.__output_type)
#         if not func:
#             raise ValueError(f"Unsupported output type: {self.output_type}")
#
#         reformatted, warnings = self.__extract_command_results(results, fields=fields or [], drop=drop or [])
#
#         for _warning in warnings:
#             log.warn(f"Warning returned: {_warning}")
#
#         rows = split_id_from_fields(reformatted)
#         func(rows, **kwargs)
#
#     def run_command(self, command, fix_json=False, fields: list = None, drop: list = None, output_file: str = None, **kwargs):
#         fix_json = False if fix_json is False else True
#         response = self.session.action_run_command(
#             command_name=command,
#             input_dict=kwargs,
#             reformat=False)
#
#         if fix_json:
#             response = lhub_pw.common.to_dict_recursive(response)
#
#         self.print_command_results(response, fields=fields, drop=drop, output_file=output_file)


def main():
    args = parse_and_validate_args()
    # _ = lhub_pw.LogicHubConnection(instance_alias=args.instance)

    command_parameters = {}
    for i in args.params:
        _parts = re.search("^([^=]+)=(.*)", i)
        if not _parts:
            log.fatal(f"Parameters must be key-value pairs. Invalid input: {i}")
        command_parameters[_parts.group(1)] = _parts.group(2)

    fields = [x.strip() for x in args.fields.split(',') if x.strip()]
    drop_fields = [x.strip() for x in args.drop.split(',') if x.strip()]

    config = lhub_cli.connection_manager.LhubConfig()
    config = config.get_instance(args.instance)
    session = lhub.LogicHub(
        hostname=config.hostname, api_key=config.api_key, username=config.username, password=config.password, verify_ssl=config.verify_ssl)

    cmd = lhub_cli.features.commands.Command(
        session=session,
        verify_ssl=config.verify_ssl,
        output_type=args.output_type,
        table_format=args.table_format
    )
    cmd.run_command(command=args.command, fix_json=args.fix_json, fields=fields, drop=drop_fields, output_file=args.file, **command_parameters)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=sys.stderr)
