import lhub
from .connection_manager import LogicHubConnection
from .actions import Actions
from .log import DefaultLogger


class LogicHubCLI:

    def __init__(self, instance_name, logger=None, log_level=None, **kwargs):
        # ToDo:
        #  * Move the logging function out of lhub and into lhub_cli
        #  * Standardize better w/ the "logging" package
        self.instance_name = instance_name
        self.log = logger or DefaultLogger()
        if log_level:
            self.log.setLevel(log_level)
        credentials_file_name = kwargs.pop("credentials_file_name", None)
        self.log.debug(f"Initializing config: {instance_name=}")
        self.__config = LogicHubConnection(instance_name, credentials_file_name=credentials_file_name)
        hostname = self.__config.credentials.hostname
        self.log.debug(f"Initializing connection: {instance_name=} {hostname=}")
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
