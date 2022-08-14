from typing import List

import lhub
from .connection_manager import LogicHubConnection
from .actions import Actions
from .log import generate_logger, ExpectedLoggerTypes
import asyncio


class LogicHubCLI:

    def __init__(self, instance_name, log_level=None, logger: ExpectedLoggerTypes = None, **kwargs):
        # ToDo:
        #  * Move the logging function out of lhub and into lhub_cli
        #  * Standardize better w/ the "logging" package
        self.instance_name = instance_name
        credentials_file_name = kwargs.pop("credentials_file_name", None)
        self.log = logger or generate_logger(name=__name__, instance_name=self.instance_name, level=log_level)
        if log_level and hasattr(self.log, "setLevel"):
            self.log.setLevel(log_level)
        self.log.debug(f"Initializing config")
        self.__config = LogicHubConnection(instance_alias=instance_name, credentials_file_name=credentials_file_name)
        self.log = self.log.new(hostname=self.hostname)
        self.log.debug(f"Initializing connection")
        self.session = lhub.LogicHub(
            **self.__config.credentials.to_dict(),
            api_key=self.__config.credentials.api_key,
            password=self.__config.credentials.password,
            logger=self.log,
            **kwargs
        )
        self.actions = Actions(
            session=self.session,
            config=self.__config,
            instance_label=self.__config.instance,
            logger=self.log
        )

    @property
    def hostname(self):
        return self.__config.credentials.hostname

    @property
    def auth_type(self):
        return self.__config.credentials.auth_type


class LogicHubBulkCLI:
    sessions: List[LogicHubCLI] = None

    def __init__(self, credentials_file_name: str = None, instances: list = None, log_progress=False, *args, **kwargs):
        self.log_progress = log_progress is True
        self.credentials_file_name = credentials_file_name
        __config = LogicHubConnection(credentials_file_name=credentials_file_name)
        log = __config.log
        self.instances = instances
        if not self.instances:
            self.instances = __config.all_instances

        self.instances.sort()
        if self.log_progress:
            log.info(f"Pre-connecting to all instances: {', '.join(self.instances)}")

        self.sessions = asyncio.run(self.connect_to_multiple(*args, **kwargs))

    async def connect_to_instance(self, instance_alias, *args, **kwargs):
        _session = LogicHubCLI(instance_name=instance_alias, credentials_file_name=self.credentials_file_name, *args, **kwargs)
        if self.log_progress:
            _session.log.info(f"Connected to {_session.instance_name} ({_session.hostname})")
        return _session

    async def connect_to_multiple(self, *args, **kwargs):
        return await asyncio.gather(*[self.connect_to_instance(i, *args, **kwargs) for i in self.instances])


def list_all_instances(credentials_file_name=None):
    config = LogicHubConnection(credentials_file_name=credentials_file_name)
    return sorted(config.all_instances)
