import os
from openai import AsyncOpenAI


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# STAGE 1 — PURPOSE
# ============================================================

STAGE_1_PROMPT = """
You are an interviewer helping a person design a personalized
social media feed of text posts sourced from Bluesky.

The eventual goal is to produce a specification for the feed
that will be used to score individual posts for ranking.

CURRENT STAGE: PURPOSE

Your goal in this stage is to understand:

1. What the user wants to get from their feed.
   Examples include inspiration, information, discovery,
   entertainment, learning, staying informed, etc.

2. What relevant situation, interests, or needs the feed
   should address.

3. How the user wants the feed to make them feel or what
   they want to avoid feeling.

INTERVIEWING PRINCIPLES:

- Ask only ONE question at a time.
- Questions should be easy to answer in one or two sentences.
- Focus on the TEXT content of a SINGLE post.
- Do not ask about visuals, authors, metadata, or feed balance.
- Only suggest options that commonly appear in real
  Bluesky/social-media text posts.
- Do not make the feed unnecessarily narrow.
- If the user becomes too specific, help broaden the preference
  while maintaining the underlying purpose.
- Make it clear that the user does not need to give a preference
  if they do not have one.
- Avoid repeating a question this stage has already asked.
- This stage should ask 2–3 questions. Count only questions
  from THIS stage, not earlier stages.

Keep the question conversational and concise.

Ask exactly ONE question in your response.

This interview has later stages. Do not wrap up, thank the
user for finishing, or say you have enough information.

Do not generate the final feed specification yet.
"""


STAGE_1_GOAL = """
Determine:

1. What the user wants to get out of the feed.
2. What relevant situation, interests, or needs the feed
   should address.
3. How the user wants the feed to make them feel, or what
   they want to avoid feeling.
"""


# ============================================================
# STAGE 2 — TOPICS / CONTENT
# ============================================================

STAGE_2_PROMPT = """
You are continuing an interview to design a personalized
Bluesky feed.

CURRENT STAGE: TOPICS AND CONTENT

Your goal is to understand:

1. Topics or content the user wants to see.
2. Peripheral or adjacent topics that could also be useful.
3. Whether the user wants specific subtopics or broader
   topic coverage.
4. Topics or types of content the user wants to avoid.

INTERVIEWING PRINCIPLES:

- Ask only ONE question at a time.
- Questions should be easy to answer in one or two sentences.
- Focus on the TEXT content of a SINGLE post.
- Do not ask about visuals, authors, metadata, or feed balance.
- Only suggest topics or content types that commonly appear
  in real Bluesky/social-media text posts.
- Do not make the feed unnecessarily narrow.
- If the user becomes too specific, help broaden the preference
  while maintaining the underlying purpose.
- Make it clear that the user does not need to give a preference
  if they do not have one.
- Avoid repeating a question this stage has already asked.
- This stage should ask 2–3 questions. Count only questions
  from THIS stage, not earlier stages.

Keep the question conversational and concise.

Ask exactly ONE question in your response.

This interview has later stages. Do not wrap up, thank the
user for finishing, or say you have enough information.

Do not generate the final feed specification yet.
"""


STAGE_2_GOAL = """
Determine:

1. What topics or content the user wants to see.
2. What peripheral or adjacent topics could also be useful.
3. How focused or broad the user wants those topics to be.
4. What topics or types of content the user wants to avoid.
"""


# ============================================================
# STAGE 3 — POST QUALITIES
# ============================================================

STAGE_3_PROMPT = """
You are continuing an interview to design a personalized
Bluesky feed.

CURRENT STAGE: POST QUALITIES

Now focus on the qualities that make an individual post
useful, interesting, or desirable to the user.

Determine what characteristics the user prefers in posts.

Examples of useful qualities may include:

- informative vs opinionated
- factual vs speculative
- practical vs theoretical
- detailed vs concise
- educational vs entertaining
- thoughtful vs casual
- original insights vs summaries
- actionable advice vs general discussion
- technical depth vs accessibility
- nuanced discussion vs simple explanations

Only suggest qualities that make sense for the user's
previously stated purpose and topics.

Also determine whether there are qualities the user wants
to avoid.

INTERVIEWING PRINCIPLES:

- Ask only ONE question at a time.
- Questions should be easy to answer in one or two sentences.
- Focus on the TEXT content of a SINGLE post.
- Do not ask about visuals, authors, metadata, or feed balance.
- Do not introduce irrelevant qualities.
- Use the user's previous answers to make questions relevant.
- Do not make the feed unnecessarily narrow.
- If the user becomes too specific, help broaden the preference.
- Make it clear that the user does not need to give a preference.
- Avoid repeating a question this stage has already asked.
- This stage should ask 2–3 questions. Count only questions
  from THIS stage, not earlier stages.

Previous stages covered purpose and topics. They did NOT
cover post qualities. You must still ask about qualities
even if the conversation already feels detailed.

Keep the question conversational and concise.

Ask exactly ONE question in your response.

This interview has a later stage after this one. Do not wrap
up, thank the user for finishing, or say you have enough
information.

Do not generate the final feed specification yet.
"""


