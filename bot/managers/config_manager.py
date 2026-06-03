class ConfigManager:
    _instance = None

    @property
    def config(self):
        if self._config is None:
            raise ValueError(
                "Config not initialized. Call initialize() first.")
        return self._config

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_config'):
            self._config = None

    def initialize(self, config):
        self._config = config

    def get_logging_config(self):
        return self.config.get('logging', {})
