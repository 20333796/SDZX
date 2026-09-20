"""测试内置 ask_user_question 工具的格式契约。"""

import json

import pytest

from yuxi.agents.toolkits.buildin import tools


def test_ask_user_question_interrupt_payload_and_result_format(monkeypatch):
    captured_payloads = []
    expected_answer = {"style": "simple"}
    questions = [
        {
            "question_id": "style",
            "question": "选择界面风格",
            "options": [
                {"label": "简洁 (Recommended)", "value": "simple"},
                {"label": "详细", "value": "detailed"},
            ],
            "multi_select": False,
            "allow_other": False,
        }
    ]

    def fake_interrupt(payload):
        captured_payloads.append(payload)
        return expected_answer

    monkeypatch.setattr(tools, "interrupt", fake_interrupt)

    result = tools.ask_user_question.func(questions=questions)

    assert captured_payloads == [{"questions": questions, "source": "ask_user_question"}]
    assert result == {"questions": questions, "answer": expected_answer}


def test_ask_user_question_accepts_json_string_questions(monkeypatch):
    captured_payloads = []

    monkeypatch.setattr(tools, "interrupt", lambda payload: captured_payloads.append(payload) or {"q-1": "A"})

    result = tools.ask_user_question.func(
        questions=json.dumps(
            [
                {
                    "question": "选择一个选项",
                    "options": ["A", "B"],
                    "allow_other": False,
                }
            ],
            ensure_ascii=False,
        )
    )

    assert captured_payloads[0]["source"] == "ask_user_question"
    assert captured_payloads[0]["questions"] == [
        {
            "question_id": "q-1",
            "question": "选择一个选项",
            "options": [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}],
            "multi_select": False,
            "allow_other": False,
        }
    ]
    assert result["answer"] == {"q-1": "A"}


def test_ask_user_question_accepts_json_with_trailing_model_text(monkeypatch):
    captured_payloads = []
    questions = json.dumps(
        [
            {
                "question_id": "scope",
                "question": "需要全面综述还是聚焦某类方法？",
                "options": ["全面综述", "聚焦经验公式"],
            }
        ],
        ensure_ascii=False,
    )
    malformed_model_argument = f"{questions}\n我将等待用户选择后继续。"

    monkeypatch.setattr(tools, "interrupt", lambda payload: captured_payloads.append(payload) or {"scope": "全面综述"})

    result = tools.ask_user_question.func(questions=malformed_model_argument)

    assert captured_payloads[0]["questions"][0]["question"] == "需要全面综述还是聚焦某类方法？"
    assert result["answer"] == {"scope": "全面综述"}


def test_ask_user_question_rejects_empty_questions():
    with pytest.raises(ValueError, match="questions 至少需要包含一个有效问题"):
        tools.ask_user_question.func(questions=[])
