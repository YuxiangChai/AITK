from openai import OpenAI

from aitk import answer_correct_judge
from aitk.utils.xml_processor import ETParser


def task() -> dict:
    return {
        "task": "In bluecoins, how much did I spend on Dec 9, 2024",
        "app": "bluecoins",
        "app_package": "com.rammigsoftware.bluecoins",
        "level": "medium",
        "max_steps": 15,
        "category": "single-page query",
        "essential_states": [
            "Bluecoins app is open",
            "Date is set to Dec 9, 2024",
            "Total expense is displayed",
        ],
    }


def eval(
    task: str,
    history: dict,  # history dictionary containing xml, screenshot and action
    answer: str = None,  # agent answer
    client: OpenAI = None,
    model_type: str = "gpt-4.1-mini",
) -> bool:

    parser = ETParser(history["xml"][-1])
    month_element = parser.get_element(
        "resource-id", "com.rammigsoftware.bluecoins:id/month_name"
    )

    if month_element is None:
        return False

    # if not dec 2024
    if month_element.attrib["text"] != "December 2024":
        return False

    date_element = parser.get_element_contains_from(
        "content-desc", "9", "content-desc", "Calendar"
    )

    # if not dec 9
    if date_element.attrib["checked"] == "false":
        return False

    no_transaction_element = parser.get_element(
        "resource-id", "com.rammigsoftware.bluecoins:id/empty_tab"
    )

    if no_transaction_element is not None:
        gt = "0.00"
        judge = answer_correct_judge(
            task,
            answer,
            gt,
            client,
            model_type,
        )
        return judge

    expense_element = parser.get_element_contains_from(
        "resource-id", "com.rammigsoftware.bluecoins:id/amount_tv", "text", "EXPENSE"
    )

    if expense_element is None:
        gt = "0.00"
        judge = answer_correct_judge(
            task,
            answer,
            gt,
            client,
            model_type,
        )
        return judge

    gt = expense_element.attrib["text"]
    judge = answer_correct_judge(
        task,
        answer,
        gt,
        client,
        model_type,
    )
    return judge
