import os

from dotenv import load_dotenv

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()

JEV_MODEL = os.getenv("JEV_MODEL", "jev-latest")

# Score levels are situations, not degrees, and are ordered low to high.
QUESTIONS = {
    # Used to build the requirement dict
    "reasoning_difficulty": Score(
        instructions="How hard is the thinking the task requires?",
        criteria=[
            "Simple lookup, rewrite or formatting; no multi-step thinking.",
            "Straightforward task with a few steps, such as summarizing or routine classification.",
            "Careful multi-step analysis, such as comparing options or debugging a non-trivial problem.",
            "Hard reasoning, such as math proofs, complex algorithms or planning under many constraints.",
        ],
    ),
    "context_size": Score(
        instructions="How much input text must the model read to do this task?",
        criteria=[
            "A short message or a few sentences.",
            "A few pages, such as an email thread or a short article.",
            "A long document, such as a report or a book chapter.",
            "A book-length text or a large codebase.",
            "Several books or an entire document archive.",
        ],
    ),
    "needs_vision": Noul(
        instructions="The task requires understanding images, screenshots, charts or scanned documents.",
    ),
    "needs_tool_use": Noul(
        instructions="The task requires calling external tools, functions or APIs.",
    ),
    "needs_long_output": Noul(
        instructions="The task requires a very long response, such as a full report or thousands of words.",
    ),

    # Asked and logged only in V1 (no catalog field to filter on yet)
    "latency_sensitivity": Score(
        instructions="How quickly does the answer need to come back?",
        criteria=[
            "No time pressure; a batch or background job.",
            "A person waits for the answer, but a few seconds is fine.",
            "Real-time interaction where delays are noticeable, such as live chat or voice.",
        ],
    ),
    "cost_sensitivity": Score(
        instructions="How much does the cost of running this task matter?",
        criteria=[
            "Cost is not a concern; answer quality is what matters.",
            "Cost matters somewhat, within a normal budget.",
            "Very cost-sensitive: high volume, or an explicit wish to keep it cheap.",
        ],
    ),
    "is_coding": Noul(
        instructions="The task involves writing, reading or debugging code.",
    ),
    "task_type": Choice(
        instructions="Which kind of task is this?",
        criteria={
            "coding": "Writing, reviewing or debugging code.",
            "summarization": "Condensing a document or conversation.",
            "extraction_classification": "Pulling out fields or labelling text into categories.",
            "writing": "Drafting or rewriting prose, such as emails, articles or marketing copy.",
            "analysis_reasoning": "Analysis, math or problem solving that needs careful reasoning.",
            "conversation_qa": "Answering questions or chatting.",
            "agent_workflow": "Carrying out multi-step work by calling tools.",
            "other": "None of the above.",
        },
    ),
}


def judge_task(task: str):
    api_key = os.environ["typesafe_api_key"]  # SDK default name is uppercase, so pass this one explicitly

    with TypeSafeClient(api_key=api_key, model=JEV_MODEL) as client:
        return client.system_one(state={"task": task}, questions=QUESTIONS).model_dump().get("answers", {})


if __name__ == "__main__":
    tasks = [
        "Write a Python function that parses a CSV file and returns the rows as dictionaries.",
        "Here is a screenshot of our dashboard. Describe what the chart shows and any anomalies.",
        "What is the capital of Australia?",
        "Prove that the sum of two even integers is even, and then generalize the proof to modular arithmetic.",
        "Classify 2 million customer support tickets into 12 categories as cheaply as possible.",
        "Act as a travel agent: search flights, compare hotel prices through the booking API, and book the best option.",
        "Write a 5,000-word long-form report on renewable energy trends from these 40 research papers.",
        "Live voice assistant that must reply to the caller in under a second.",
    ]
    for task in tasks:
        print(task)
        print(type(judge_task(task)))
        print(judge_task(task))
        break