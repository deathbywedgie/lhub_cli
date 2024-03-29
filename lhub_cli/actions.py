import lhub
import time
import os
from pathlib import Path
from requests import HTTPError
import json
import base64
import re
from .connection_manager import LogicHubConnection
from .common.output import print_fancy_lists
from numbers import Number
from .log import generate_logger, ExpectedLoggerTypes
from typing import Union

# ToDo NEXT: Follow the same formula from "export_playbooks" to add support for exporting other resource types as well
#  * custom lists
#  * event types
#  * commands
#  * modules
#  * custom integration
#  * baselines
#  * scripts (new, used in runScript)
#  * scripts (legacy, if the process is different)
#  * dashboards & widgets
#  Features without an official export ability:
#  * cases? Probably not, but maybe...


# ToDo This isn't going to scale indefinitely. Need to break these actions apart by feature somehow.
class Actions:

    def __init__(self, session: lhub.LogicHub, config: LogicHubConnection, instance_label, logger: ExpectedLoggerTypes = None):
        self.__lhub = session
        self.__config = config
        self.__instance_name = instance_label
        self.__log = logger or generate_logger(name=__name__, instance_name=instance_label)

    def __set_export_path(self, parent_folder, export_type):
        current_date = time.strftime("%Y-%m-%d")
        _folder_counter = 0
        while True:
            _folder_counter += 1
            _new_export_folder = os.path.join(parent_folder, f"{self.__lhub.api.url.server_name}_{export_type}_{current_date}_{_folder_counter}_m{self.__lhub.api.version}")
            if not os.path.exists(_new_export_folder) or not os.listdir(_new_export_folder):
                parent_folder = _new_export_folder
                path = Path(parent_folder)
                path.mkdir(parents=True, exist_ok=True)
                break
        return parent_folder

    def __save_export_to_disk(self, response, export_folder, resource_id, resource_name, file_info):
        write_mode = "w"
        content_b64 = response["result"]["contentB64"]
        file_type = response["result"]["fileType"]
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
        self.__log.info(f"{file_info} - Saved successfully")

    def export_playbooks(self, export_folder, limit=None, return_summary=False):
        export_folder = self.__set_export_path(parent_folder=export_folder, export_type="flows")
        self.__log.info(f"Saving files to: {export_folder}")
        flow_ids = self.__lhub.actions.playbook_ids
        flow_ids_list = sorted(list(flow_ids.keys()))
        if limit:
            flow_ids_list = flow_ids_list[:limit]
        failed = {}
        for n in range(len(flow_ids_list)):
            _flow_id = flow_ids_list[n]
            _flow_name = flow_ids[_flow_id]
            _file_info = f"{n + 1} of {len(flow_ids_list)}: {_flow_id} ({_flow_name})"
            self.__log.info(f"{_file_info} - Downloading...")
            try:
                _response = self.__lhub.api.export_playbook(_flow_id)
                self.__save_export_to_disk(response=_response, export_folder=export_folder, resource_id=_flow_id, resource_name=_flow_name, file_info=_file_info)
            except HTTPError:
                warning = f"{_file_info} - Download FAILED"
                _response_message = json.loads(self.__lhub.api.last_response_text)
                if not failed.get(_flow_id):
                    failed[_flow_id] = {"name": _flow_name, "errors": []}
                if not _response_message.get("errors"):
                    error = f"unknown failure (status code {self.__lhub.api.last_response_status})"
                    new_warning = f"{warning}: {error}"
                    failed[_flow_id]["errors"].append(error)
                    self.__log.error(new_warning)
                    with open(os.path.join(export_folder, "_FAILURES.log"), "a+") as _error_file:
                        _error_file.write(new_warning + "\n")
                else:
                    for _error in _response_message.get("errors", []):
                        error = f"{_error.get('errorType')}: {_error['message']}"
                        new_warning = f"{warning}: {error}"
                        failed[_flow_id]["errors"].append(error)
                        self.__log.error(new_warning)
                        with open(os.path.join(export_folder, "_FAILURES.log"), "a+") as _error_file:
                            _error_file.write(new_warning + "\n")

        self.__log.info("Playbook export complete")
        if return_summary:
            successful = True
            if failed:
                successful = False
            return successful, failed

    def reprocess_batches(self, batch_ids: (list, str, int), sec_between_calls=None):
        # Rather that using list(set(batch_ids)) to dedupe, do it manually to preserve the order that they are requested in
        unique_ids = []
        for b in batch_ids if isinstance(batch_ids, list) else [batch_ids]:
            if b not in unique_ids:
                unique_ids.append(b)
        if sec_between_calls:
            sec_between_calls = float(sec_between_calls)
        for n in range(len(unique_ids)):
            batch_id = unique_ids[n]
            if sec_between_calls and n > 0:
                time.sleep(sec_between_calls)
            _ = self.__lhub.actions.reprocess_batch(batch_id)
            self.__log.info(f'Batch {batch_id} rerun on {self.__instance_name}')

    @staticmethod
    def _reformat_user(user: dict):
        groups = [g['name'] for g in user['groups'] if not g.get("isDeleted", False)]
        user_attributes = {
            "username": user.get("name"),
            "is_admin": user["role"]["value"] == "admin",
            "groups": ', '.join(groups),
            "email": user.get("email"),
            "is_deleted": user.get("isDeleted"),
            "is_enabled": user.get("isEnabled"),
            "auth_type": user.get("authenticationType"),
            "id": user.get("userId"),
        }
        # would it be beneficial to make a class object for these instead of returning a dict?
        return user_attributes

    @staticmethod
    def _reformat_users(users: list):
        return [Actions._reformat_user(user) for user in users]

    def create_user(self, username, email, authentication_type: Union[str, dict] = None, group_names: list = None, group_ids: list = None):
        _result = self.__lhub.actions.create_user(
            username=username,
            email=email,
            authentication_type=authentication_type or "password",
            group_names=group_names or ["Everyone"],
            group_ids=group_ids,
        )
        self.__log.info("User created successfully", username=username)
        return _result

    def delete_user_by_name(self, username):
        results = self.__lhub.actions.delete_user_by_name(usernames=username)
        self.__log.warn(f"User deleted successfully", username=username)
        return results

    def list_users(self, print_output=True, return_results=True, show_hostname=False, sort_order=None, attributes: list = None, hide_inactive=True, **print_kwargs):
        required_columns = ["username"]
        if sort_order is None:
            sort_order = ["connection name", "username"]
        if attributes == "*":
            attributes = []
        attributes = attributes or []

        results = self.__lhub.actions.list_users(hide_inactive=hide_inactive, simple_format=True)
        for r in results:
            if 'auth_type' in r:
                r['password_enabled'] = r['auth_type'] == "password" or isinstance(r['auth_type'], dict) and r['auth_type']['enablePasswordAuthentication'] is True
                r['sso_enabled'] = 'samlConfigId' in r['auth_type']
            for k, v in r.items():
                if not isinstance(v, (str, Number)) or isinstance(v, bool):
                    r[k] = json.dumps(v)
        self.__log.debug(f"{len([r for r in results if r['is_admin']])} admin users found")

        # Update output to insert
        stock_fields = {"connection name": self.__config.credentials.connection_name}
        if show_hostname:
            stock_fields["hostname"] = self.__lhub.api.url.server_name
        results = [
            dict(**stock_fields, **{k: v for k, v in r.items() if k in required_columns or k in attributes or not attributes})
            for r in results
        ]

        for column in [sort_order[-1 - n] for n in range(len(sort_order))]:
            results = sorted(results, key=lambda e: (e[column]))
        if print_output:
            print_fancy_lists(results=results, **print_kwargs)
        if return_results:
            return results

    def list_commands(self, print_output=True, return_results=True, show_hostname=False, sort_order=None, attributes: list = None, **print_kwargs):
        required_columns = ["name"]
        if sort_order is None:
            sort_order = ["connection name", "name"]
        if attributes == "*":
            attributes = []
        attributes = attributes or []

        results = self.__lhub.actions.list_commands(simple_format=True)

        # Update output to insert
        stock_fields = {"connection name": self.__config.credentials.connection_name}
        if show_hostname:
            stock_fields["hostname"] = self.__lhub.api.url.server_name
        results = [
            dict(**stock_fields, **{k: v for k, v in r.items() if k in required_columns or k in attributes or not attributes})
            for r in results
        ]

        for column in [sort_order[-1 - n] for n in range(len(sort_order))]:
            results = sorted(results, key=lambda e: (e[column]))
        if print_output:
            print_fancy_lists(results=results, **print_kwargs)
        if return_results:
            return results
