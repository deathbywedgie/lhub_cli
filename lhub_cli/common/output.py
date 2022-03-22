import csv
import json
import os

from tabulate import tabulate, tabulate_formats

SUPPORTED_OUTPUT_TYPES = sorted(["csv", "json", "json_pretty", "table"])
SUPPORTED_TABLE_FORMATS = sorted(tabulate_formats)


def print_fancy_lists(results, output_type="table", table_format=None, ordered_headers=None, output_file=None, sort_order=None, file_only=False):
    """
    Print a list of dicts in a variety of ways, such as json, CSV, or assorted text tables

    :param results: list of dicts with a common schema
    :type results: list

    :param output_type: selection from SUPPORTED_OUTPUT_TYPES (default: table)
    :type output_type: str

    :param table_format: selection from SUPPORTED_TABLE_FORMATS (default: tabulate default)

    :param ordered_headers: optional: customize exact order of columns in the final output
    :type ordered_headers: list

    :param output_file: optional: path to write the output to a file
    :type output_type: str

    :param sort_order: optional: list of column headers to sort the results by before printing
    :type sort_order: list

    """

    def print_json(result_list, pretty=False):
        indent = 2 if pretty else None
        output = json.dumps(result_list, indent=indent)
        if not file_only:
            print(output)
        if output_file:
            with open(output_file, "w+") as _file:
                _file.write(output)

    def print_table(result_list):
        if table_format:
            if table_format not in SUPPORTED_TABLE_FORMATS:
                raise ValueError(f"{table_format} is not a supported table format")

        data = [x.values() for x in result_list]
        headers = ordered_headers
        if not headers:
            headers = result_list[0].keys() if result_list else ['no results']

        output = tabulate(
            tabular_data=data,
            headers=headers,
            tablefmt=table_format or None
        )
        if not file_only:
            print(output)
        if output_file:
            with open(output_file, "w+") as _file:
                _file.write(output)

    def print_csv(result_list):
        headers = result_list[0].keys()

        default_temp_file = '.__temp_csv'
        _output_file = output_file or default_temp_file

        with open(_output_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for data in result_list:
                writer.writerow(data)

        if not file_only:
            with open(_output_file, 'r') as _file:
                print(_file.read().strip())

        if _output_file == default_temp_file:
            os.remove(_output_file)

    if output_type not in SUPPORTED_OUTPUT_TYPES:
        raise ValueError(f"{output_type} is not a valid output type")

    if sort_order:
        for column in [sort_order[-1 - n] for n in range(len(sort_order))]:
            results = sorted(results, key=lambda e: (e[column]))

    if ordered_headers:
        new_rows = []
        for n in range(len(results)):
            new_entry = {}
            for k in ordered_headers:
                new_entry[k] = results[n][k]
            new_rows.append(new_entry)
        results = new_rows
    if output_type == "json":
        print_json(results, pretty=False)
    elif output_type == "json_pretty":
        print_json(results, pretty=True)
    elif output_type == "table":
        print_table(results)
    elif output_type == "csv":
        print_csv(results)
    else:
        raise ValueError(f"Unsupported output type: {output_type}")
