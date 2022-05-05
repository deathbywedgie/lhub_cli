import argparse
from lhub_cli.common.output import SUPPORTED_OUTPUT_TYPES, SUPPORTED_TABLE_FORMATS
from ..log import Logging


def add_script_output_args(parser: argparse.ArgumentParser, include_log_level=True, default_output=None):
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
        logging = output.add_mutually_exclusive_group()
        logging.add_argument(
            "-log", "--level", default="INFO",
            choices=['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET', 'critical', 'fatal', 'error', 'warn', 'warning', 'info', 'debug'],
            help="Set logging level"
        )
        logging.add_argument("--debug", action="store_true", help="Enable debug logging (shortcut)")
        logging.add_argument("-vv", "--verbose", action="store_true", help="Enable very verbose logging")


def finish_parser_args(parser: argparse.ArgumentParser, **kwargs):
    # _ = kwargs.pop("include_log_level", None)
    add_script_output_args(parser=parser, **kwargs)
    final_args = parser.parse_args()
    if kwargs.get("include_log_level", True) is not False:
        if not final_args.verbose:
            # Doing this first before setting any other log level prevents enabling debug logs for urllib3 and any other modules which use logging
            _ = Logging()
        log_level = final_args.level.upper().strip()
        if final_args.debug or final_args.verbose:
            log_level = "DEBUG"
        Logging.level = log_level
    final_args.LOGGER = Logging()
    final_args.LOGGER = final_args.LOGGER.log
    return final_args
