# Noul answers at or above this value count as "yes"
YES_THRESHOLD = 0.7

# Noul question -> boolean requirement field
NOUL_RULES = {
    "needs_vision": "vision",
    "needs_tool_use": "tool_call",
}

# needs_long_output (Noul) sets min_output to this many tokens
LONG_OUTPUT_MIN_TOKENS = 16_000

# reasoning_difficulty (Score): needs_reasoning is True when the probability of
# this level or higher reaches the threshold
REASONING_LEVEL = 2
REASONING_PROBABILITY = 0.5

# context_size (Score) level -> min_context in tokens (None = no requirement)
CONTEXT_LEVEL_TO_MIN_CONTEXT = {
    0: None,
    1: 16_000,
    2: 64_000,
    3: 200_000,
    4: 1_000_000,
}


def level_probabilities(answer: dict) -> dict[int, float]:
    # Keys can come back as strings after a JSON round trip (e.g. from the logs)
    return {int(level): p for level, p in answer["probabilities"].items()}


def probability_at_least(probabilities: dict[int, float], level: int) -> float:
    return sum(p for lvl, p in probabilities.items() if lvl >= level)


def median_level(probabilities: dict[int, float]) -> int:
    # Lowest level where the cumulative probability reaches 0.5
    cumulative = 0.0
    for level in sorted(probabilities):
        cumulative += probabilities[level]
        if cumulative >= 0.5:
            return level
    return max(probabilities)


def judgments_to_requirement(answers: dict) -> dict:
    # answers has the shape of response.model_dump()["answers"].
    # A question missing from answers leaves its field out of the requirement.
    requirement = {}

    for question, field in NOUL_RULES.items():
        if question in answers:
            requirement[field] = answers[question]["noul"] >= YES_THRESHOLD

    if "needs_long_output" in answers and answers["needs_long_output"]["noul"] >= YES_THRESHOLD:
        requirement["min_output"] = LONG_OUTPUT_MIN_TOKENS

    if "reasoning_difficulty" in answers:
        probabilities = level_probabilities(answers["reasoning_difficulty"])
        requirement["needs_reasoning"] = probability_at_least(probabilities, REASONING_LEVEL) >= REASONING_PROBABILITY

    if "context_size" in answers:
        level = median_level(level_probabilities(answers["context_size"]))
        min_context = CONTEXT_LEVEL_TO_MIN_CONTEXT[level]
        if min_context:
            requirement["min_context"] = min_context

    return requirement

if __name__ == "__main__":
    jev_resp = {
    'reasoning_difficulty':
    {
        'type': 'score',
        'score': 0.7,
        'confidence': 0.7,
        'legend':
        {
            0: 'Simple lookup, rewrite or formatting; no multi-step thinking.',
            1: 'Straightforward task with a few steps, such as summarizing or routine classification.',
            2: 'Careful multi-step analysis, such as comparing options or debugging a non-trivial problem.',
            3: 'Hard reasoning, such as math proofs, complex algorithms or planning under many constraints.'
        },
        'probabilities':
        {
            0: 0.3,
            1: 0.7,
            2: 0.0,
            3: 0.0
        }
    },
    'context_size':
    {
        'type': 'score',
        'score': 0.0,
        'confidence': 1.0,
        'legend':
        {
            0: 'A short message or a few sentences.',
            1: 'A few pages, such as an email thread or a short article.',
            2: 'A long document, such as a report or a book chapter.',
            3: 'A book-length text or a large codebase.',
            4: 'Several books or an entire document archive.'
        },
        'probabilities':
        {
            0: 1.0,
            1: 0.0,
            2: 0.0,
            3: 0.0,
            4: 0.0
        }
    },
    'needs_vision':
    {
        'type': 'noul',
        'noul': 0.02
    },
    'needs_tool_use':
    {
        'type': 'noul',
        'noul': 0.16
    },
    'needs_long_output':
    {
        'type': 'noul',
        'noul': 0.03
    },
    'latency_sensitivity':
    {
        'type': 'score',
        'score': 0.72,
        'confidence': 0.55,
        'legend':
        {
            0: 'No time pressure; a batch or background job.',
            1: 'A person waits for the answer, but a few seconds is fine.',
            2: 'Real-time interaction where delays are noticeable, such as live chat or voice.'
        },
        'probabilities':
        {
            0: 0.29,
            1: 0.7,
            2: 0.01
        }
    },
    'cost_sensitivity':
    {
        'type': 'score',
        'score': 0.03,
        'confidence': 0.97,
        'legend':
        {
            0: 'Cost is not a concern; answer quality is what matters.',
            1: 'Cost matters somewhat, within a normal budget.',
            2: 'Very cost-sensitive: high volume, or an explicit wish to keep it cheap.'
        },
        'probabilities':
        {
            0: 0.98,
            1: 0.02,
            2: 0.0
        }
    },
    'is_coding':
    {
        'type': 'noul',
        'noul': 0.98
    },
    'task_type':
    {
        'type': 'choice',
        'choice': 'coding',
        'confidence': 1.0,
        'probabilities':
        {
            'coding': 1.0,
            'summarization': 0.0,
            'extraction_classification': 0.0,
            'writing': 0.0,
            'analysis_reasoning': 0.0,
            'conversation_qa': 0.0,
            'agent_workflow': 0.0,
            'other': 0.0
        }
    }
}