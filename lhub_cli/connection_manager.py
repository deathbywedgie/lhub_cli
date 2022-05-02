from pathlib import Path
import os
from configobj import ConfigObj
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lhub import LogicHub
from .encryption import Encryption
import getpass
from .common.config import dict_to_ini_file
from .common.shell import query_yes_no
from requests.exceptions import SSLError
from .exceptions.base import CLIValueError
import sys
from .log import generate_logger, ExpectedLoggerTypes

# static/global variables
LHUB_CONFIG_PATH = os.path.join(str(Path.home()), ".logichub")
CREDENTIALS_FILE_NAME = "credentials"
PREFERENCES_FILE_NAME = "preferences"


@dataclass_json
@dataclass
class _PreferenceMain:
    default_instance: str = None


@dataclass_json
@dataclass
class _PreferenceCommands:
    table_style: str = None


@dataclass_json
@dataclass
class Preferences:
    main: _PreferenceMain = None
    commands: _PreferenceCommands = None

    def __post_init__(self):
        self.preferences_file_name = PREFERENCES_FILE_NAME
        self.preferences_path = os.path.join(LHUB_CONFIG_PATH, self.preferences_file_name)
        self.get_preferences()

    def save_preferences_file(self):
        dict_to_ini_file(self.to_dict(), self.preferences_path)

    def get_preferences(self):
        if not os.path.exists(self.preferences_path):
            self.main = _PreferenceMain()
            self.commands = _PreferenceCommands()
            self.save_preferences_file()
            return

        preferences_obj = ConfigObj(self.preferences_path)
        if not self.main:
            self.main = _PreferenceMain(**{
                k: v for k, v in preferences_obj.dict().get("main", {}).items()
            })
        if not self.commands:
            self.commands = _PreferenceCommands(**{
                k: v for k, v in preferences_obj.dict().get("commands", {}).items()
            })


@dataclass_json
@dataclass
class Connection:
    # Deliberately left out password and api_token so that those sensitive fields do not show in JSON or repr forms
    hostname: str
    username: str
    verify_ssl: bool

    def __init__(self, name, **kwargs):
        self.connection_name = name
        self.hostname = kwargs.get("hostname")
        self.api_key = kwargs.get("api_key")
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.verify_ssl = kwargs.get("verify_ssl") or True
        if isinstance(self.verify_ssl, str):
            self.verify_ssl = not self.verify_ssl.lower() == 'false'
        assert self.hostname, "Server hostname not provided"
        if not self.api_key:
            assert self.password, "Neither an API key nor a password were provided in the connection config"
            assert self.username, "Username not provided"

    # Make it possible to represent a Connection object simply as a string in order to see the connection name
    def __str__(self):
        return self.connection_name


