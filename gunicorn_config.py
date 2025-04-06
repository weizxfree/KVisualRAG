from logging.config import dictConfig
from app.core.config import settings

loglevel = settings.log_level
accesslog = settings.log_file
errorlog = settings.log_file
workers = 10  # Number of worker processes
bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 0  # 设置超时时间为 120 秒

# 日志配置
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": settings.log_file,
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": True,
            },
            "gunicorn.error": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            "gunicorn.access": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
        },
    }
)
