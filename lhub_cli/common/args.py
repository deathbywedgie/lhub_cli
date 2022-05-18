import argparse
from .output import SUPPORTED_OUTPUT_TYPES, SUPPORTED_TABLE_FORMATS
from ..log import Logging
from typing import Union

parser_types = Union[argparse.ArgumentParser, argparse._ArgumentGroup]
DEFAULT_LOG_LEVEL = "INFO"


def add_script_logging_args(parser: parser_types, default_log_level=DEFAULT_LOG_LEVEL):
    logging = parser.add_mutually_exclusive_group()
    logging.add_argument(
        "-log", "--level", dest="LOG_LEVEL", default=default_log_level,
        help="Set logging level",
        choices=['critical', 'fatal', 'error', 'warn', 'warning', 'info', 'debug', 'notset']
    )
    logging.add_argument("-v", "--debug", dest="DEBUG", action="store_true", help="Enable debug logging (shortcut)")
    logging.add_argument("-vv", "--verbose", dest="VERBOSE", action="store_true", help="Enable very verbose logging")


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


def build_args_and_logger(
        parser: argparse.ArgumentParser = None,
        description: str = None,
        include_list_output_args: bool = False,
        include_logging_args: bool = False,
        default_log_level: str = DEFAULT_LOG_LEVEL,
        **table_kwargs
) -> (argparse.Namespace, Logging):
    parser = parser or argparse.ArgumentParser(description=description)

    if include_list_output_args is True:
        # To prevent duplication of logging lines, leave include_log_level out when calling add_script_output_args
        table_kwargs["include_log_level"] = False
        add_script_output_args(parser=parser, **table_kwargs)

    if include_logging_args is True:
        add_script_logging_args(parser, default_log_level=default_log_level)

    final_args = parser.parse_args()

    # in case include_log_level was not enabled, force the existence of certain log properties
    final_args.DEBUG = getattr(final_args, "DEBUG", False)
    final_args.VERBOSE = getattr(final_args, "VERBOSE", False)
    final_args.LOG_LEVEL = "DEBUG" if final_args.DEBUG or final_args.VERBOSE else getattr(final_args, "LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    if not final_args.VERBOSE:
        # Doing this first before setting any other log level prevents enabling debug logs for urllib3 and any other modules which use logging
        _ = Logging()
    Logging.level = final_args.LOG_LEVEL
    return final_args, Logging()
