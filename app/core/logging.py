import logging
from .config import settings

# 日志配置
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    filename=settings.log_file,
    filemode="a",
)
logger = logging.getLogger(__name__)
