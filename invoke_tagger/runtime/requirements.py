import sys


from .package_analyzer import validate_requirements
from .config import (LOGGER_NAME, LOGGER_COLOR, LOGGER_LEVEL,REQUIREMENTS_PATH,)
from .logger import get_logger
from .cmd import run_cmd


logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)


def setup_tagger() -> None:
    logger.info("Check WD 1.4 Tagger requirements")
    if not validate_requirements(REQUIREMENTS_PATH):
        logger.info("Install WD 1.4 Tagger requirements")
        run_cmd([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_PATH.as_posix()])
    logger.info("Check WD 1.4 Tagger requirements done")
