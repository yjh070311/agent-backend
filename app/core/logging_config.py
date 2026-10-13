"""日志配置,按照相同规则输出，只需要配置一次handler和formatter，后面的logger都与根logger统一"""

import logging
import sys

LOG_FORMAT="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s "

def setup_logging(level:int=logging.INFO)->None:
    root=logging.getLogger()

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler=logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT,datefmt="%H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(level)