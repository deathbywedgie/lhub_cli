from lhub.log import Logger
from lhub.common.dicts_and_lists import to_dict_recursive
import json
from tabulate import tabulate
import csv
import os

log = Logger()


# ToDo Rewrite to make this a part of the LogicHubCLI instance instead of needing the "session" input

class Command:
    __output_type = "json_pretty"
    _supported_output_types = sorted(["json", "json_pretty", "raw", "raw_pretty", "table", "csv"])
    verify_ssl = True
    lhub_hidden_fields = ["lhub_page_num", "lhub_id"]

    def __init__(self, session, verify_ssl=True, output_type: str = None, table_format: str = None):
        if output_type:
            self.output_type = output_type
        if isinstance(verify_ssl, bool):
            self.verify_ssl = verify_ssl
        else:
            raise TypeError("verify_ssl requires a boolean value")
        self.table_format = table_format
        self.session = session

    @property
    def output_type(self):
        return self.__output_type

    @output_type.setter
    def output_type(self, var):
        if var not in self._supported_output_types:
            raise ValueError(f"\"{var}\" is not a supported output type. Supported types are: {self._supported_output_types}")
        self.__output_type = var

    def __extract_command_results(self, response, fields: list = None, drop: list = None):
        result = response.pop("result")
        warnings = result.pop("warnings", [])
        rows = result['rows']['data']
        drop_fields = self.lhub_hidden_fields
        if drop:
            drop_fields.extend(drop)
        for row_num in range(len(rows)):

            rows[row_num]['fields'] = {k: v for k, v in rows[row_num]['fields'].items() if k not in drop_fields}
            if fields:
                new_output = {}

                for _field in fields:
                    if _field in rows[row_num]['fields']:
                        new_output[_field] = rows[row_num]['fields'][_field]
                if new_output:
                    rows[row_num]['fields'] = new_output
                else:
                    log.warn(f"None of the provided fields were found in the results. Returning all columns.")
        log.debug(f"Non-result response: {json.dumps(response)}")
        return rows, warnings

    def print_command_results(self, results, fields: list = None, drop: list = None, output_file: str = None):
        def split_id_from_fields(result_list):
            output = []
            for row in result_list:
                _id = row['id']
                _fields = row['fields']
                log.debug(f"Processing correlation ID: {_id}")
                output.append(_fields)
            return output

        def _print_json(result_list, pretty=False):
            indent = 2 if pretty else None
            output = json.dumps(result_list, indent=indent)
            log.print(output)
            if output_file:
                with open(output_file, "w+") as _file:
                    _file.write(output)

        def _print_table(result_list):
            if self.table_format:
                output = tabulate([x.values() for x in result_list], headers=result_list[0].keys(), tablefmt=self.table_format)
            else:
                output = tabulate([x.values() for x in result_list], headers=result_list[0].keys())

            print(output)
            if output_file:
                with open(output_file, "w+") as _file:
                    _file.write(output)

        def _print_raw(result_list, pretty=False):
            indent = 2 if pretty else None
            output = json.dumps(result_list, indent=indent)
            log.print(output)
            if output_file:
                with open(output_file, "w+") as _file:
                    _file.write(output)

        def _print_csv(result_list):
            headers = result_list[0].keys()

            default_temp_file = '.__temp_csv'
            _output_file = output_file or default_temp_file

            with open(_output_file, 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                for data in result_list:
                    writer.writerow(data)

            with open(_output_file, 'r') as _file:
                print(_file.read().strip())
                # for _line in _file.readlines():
                #     print(_line)

            if _output_file == default_temp_file:
                os.remove(_output_file)

        if self.output_type == "raw":
            _print_raw(results, pretty=False)
            return
        elif self.output_type == "raw_pretty":
            _print_raw(results, pretty=True)
            return

        output_functions = {
            "json": (_print_json, {"pretty": False}),
            "json_pretty": (_print_json, {"pretty": True}),
            "table": (_print_table, {}),
            "csv": (_print_csv, {})
        }

        func, kwargs = output_functions.get(self.__output_type)
        if not func:
            raise ValueError(f"Unsupported output type: {self.output_type}")

        reformatted, warnings = self.__extract_command_results(results, fields=fields or [], drop=drop or [])

        for _warning in warnings:
            log.warn(f"Warning returned: {_warning}")

        rows = split_id_from_fields(reformatted)
        func(rows, **kwargs)

    def run_command(self, command, fix_json=False, fields: list = None, drop: list = None, output_file: str = None, **kwargs):
        fix_json = False if fix_json is False else True
        response = self.session.actions.execute_command(
            command_name=command,
            input_dict=kwargs,
            reformat=False)

        if fix_json:
            response = to_dict_recursive(response)

        self.print_command_results(response, fields=fields, drop=drop, output_file=output_file)
