from types import SimpleNamespace

from yuxi.agents.buildin.chatbot.prompt import build_prompt_with_context


def test_chatbot_prompt_declares_workspace_visibility_and_default_write_boundary():
    prompt = build_prompt_with_context(
        SimpleNamespace(
            workdir_path="/home/gem/user-data/projects/11111111-1111-4111-8111-111111111111",
            system_prompt="",
        )
    )

    assert "可以读取其他 Project 目录作为参考" in prompt
    assert "未经用户明确要求，不得在当前 Project Workdir 之外" in prompt
    assert "/home/gem/user-data/agents/skills/" in prompt
    assert "html:preview" not in prompt


def test_chatbot_prompt_requires_official_links_for_resource_recommendations():
    prompt = build_prompt_with_context(
        SimpleNamespace(
            workdir_path="/home/gem/user-data/projects/11111111-1111-4111-8111-111111111111",
            system_prompt="",
        )
    )

    assert "每条推荐都要给出可点击的 Markdown 链接" in prompt
    assert "不得猜测、拼接或编造 URL" in prompt
    assert "必须继续调用 `web_search`" in prompt


def test_chatbot_prompt_routes_general_questions_without_forcing_knowledge_search():
    prompt = build_prompt_with_context(
        SimpleNamespace(
            workdir_path="/home/gem/user-data/projects/11111111-1111-4111-8111-111111111111",
            system_prompt="",
        )
    )

    assert "一般概念、原理、公式推导" in prompt
    assert "不调用检索工具" in prompt
    assert "明显不相关时不得调用 `query_kb`" in prompt
