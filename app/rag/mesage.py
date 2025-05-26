from app.db.mongo import get_mongo


async def find_parent_mesage(conversation_id, message_id):

    db = await get_mongo()

    message = None
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        return message

    for turn in conversation["turns"]:
        if message_id == turn["message_id"]:
            messages = {
                    "message_id": turn["message_id"],
                    "parent_message_id": turn["parent_message_id"],
                    "user_message": turn["user_message"],
                    "temp_db": turn["temp_db"],
                    "ai_message": turn["ai_message"],
                    "file_used": turn["file_used"],
                    "status": turn["status"],
                    "timestamp": turn["timestamp"].isoformat(),
                }
            
            break
    return messages


async def find_depth_parent_mesage(conversation_id, message_id, MAX_PARENT_DEPTH=5):
    
    parent_stack = []

    while message_id and len(parent_stack) < MAX_PARENT_DEPTH:
        parent_messages = await find_parent_mesage(conversation_id, message_id)
        message_id = parent_messages.get("parent_message_id","")
        parent_stack.append(parent_messages.get("ai_message"))
        parent_stack.append(parent_messages.get("user_message"))

    return parent_stack