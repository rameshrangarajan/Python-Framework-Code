import logging
import utils
import os
from logging.handlers import TimedRotatingFileHandler

class log:

    def getLogger():

        if not os.path.exists("./logs"):
            os.mkdir("./logs")
        logging.basicConfig(format="%(asctime)s [%(filename)-25.25s] [%(levelname)-5.5s]  %(message)s",
                            handlers=[TimedRotatingFileHandler('./logs/log', when="midnight", interval=1, utc=False), logging.StreamHandler(),
                                      ])
        config = utils.config_parser()
        log_level = config.get('generic', 'log_level')

        logger = logging.getLogger()
        if log_level == "DEBUG":
            logger.setLevel(logging.DEBUG)

        if log_level == "INFO" or log_level == "":
            logger.setLevel(logging.INFO)

        if log_level == "ERROR":
            logger.setLevel(logging.ERROR)

        return logger

    def info(self, msg, *args):
        logger = log.getLogger()
        if not all(args):
            logger.info(msg)
        else:
            logger.info(msg, *args)

    def warning(self, msg, *args):
        logger = log.getLogger()
        if not all(args):
            logger.warning(msg)
        else:
            logger.warning(msg, *args)

    def exception(self, msg, *args):
        logger = log.getLogger()
        if not all(args):
            logger.exception(msg)
        else:
            logger.exception(msg, *args)

    def error(self, msg, *args):
        logger = log.getLogger()
        if not all(args):
            logger.error(msg)
        else:
            logger.error(msg, *args)