class LhubConfig:
    __full_config: ConfigObj = None
    credentials_file_name = CREDENTIALS_FILE_NAME
    __credentials_file_modified_time = None

    def __init__(self, credentials_file_name=None, logger: ExpectedLoggerTypes = None, log_level=None):
        self.__log = logger or generate_logger(self_obj=self, log_level=log_level)
        if log_level:
            self.__log.setLevel(log_level)
        if not os.path.exists(LHUB_CONFIG_PATH):
            self.__log.info(f"Default config path not found. Creating: {LHUB_CONFIG_PATH}")
            __lhub_path = Path(LHUB_CONFIG_PATH)
            __lhub_path.mkdir(parents=True, exist_ok=True)

        if credentials_file_name and credentials_file_name != self.credentials_file_name:
            self.credentials_file_name = f"{CREDENTIALS_FILE_NAME}-{credentials_file_name}"
        self.credentials_path = os.path.join(LHUB_CONFIG_PATH, self.credentials_file_name)
        self.__load_credentials_file()
        self.encryption = Encryption(LHUB_CONFIG_PATH, logger=self.__log, log_level=log_level)

    @property
    def existing_credential_files(self):
        return [CREDENTIALS_FILE_NAME] + sorted(list(set(
            [
                f.removeprefix(f'{CREDENTIALS_FILE_NAME}-')
                for f in os.listdir(LHUB_CONFIG_PATH)
                if f.startswith(f'{CREDENTIALS_FILE_NAME}-')
            ]
        )))

    def write_credential_file(self, explicit_config: dict = None):
        if explicit_config is None:
            explicit_config = self.__full_config.dict()
        dict_to_ini_file(explicit_config, self.credentials_path)
        self.reload()

    def __load_credentials_file(self):
        if not os.path.exists(self.credentials_path):
            if self.credentials_file_name != CREDENTIALS_FILE_NAME:
                if query_yes_no(f"No credential file found by name {self.credentials_file_name}. Create new file now?"):
                    self.write_credential_file(explicit_config={})
                else:
                    self.__log.fatal("Aborted by user.")
                    sys.exit(1)
            else:
                self.write_credential_file(explicit_config={})
        # Check the time the file was last modified
        file_modified = os.path.getmtime(self.credentials_path)
        if self.__full_config and self.__credentials_file_modified_time == file_modified:
            return
        self.__credentials_file_modified_time = file_modified
        self.__log.debug(f"Loading credential file: {self.credentials_file_name} [{self.credentials_path}]")
        self.__full_config = ConfigObj(self.credentials_path)

    @property
    def credential_file_changed(self):
        if self.__full_config and self.__credentials_file_modified_time == os.path.getmtime(self.credentials_path):
            return True
        return False

    def reload(self):
        # Reset file modified time so that any existing config will not be used
        self.__credentials_file_modified_time = None
        self.__load_credentials_file()

    def update_connection(self, instance_label, **kwargs):
        if not self.__full_config.get(instance_label):
            self.__full_config[instance_label] = kwargs
        else:
            self.__full_config[instance_label].update(kwargs)
        self.write_credential_file()

    def delete_connection(self, instance_label):
        if not self.__full_config.get(instance_label):
            self.__log.error(f"No connection found: {instance_label=}")
            return
        else:
            self.__log.debug(f"Deleting connection: {instance_label=}")
            del self.__full_config[instance_label]
        self.write_credential_file()

    def get_instance(self, instance_label):
        if self.credential_file_changed:
            self.reload()
        if instance_label not in self.__full_config:
            self.__log.error(f"No connection found: {instance_label=}")
            return
        # Make a copy of the dict, otherwise this will only work once, and it
        # will fail with a decryption error any subsequent calls for the same instance
        _credentials = {k: v for k, v in self.__full_config[instance_label].items()}
        for k in _credentials:
            if k in ('password', 'api_key'):
                _credentials[k] = self.encryption.decrypt_string(_credentials[k])
        return Connection(name=instance_label, **_credentials)

    def create_instance(self, instance_label, server=None, auth_type=None, api_key=None, username=None, password=None, verify_ssl=None):

        def verify_lhub_connection():
            verify = True if verify_ssl is None else verify_ssl
            self.__log.debug(f"Testing connectivity and authentication: {server=} {username=} {verify=}")
            _ = LogicHub(hostname=server, username=username, password=password, api_key=api_key, verify_ssl=verify_ssl)

        instance_label = instance_label.strip()
        if instance_label in self.__full_config:
            raise CLIValueError(f"An instance already exists by the name {instance_label}")
        server = server.strip() if server else None
        auth_type = auth_type.strip() if auth_type else None
        api_key = api_key.strip() if api_key else None
        username = username.strip() if username else None
        password = password.strip() if password else None
        verify_ssl = verify_ssl if verify_ssl is False else None

        if password and not api_key:
            # If a password was provided but no API key, assume password auth
            auth_type = 'password'
        if api_key and not password:
            # If an API key was provided but no password, assume password auth
            auth_type = 'api_key'

        while not server:
            server = input("Server hostname or IP: ").strip()

        while not auth_type:
            auth_choices = {
                "1": "password",
                "2": "api_key"
            }
            prompt = 'Authentication options:\n'
            for k, v in auth_choices.items():
                prompt += f'  [{k}] {v}\n'
            auth_type = auth_choices.get(input(prompt + '\nEnter a number to make a selection: ').strip())
            if not auth_type:
                print('Invalid input. Please select one of the provided options.\n')

        # Grouping the inputs meant for update_connection so that verify_ssl can be left out entirely if it is not disabled.
        # This way it only gets stored in the credentials file if it needs to be disabled.
        connection_kwargs = {"instance_label": instance_label, "hostname": server, "verify_ssl": verify_ssl, "username": username, "password": None, "api_key": None}

        # Password auth
        if auth_type == 'password':
            api_key = None
            while not username:
                username = input("Username: ")
            while not password:
                password = getpass.getpass()
            connection_kwargs.update({"username": username, "password": self.encryption.encrypt_string(password)})

        # API token auth
        else:
            username = password = None
            while not api_key:
                api_key = getpass.getpass(prompt='API Token: ')
            connection_kwargs["api_key"] = self.encryption.encrypt_string(api_key)

        try:
            verify_lhub_connection()
        except SSLError as err:
            verify_ssl = not query_yes_no('SSL certificate verification failed. Disable SSL verification?')
            if verify_ssl:
                raise err
            else:
                connection_kwargs['verify_ssl'] = verify_ssl
                verify_lhub_connection()

        # Drop any empty keys from kwargs before submitting
        connection_kwargs = {k: v for k, v in connection_kwargs.items() if v is not None}
        self.update_connection(**connection_kwargs)

    def list_configured_instances(self):
        return sorted(self.__full_config.dict().keys())

    def print_configured_instances(self):
        instances = self.list_configured_instances()
        if not instances:
            print("No stored instances")
        else:
            print(f"Stored instances:")
            for i in instances:
                print(f"    {i}")


class LogicHubConnection:
    __instance = None
    # preferences: Preferences = None
    credentials = None

    config: LhubConfig = None

    def __init__(self, instance_alias=None, logger: ExpectedLoggerTypes = None, log_level=None, **kwargs):
        self.log = logger or generate_logger(self_obj=self, instance_name=instance_alias, log_level=log_level)
        if log_level:
            self.log.setLevel(log_level)
        self.config = LhubConfig(logger=self.log, **kwargs)
        # ToDo Not yet used, but the groundwork has been laid. Revisit and enable this when ready to begin putting it to use.
        # if not self.preferences:
        #     self.preferences = Preferences()
        if instance_alias:
            self.instance = instance_alias

    @property
    def all_instances(self):
        return self.config.list_configured_instances()

    @property
    def instance(self):
        if not self.__instance:
            raise ValueError("Instance not set")
        return self.__instance

    @instance.setter
    def instance(self, name: str):
        name = name.strip()
        _new_credentials = self.config.get_instance(name)
        if not _new_credentials:
            self.log.warning(f"No instance found by name \"{name}.\" Creating new connection...")
            self.config.create_instance(name)
            _new_credentials = self.config.get_instance(name)

        self.__instance = name
        self.credentials = _new_credentials
