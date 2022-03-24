import argparse
from lhub_cli.common.output import SUPPORTED_OUTPUT_TYPES, SUPPORTED_TABLE_FORMATS


def add_script_output_args(parser: argparse.ArgumentParser, default_output=None):
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
