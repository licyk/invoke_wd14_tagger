from .invoke_tagger.runtime.requirements import setup_tagger  # ty: ignore
from .invoke_tagger.runtime import logger  # ty: ignore
setup_tagger()

logger.info("Load WD1.4 Tagger Node")
from .invoke_tagger.node.wd_tagger import Wd14Tagger  # noqa: F401  # ty: ignore
logger.info("Load WD1.4 Tagger Node Done")