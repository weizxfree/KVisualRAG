from fastapi import FastAPI, APIRouter, HTTPException, Request
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, List, Type, Optional
from pydantic import BaseModel
from app.utils.validation import validate_json
from app.utils.middlewares import LoggingMiddleware
from app.core.logging import logger
from app.utils.error_handlers import (
    http_exception_handler,
    general_exception_handler,
)
from app.core.config import settings


class FastAPIFramework:
    def __init__(self, debug_mode: bool):
        self.app = FastAPI(debug=debug_mode)
        #self.app.add_middleware(LoggingMiddleware)
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self.app.add_exception_handler(HTTPException, http_exception_handler)
        self.app.add_exception_handler(Exception, general_exception_handler)
        logger.info("FastAPI Framework initialized")

    def create_router(self, prefix: str) -> APIRouter:
        return APIRouter(prefix=prefix)

    def register_task(
        self,
        router: APIRouter,
        path: str,
        task_function: Callable[[Any], Any],
        request_model: Optional[Type[BaseModel]] = None,
        methods: List[str] = ["GET"],
        is_async: bool = False,
    ):
        if is_async:

            async def async_wrapper(request: Request):
                try:
                    if request_model:
                        body = await request.json()
                        validated_data = validate_json(request_model, body)
                        result = await task_function(**validated_data.model_dump())
                    else:
                        result = await task_function()
                    return {"result": result}
                except HTTPException as e:
                    raise e
                except Exception as e:
                    logger.error(
                        f"Error executing async task {task_function.__name__}: {e}"
                    )
                    raise HTTPException(status_code=500, detail="Task execution failed")

            router.add_api_route(path, async_wrapper, methods=methods)
        else:

            async def sync_wrapper(request: Request):
                loop = asyncio.get_event_loop()
                try:
                    if request_model:
                        body = await request.json()
                        validated_data = validate_json(request_model, body)
                        func_args = validated_data.model_dump()
                        result = await loop.run_in_executor(
                            self.executor, lambda: task_function(**func_args)
                        )
                    else:
                        result = await loop.run_in_executor(
                            self.executor, task_function
                        )
                    return {"result": result}
                except HTTPException as e:
                    raise e
                except Exception as e:
                    logger.error(f"Error executing task {task_function.__name__}: {e}")
                    raise HTTPException(status_code=500, detail="Task execution failed")

            router.add_api_route(path, sync_wrapper, methods=methods)

    def include_router(self, router: APIRouter):
        self.app.include_router(router)
        logger.info(f"Router with prefix {router.prefix} included")

    def get_app(self):
        return self.app
