from durabletask import task


class ReplaySafeLogger():
    def __init__(self, logger):
        self.logger = logger

    def info(self, ctx: task.OrchestrationContext, message):
        if not ctx.is_replaying:
            self.logger.info(message)

    def error(self, ctx: task.OrchestrationContext, message):
        if not ctx.is_replaying:
            self.logger.error(message)
    
    def debug(self, ctx: task.OrchestrationContext, message):
        if not ctx.is_replaying:
            self.logger.debug(message)

    def warning(self, ctx: task.OrchestrationContext, message):
        if not ctx.is_replaying:
            self.logger.warning(message)