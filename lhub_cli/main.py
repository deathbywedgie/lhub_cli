import lhub
from .connection_manager import LogicHubConnection
from .actions import Actions
from .log import generate_logger, ExpectedLoggerTypes


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
        self.__config = LogicHubConnection(instance_name, credentials_file_name=credentials_file_name)
        self.hostname = self.__config.credentials.hostname
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


def list_all_instances(credentials_file_name=None):
    config = LogicHubConnection(credentials_file_name=credentials_file_name)
    return sorted(config.all_instances)
