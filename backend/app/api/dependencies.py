from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings, get_settings
from app.db.session import get_database_session

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseSessionDep = Annotated[AsyncSession, Depends(get_database_session)]