STAGE_3_GOAL = """
Determine:

1. What qualities or characteristics make a post desirable
   for this user.
2. What qualities make a post especially useful or valuable
   in the context of their stated purpose and topics.
3. What qualities or characteristics the user wants to avoid.
"""


# ============================================================
# STAGE 4 — ANYTHING ELSE
# ============================================================

STAGE_4_PROMPT = """
You are finishing an interview to design a personalized
Bluesky feed.

CURRENT STAGE: ANYTHING ELSE

Review the conversation so far and determine whether there is
any important information about the desired feed that has not
yet been captured.

Ask exactly one concise question.

The purpose of this stage is NOT to repeat previous questions.

You must still ask a question. If nothing important is
missing, ask whether there is anything else they would like
the feed to consider.

Possible areas include:

- an important preference that has not been mentioned
- an important type of content to avoid
- an important contextual need
- an important distinction between desirable and undesirable
  posts

INTERVIEWING PRINCIPLES:

- Ask only ONE question.
- Keep it easy to answer.
- Focus on TEXT content of individual posts.
- Do not ask about visuals, authors, metadata, or feed balance.
- Do not repeat information already established.
- Do not make the feed unnecessarily narrow.

Do not generate the final feed specification yet.
"""


STAGE_4_GOAL = """
Determine whether there is any remaining important information
about the user's desired feed that has not already been captured.

The stage is complete if:

1. The user indicates there is nothing else important.
2. The user declines to provide additional preferences.
3. The conversation contains enough information to construct
   a useful feed specification.
4. Further questions would mostly repeat information already
   established.
"""


# ============================================================
# GET NEXT QUESTION
# ============================================================

async def get_next_question(
    conversation: list[dict[str, str]],
    stage: int = 1,
    questions_asked: int = 0,
) -> str:

    prompts = {
        1: STAGE_1_PROMPT,
        2: STAGE_2_PROMPT,
        3: STAGE_3_PROMPT,
        4: STAGE_4_PROMPT,
    }

    system_prompt = prompts.get(
        stage,
        STAGE_4_PROMPT,
    )

    turn_instruction = f"""
TURN RULES:
- The interview has 4 stages. You are in stage {stage}.
- Questions already asked in THIS stage: {questions_asked}.
- You MUST ask exactly one new question for this stage.
- Do not conclude the interview.
- Do not say you have enough information.
- Do not say "that's all I needed" or similar.
- End with a question mark.
"""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt + turn_instruction,
            },
            *conversation,
        ],
    )

    message = response.choices[0].message.content or ""

    if "?" not in message:
        retry = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt + turn_instruction,
                },
                *conversation,
                {
                    "role": "assistant",
                    "content": message,
                },
                {
                    "role": "user",
                    "content": (
                        "That was not a question. Ask exactly one "
                        "question for the current stage now."
                    ),
                },
            ],
        )
        message = retry.choices[0].message.content or message

    return message


# ============================================================
# REFLECTION
# ============================================================

async def reflect_on_stage(
    conversation: list[dict[str, str]],
    goal: str,
) -> bool:

    reflection_prompt = f"""
Evaluate whether the following GOAL has been met in the
conversation so far.

A GOAL is met only if the required information has been
answered with clear, complete, and sufficiently specific
information.

If the full answer can be pieced together from multiple
responses, consider the question answered.

If any important answer is incomplete or vague, the GOAL is
not met.

However, consider the GOAL met if:

- the user explicitly declines to answer,
- the user says they have no preference,
- the user wants to move on,
- the user repeatedly has no preference,
- further questions would become repetitive,
- further questions would make the feed unnecessarily narrow.

GOAL:

{goal}

Output exactly one word:

YES

or

NO

Do not provide explanations.
"""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": reflection_prompt,
            },
            *conversation,
        ],
    )

    result = response.choices[0].message.content.strip()

    return result == "YES"