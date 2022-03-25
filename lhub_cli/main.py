import lhub
from .connection_manager import LogicHubConnection
from .actions import Actions


class LogicHubCLI:

    def __init__(self, instance_name, log_level=None):
        # ToDo:
        #  * Move the logging function out of lhub and into lhub_cli
        #  * Standardize better w/ the "logging" package
        self.instance_name = instance_name
        self.__config = LogicHubConnection(instance_name)
        self.session = lhub.LogicHub(
            **self.__config.credentials.to_dict(),
            api_key=self.__config.credentials.api_key,
            password=self.__config.credentials.password,
            log_level=log_level
        )
        self.log = self.session.api.log
        self.actions = Actions(
            session=self.session,
            config=self.__config,
            instance_label=self.__config.instance
        )
