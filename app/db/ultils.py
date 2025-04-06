from bson import ObjectId
from app.core.logging import logger


def format_page_response(result: dict, page: int, page_size: int):
    total = result.get("total", 0)
    return {
        "data": result.get("data", []),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def parse_aggregate_result(result):
    if not result:
        return {"data": [], "total": 0}

    # 正确提取分页数据和总数
    data = result[0].get("data", [])
    metadata = result[0].get("metadata", [])
    total = metadata[0].get("total", 0) if metadata else 0

    return {"data": data, "total": total}
