import argparse
from lhub_cli.common.output import SUPPORTED_OUTPUT_TYPES, SUPPORTED_TABLE_FORMATS


def add_script_output_args(parser: argparse.ArgumentParser, default=None):
    if not default:
        default = "table"
    elif default not in SUPPORTED_OUTPUT_TYPES:
        raise ValueError(f"{default} is not a supported output type")
    output = parser.add_argument_group('output')

    output.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Also write output to a file")

    output.add_argument(
        "-o", "--output",
        dest="output_type",
        type=str,
        metavar="<OPTION>",
        default=default,
        choices=SUPPORTED_OUTPUT_TYPES,
        help=f"Output style (default: {default}). Available output types are: {', '.join(SUPPORTED_OUTPUT_TYPES)}")

    # https://github.com/astanin/python-tabulate#table-format
    output.add_argument(
        "-t", "--table_format",
        type=str,
        metavar="<OPTION>",
        default=None,
        choices=SUPPORTED_TABLE_FORMATS,
        help=f"Table format (ignored if output type is not table). Available formats are: {', '.join(SUPPORTED_TABLE_FORMATS)}"
    )
