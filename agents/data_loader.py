    def __init__(self):
        """Initialize DataLoader agent."""
        self.name = "DataLoader"
        self.logger = get_logger("DataLoader")
        self.loaded_data = None
        self.metadata = {}
        self.logger.info("DataLoader initialized")