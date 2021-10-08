#-*-coding:utf-8-*-
"""
@FileName:
    log.py
@Description:
    Logger for registry and component
@CreateTime:
    2021/10/08 17:34
"""
import os
import sys
import logging

# import part
__all__ = ["logger", "getLogger"]

# by default, log level is logging.INFO
LEVEL = "info"
if "MNSIM_NOC_LOG_LEVEL" in os.environ:
    LEVEL = os.environ["MNSIM_NOC_LOG_LEVEL"]
LEVEL = getattr(logging, LEVEL.upper())
LOG_FORMAT = "%(asctime)s %(name)-16s %(levelname)7s: %(message)s"
logging.basicConfig(
    stream=sys.stdout, level=LEVEL,
    format=LOG_FORMAT, datefmt="%m/%d %I:%M:%S %p"
)

logger = logging.getLogger()
def addFile(self, filename):
    handler = logging.FileHandler(filename)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    self.addHandler(handler)
# logger.__class__.addFile = addFile
logging.Logger.addFile = addFile

def getLogger(name):
    return logger.getChild(name)
