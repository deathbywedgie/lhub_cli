import argparse
from lhub_cli.common.output import supported_output_types, supported_table_formats


def add_script_output_args(parser: argparse.ArgumentParser, default=None):
    if not default:
        default = "table"
    elif default not in supported_output_types:
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
        choices=supported_output_types,
        help=f"Output style (default: {default}). Available output types are: {', '.join(supported_output_types)}")

    # https://github.com/astanin/python-tabulate#table-format
    output.add_argument(
        "-t", "--table_format",
        type=str,
        metavar="<OPTION>",
        default=None,
        choices=supported_table_formats,
        help=f"Table format (ignored if output type is not table). Available formats are: {', '.join(supported_table_formats)}"
    )
