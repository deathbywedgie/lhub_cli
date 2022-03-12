import lhub
import time
import os
from pathlib import Path
from requests import HTTPError
import json
import base64
import re


class LogicHubCLI:

    def __init__(self, **kwargs):
        # ToDo:
        #  * Move the logging function out of lhub and into lhub_cli
        #  * Standardize better w/ the "logging" package
        self.log = lhub.log.Logger()
        self.__lhub = lhub.LogicHub(**kwargs)

    def _set_export_path(self, parent_folder, export_type):
        current_date = time.strftime("%Y-%m-%d")
        _folder_counter = 0
        while True:
            _folder_counter += 1
            _new_export_folder = os.path.join(parent_folder, f"{self.__lhub.api.url.server_name}_{export_type}_{current_date}_{_folder_counter}")
            if not os.path.exists(_new_export_folder) or not os.listdir(_new_export_folder):
                parent_folder = _new_export_folder
                path = Path(parent_folder)
                path.mkdir(parents=True, exist_ok=True)
                break
        return parent_folder

    def _save_export_to_disk(self, response, export_folder, resource_id, resource_name, file_info):
        try:
            response.raise_for_status()
        except HTTPError:
            warning = f"{file_info} - Download FAILED"
            _response_message = {}
            if response.text:
                try:
                    _response_message = json.loads(response.text)
                except json.decoder.JSONDecodeError:
                    pass

            if not _response_message.get("errors"):
                self.log.error(warning + f': unknown failure (status code {response.status_code})')
            else:
                for _error in _response_message.get("errors", []):
                    warning += f": {_error.get('errorType')}: {_error['message']}"
                    self.log.error(warning)
                    with open(os.path.join(export_folder, "_FAILURES.log"), "a+") as _error_file:
                        _error_file.write(warning + "\n")
        else:
            write_mode = "w"
            content_b64 = response.json()["result"]["contentB64"]
            file_type = response.json()["result"]["fileType"]
            file_name = f"{resource_name}.{file_type}"
            # Sanitize the name in case it contains illegal characters for a file name
            file_name = re.sub(r'[^\w\-()\[\] +]', '_', file_name)
            if file_type == "json":
                decoded = base64.b64decode(content_b64).decode("utf-8")
                file_data = json.dumps(json.loads(decoded), indent=4)
            elif file_type == "zip":
                write_mode = "wb"
                file_data = base64.b64decode(content_b64)
            else:
                # Should never happen, but just in case...
                raise lhub.exceptions.LhBaseException(f"\nERROR: Unknown file type. You will need to download manually: {resource_name} ({resource_id})")

            with open(os.path.join(export_folder, file_name), write_mode) as _file:
                _file.write(file_data)
            self.log.info(f"{file_info} - Saved successfully")

    def export_flows(self, export_folder, limit=None):
        export_folder = self._set_export_path(parent_folder=export_folder, export_type="flows")

        flow_ids = self.__lhub.actions.playbook_ids
        flow_ids_list = sorted(list(flow_ids.keys()))
        if limit:
            flow_ids_list = flow_ids_list[:limit]
        for n in range(len(flow_ids_list)):
            _flow_id = flow_ids_list[n]
            _flow_name = flow_ids[_flow_id]
            _file_info = f"{n + 1} of {len(flow_ids_list)}: {_flow_id} ({_flow_name})"
            self.log.info(f"{_file_info} - Downloading...")
            _response = self.__lhub.api._http_request(url=self.__lhub.api.url.flow_export.format(_flow_id), test_response=False)
            self._save_export_to_disk(response=_response, export_folder=export_folder, resource_id=_flow_id, resource_name=_flow_name, file_info=_file_info)

        self.log.info("Finished")
