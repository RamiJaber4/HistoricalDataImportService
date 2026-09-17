import csv
import io
import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

from db_manager import db
from deps import CurrentContext, get_current_context
from queue_manager import queue
from security import create_access_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = db.get_user_by_username(form_data.username)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    cred = {
        "sub": user_data["username"],
        "role": user_data["role"],
        "company_id": user_data["company_id"],
    }
    token = create_access_token(cred)
    return {
        "access_token": token,
        "token_type": "bearer",
    }


#---------------------------- idempotency ----------------------------
@router.post("/upload_file")
# @idempotent(storage_backend=memory_backend)
async def receive_file(file: UploadFile = File(...), context: CurrentContext = Depends(get_current_context)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="The file should be csv format"
        )
    if context.role == 'admin':
        logger.info("Admin is heeeeeeeeeeeeeeeeeeeeeeeeeeeere")

    raw_data = await file.read()
    text_data = io.StringIO(raw_data.decode())

    reader = csv.DictReader(text_data)

    data = []

    for i, row in enumerate(reader, start=1):
        data.append({"row_number": i, "data": row})

    track_id = str(uuid.uuid4())

    await queue.put((track_id, data, file.filename))

    return {
        "file_tracking_id": track_id
    }


@router.get("/list_imports")
async def list_imports():
    return db.get_imports()
