from fastapi import APIRouter
from pydantic import AliasChoices, BaseModel, Field

from app.services.interviewer import (
    get_next_question,
    reflect_on_stage,
    STAGE_1_GOAL,
    STAGE_2_GOAL,
    STAGE_3_GOAL,
    STAGE_4_GOAL,
)

from app.services.specification import (
    generate_feed_specification,
    FeedSpecification,
)


router = APIRouter(
    prefix="/api/interview",
    tags=["interview"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class InterviewRequest(BaseModel):
    conversation: list[dict[str, str]]
    stage: int = 1
    stage_question_count: int = Field(
        default=0,
        validation_alias=AliasChoices(
            "stage_question_count",
            "stageQuestionCount",
        ),
    )


class InterviewResponse(BaseModel):
    message: str
    stage: int
    stage_complete: bool
    stage_question_count: int


class SpecificationRequest(BaseModel):
    conversation: list[dict[str, str]]


# ============================================================
# STAGE CONFIGURATION
# ============================================================

STAGE_GOALS = {
    1: STAGE_1_GOAL,
    2: STAGE_2_GOAL,
    3: STAGE_3_GOAL,
    4: STAGE_4_GOAL,
}


# Minimum number of user answers before reflection is allowed
MIN_QUESTIONS = {
    1: 2,
    2: 2,
    3: 2,
    4: 1,
}


# Maximum number of user answers in a stage
MAX_QUESTIONS = {
    1: 3,
    2: 3,
    3: 3,
    4: 2,
}


# ============================================================
# INTERVIEW
# ============================================================

@router.post(
    "/message",
    response_model=InterviewResponse,
)
async def send_message(request: InterviewRequest):

    current_stage = request.stage

    # Keep stage within valid range
    if current_stage < 1:
        current_stage = 1

    if current_stage > 4:
        current_stage = 4

    # The frontend sends the number of questions already asked
    # in this stage. Increment it because this request contains
    # the user's newest answer.
    question_count = request.stage_question_count + 1

    minimum_reached = (
        question_count >= MIN_QUESTIONS[current_stage]
    )

    maximum_reached = (
        question_count >= MAX_QUESTIONS[current_stage]
    )

    # --------------------------------------------------------
    # Reflection
    # --------------------------------------------------------

    stage_complete = False

    if minimum_reached:
        goal = STAGE_GOALS[current_stage]

        stage_complete = await reflect_on_stage(
            request.conversation,
            goal,
        )

    # Never allow a stage to continue beyond its maximum.
    if maximum_reached:
        stage_complete = True

    # --------------------------------------------------------
    # Move to next stage
    # --------------------------------------------------------

    next_stage = current_stage

    if stage_complete and current_stage < 4:
        next_stage = current_stage + 1
        # Completing the previous stage must not look like the
        # new stage is already finished.
        stage_complete = False

    # If Stage 4 is complete, there is no Stage 5 interviewer.
    # The frontend will use this signal to generate the
    # FeedSpecification.
    if current_stage == 4 and stage_complete:
        return InterviewResponse(
            message="The interview is complete.",
            stage=4,
            stage_complete=True,
            stage_question_count=question_count,
        )

    # --------------------------------------------------------
    # Generate next question
    # --------------------------------------------------------

    response = await get_next_question(
        request.conversation,
        stage=next_stage,
        questions_asked=(
            0 if next_stage != current_stage else question_count
        ),
    )

    # Reset question count when entering a new stage
    if next_stage != current_stage:
        next_question_count = 0
    else:
        next_question_count = question_count

    return InterviewResponse(
        message=response,
        stage=next_stage,
        stage_complete=stage_complete,
        stage_question_count=next_question_count,
    )


# ============================================================
# FEED SPECIFICATION
# ============================================================

@router.post(
    "/specification",
    response_model=FeedSpecification,
)
async def create_specification(
    request: SpecificationRequest,
):

    specification = await generate_feed_specification(
        request.conversation
    )

    # Print specification in backend terminal
    print("\n" + "=" * 60)
    print("GENERATED FEED SPECIFICATION")
    print("=" * 60)
    print(specification.model_dump_json(indent=2))
    print("=" * 60 + "\n")

    return specification