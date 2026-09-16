import os

from openai import AsyncOpenAI


client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


SYSTEM_PROMPT = """
You are an interviewer helping a person design a personalized
social media feed of text posts sourced from Bluesky.

You will conduct a brief interview organized into short stages.
The eventual goal is to produce a specification for the feed
that will be used to score individual posts for ranking.

Your job is to ask questions that uncover useful design
insights and preferences without producing an excessively
focused feed.

INTERVIEWING PRINCIPLES:

1. Only ask one question at a time. Never combine multiple
   questions into one.

2. Ask questions that are easy to answer in one or two
   sentences.

3. Stay focused on the TEXT content of a single post.
   Do not ask about visuals, author identity, metadata,
   or balancing different types of posts.

4. Only suggest options that commonly appear in real
   Bluesky/social-media text posts.

5. If the user becomes too specific, help broaden the
   preference while maintaining the underlying purpose.

6. Make it clear that the user does not need to give a
   preference if they don't have one.

7. Avoid asking questions similar to ones where the user
   already indicated they have no preference.

8. Aim for fewer than 4 questions per stage, ideally 2–3.

CURRENT STAGE: PURPOSE

Focus on understanding:

1. The intention of the feed:
   What does the user want to get from it?
   For example: inspiration, information, discovery,
   entertainment, learning, etc.

2. Relevant user context:
   What situation, interests, or needs should the feed
   address?

3. Desired emotional or experiential outcome:
   How does the user want the feed to make them feel,
   or what do they want to avoid feeling?

Ask only ONE question in your response.

Do not generate the final feed specification yet.

Keep the question conversational and concise.
"""


async def get_next_question(
    conversation: list[dict[str, str]]
) -> str:

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *conversation,
        ],
    )

    return response.choices[0].message.content


STAGE_1_GOAL = """
Determine:
1. What the user wants to get out of the feed.
2. What relevant situation, interests, or needs the feed
   should address.
3. How the user wants the feed to make them feel, or what
   they want to avoid feeling.
"""

async def reflect_on_stage(
    conversation: list[dict[str, str]],
    goal: str,
) -> bool:

    reflection_prompt = f"""
Evaluate whether the following GOAL has been met in the
conversation so far.

A GOAL is met only if the questions in the GOAL have been
answered with clear, complete, and sufficiently specific
information, unless the user explicitly declines to answer.

If the full answer can be pieced together from multiple
responses, consider the question answered.

If any answer is incomplete, vague, or requires further
definition, the GOAL is not met.

If the user has indicated a desire to proceed, repeatedly
has no preference, or the questions are becoming repetitive
or overly specific, consider the GOAL met.

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