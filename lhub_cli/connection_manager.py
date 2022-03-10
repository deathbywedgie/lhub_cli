from pathlib import Path
import os
from configobj import ConfigObj
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lhub import LogicHub
from .encryption import Encryption
import getpass
from .common.config import dict_to_ini_file

# Over-writable/configurable static variables
LHUB_CONFIG_PATH = os.path.join(str(Path.home()), ".logichub")
CREDENTIALS_FILE_NAME = "credentials"
PREFERENCES_FILE_NAME = "preferences"

# Ensure that the path exists
__lhub_path = Path(LHUB_CONFIG_PATH)
__lhub_path.mkdir(parents=True, exist_ok=True)


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


class Connection:
    def __init__(self, **kwargs):
        self.hostname = kwargs.get("hostname")
        self.api_key = kwargs.get("api_key")
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.verify_ssl = kwargs.get("verify_ssl") or True
        assert self.hostname, "Server hostname not provided"
        if not self.api_key:
            assert self.password, "Neither an API key nor a password were provided in the connection config"
            assert self.username, "Username not provided"


class LhubConfig:
    __full_config: ConfigObj = None
    credentials_file_name = CREDENTIALS_FILE_NAME

    def __init__(self):
        self.credentials_path = os.path.join(LHUB_CONFIG_PATH, self.credentials_file_name)
        self.__load_credentials_file()
        self.encryption = Encryption(LHUB_CONFIG_PATH)

    def __load_credentials_file(self):
        if not os.path.exists(self.credentials_path):
            dict_to_ini_file({}, self.credentials_path)
        self.__full_config = ConfigObj(self.credentials_path)

    def reload(self):
        self.__load_credentials_file()

    def update_connection(self, instance_label, **kwargs):
        if not self.__full_config.get(instance_label):
            self.__full_config[instance_label] = kwargs
        else:
            self.__full_config[instance_label].update(kwargs)
        dict_to_ini_file(self.__full_config.dict(), self.credentials_path)

    def delete_connection(self, instance_label):
        if not self.__full_config.get(instance_label):
            return
        else:
            del self.__full_config[instance_label]
        dict_to_ini_file(self.__full_config.dict(), self.credentials_path)

    def get_instance(self, instance_label):
        if instance_label not in self.__full_config:
            return
        # Make a copy of the dict, otherwise this will only work once, and it
        # will fail with a decryption error any subsequent calls for the same instance
        _credentials = {k: v for k, v in self.__full_config[instance_label].items()}
        if _credentials.get('password'):
            _credentials['password'] = self.encryption.decrypt_string(_credentials['password'])
        if _credentials.get('api_key'):
            _credentials['api_key'] = self.encryption.decrypt_string(_credentials['api_key'])
        return Connection(**_credentials)

    def create_instance(self, instance_label):
        _server = _username = _password = _disable_warnings = _auth_type = _api_key = ""
        while not _server:
            _server = input("Server hostname or IP: ")

        while _auth_type not in ('password', 'api_key'):
            _auth_type = input('Enter "1" for password auth or "2" for API token auth:\n').strip()
            if _auth_type == '1':
                _auth_type = "password"
            elif _auth_type == '2':
                _auth_type = 'api_key'
            else:
                print('Invalid input\n')

        # Password auth
        if _auth_type == 'password':
            _api_key = None
            while not _username:
                _username = input("Username: ")
            while not _password:
                _password = getpass.getpass()

        # API token auth
        else:
            _username = _password = None
            while not _api_key:
                _api_key = getpass.getpass(prompt='API Token: ')

        # verify_ssl = query_yes_no('Verify SSL?', 'y')
        verify_ssl = True
        while _disable_warnings.lower() not in ('y', 'n'):
            _disable_warnings = input("Verify SSL? (y or n) ").lower()
            if not _disable_warnings or _disable_warnings == 'y':
                verify_ssl = True
                break
            elif _disable_warnings == 'n':
                verify_ssl = False

        # verify_ssl = False if _disable_warnings == 'n' else True
        _ = LogicHub(hostname=_server, username=_username, password=_password, api_key=_api_key, verify_ssl=verify_ssl)
        if _password:
            encrypted_password = self.encryption.encrypt_string(_password)
            self.update_connection(instance_label, hostname=_server, username=_username, password=encrypted_password, verify_ssl=verify_ssl)
        else:
            encrypted_token = self.encryption.encrypt_string(_api_key)
            self.update_connection(instance_label, hostname=_server, api_key=encrypted_token, verify_ssl=verify_ssl)
        self.reload()

    def list_configured_instances(self):
        instances = sorted(self.__full_config.dict().keys())
        if not instances:
            print("No stored instances")
        else:
            print(f"Stored instances:")
            for i in instances:
                print(f"    {i}")


class LogicHubSession:
    __instance = None
    # preferences: Preferences = None
    credentials = None

    # ToDo Hide this (dunder) when finished developing
    config: LhubConfig = None

    def __init__(self, instance_alias=None):
        self.config = LhubConfig()
        # ToDo Not yet used, but the groundwork has been laid. Revisit and enable this when ready to begin putting it to use.
        # if not self.preferences:
        #     self.preferences = Preferences()
        if instance_alias:
            self.instance = instance_alias

    @property
    def instance(self):
        if not self.__instance:
            raise ValueError("Instance not set")
        return self.__instance

    @instance.setter
    def instance(self, name: str):
        name = name.strip()
        self.config.reload()
        _updated_config = LhubConfig()
        _new_credentials = _updated_config.get_instance(name)
        if not _new_credentials:
            self.config.create_instance(name)
            _new_credentials = _updated_config.get_instance(name)

        self.__instance = name
        self.config = _updated_config
        self.credentials = _new_credentials

        # ToDo Logic here for prompting for credentials, test them, and then save an updated credentials file

        # ToDo Also use this class to invoke the LogicHub class from lhub_pw.py. When the instance is changed, create a new LogicHub instance
