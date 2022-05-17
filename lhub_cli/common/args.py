import argparse
from lhub_cli.common.output import SUPPORTED_OUTPUT_TYPES, SUPPORTED_TABLE_FORMATS
from ..main import LogicHubCLI
from ..connection_manager import LogicHubConnection
from ..log import Logging
from typing import Union

parser_types = Union[argparse.ArgumentParser, argparse._ArgumentGroup]


def add_script_logging_args(parser: parser_types, default_log_level=None):
    logging = parser.add_mutually_exclusive_group()
    logging.add_argument(
        "-log", "--level", default=default_log_level or "INFO",
        help="Set logging level",
        choices=['critical', 'fatal', 'error', 'warn', 'warning', 'info', 'debug', 'notset']
    )
    logging.add_argument("--debug", action="store_true", help="Enable debug logging (shortcut)")
    logging.add_argument("-vv", "--verbose", action="store_true", help="Enable very verbose logging")


def add_script_output_args(parser: parser_types, include_log_level: bool = True, default_output=None):
    if not default_output:
        default_output = "table"
    elif default_output not in SUPPORTED_OUTPUT_TYPES:
        raise ValueError(f"{default_output} is not a supported output type")
    output = parser.add_argument_group('output')

    output.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Also write output to a file")

    output.add_argument(
        "-o", "--output",
        type=str,
        metavar="<OPTION>",
        default=default_output,
        choices=SUPPORTED_OUTPUT_TYPES,
        help=f"Output style (default: {default_output}). Available output types are: {', '.join(SUPPORTED_OUTPUT_TYPES)}")

    # https://github.com/astanin/python-tabulate#table-format
    output.add_argument(
        "-t", "--table_format",
        type=str,
        metavar="<OPTION>",
        default=None,
        choices=SUPPORTED_TABLE_FORMATS,
        help=f"Table format (ignored if output type is not table). Available formats are: {', '.join(SUPPORTED_TABLE_FORMATS)}"
    )

    if include_log_level:
        add_script_logging_args(output)


def finish_parser_args(parser: argparse.ArgumentParser, include_log_level: bool = True, **kwargs):
    # To prevent duplication of logging lines, leave include_log_level out when calling add_script_output_args
    kwargs.update({"include_log_level": False})
    add_script_output_args(parser=parser, **kwargs)
    if include_log_level is not False:
        return finish_parser_args_with_logger_only(parser)
    final_args = parser.parse_args()
    new_logger = Logging()
    final_args.LOGGER = new_logger.log
    return final_args


def finish_parser_args_with_logger_only(parser: argparse.ArgumentParser):
    add_script_logging_args(parser)
    final_args = parser.parse_args()
    if not final_args.verbose:
        # Doing this first before setting any other log level prevents enabling debug logs for urllib3 and any other modules which use logging
        _ = Logging()
    log_level = final_args.level.upper()
    if final_args.debug or final_args.verbose:
        log_level = "DEBUG"
    Logging.level = log_level
    new_logger = Logging()
    final_args.LOGGER = new_logger.log
    return final_args
