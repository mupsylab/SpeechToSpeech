import fastapi
from logging import getLogger
logger = getLogger(__name__)

from ..utils.snowflake import generate_snowflake_id
from . import session_manager

router = fastapi.APIRouter(prefix="/api/account")
@router.get("/login")
def login():
    session_id = str(generate_snowflake_id())
    session_manager.set(session_id, dict())
    logger.debug("login session: %s" % session_id)

    response = fastapi.responses.JSONResponse({
        "session_id": session_id
    })
    response.set_cookie("session", session_id, max_age=3600)
    return response

@router.get("/logout")
def logout(request: fastapi.Request):
    session_id = request.cookies.get("session")
    session_manager.delete(session_id)
    logger.debug("logout session: %s" % session_id)

    response = fastapi.Response()
    response.delete_cookie("session")
    return response

@router.get("/islogin")
def islogin(request: fastapi.Request):
    session_id = request.cookies.get("session")
    logger.debug("judge session: %s" % session_id)

    return fastapi.responses.JSONResponse({
        "is_login": session_manager.exist(session_id),
        "session_id": session_id
    })
