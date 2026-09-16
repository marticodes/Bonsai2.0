from fastapi import APIRouter
from pydantic import BaseModel

from app.services.interviewer import get_next_question


router = APIRouter(
    prefix="/api/interview",
    tags=["interview"],
)


class InterviewRequest(BaseModel):
    conversation: list[dict[str, str]]


class InterviewResponse(BaseModel):
    message: str


# FIRST-API: POST /api/interview/message
@router.post("/message", response_model=InterviewResponse)
async def send_message(request: InterviewRequest):

    response = await get_next_question(
        request.conversation
    )

    return InterviewResponse(
        message=response
    )

