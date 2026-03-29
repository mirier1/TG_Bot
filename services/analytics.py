from database import AsyncSessionLocal
from models import UserActivity

async def log_activity(user_id: int, action: str, target_id: int = None, details: str = None):
    async with AsyncSessionLocal() as session:
        activity = UserActivity(
            user_id=user_id,
            action=action,
            target_id=target_id,
            details=details
        )
        session.add(activity)
        await session.commit()