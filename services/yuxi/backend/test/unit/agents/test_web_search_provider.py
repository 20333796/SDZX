from unittest.mock import MagicMock, patch

from yuxi.agents.toolkits.buildin.tools import (
    _all_tool_instances,
    _create_bing_search,
    _create_doubao_search,
    _extra_registry,
    _register_web_search_tool,
    _resolve_web_search_provider,
)


def test_doubao_search_missing_key(monkeypatch):
    monkeypatch.delenv("DOUBAO_SEARCH_API_KEY", raising=False)
    doubao = _create_doubao_search()
    res = doubao.invoke({"query": "python"})
    assert res["error"] == "DOUBAO_SEARCH_API_KEY 未配置"
    assert res["results"] == []


def test_doubao_search_success_with_detailed_params(monkeypatch):
    monkeypatch.setenv("DOUBAO_SEARCH_API_KEY", "test_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ResponseMetadata": {},
        "Result": {
            "TimeCost": 150,
            "WebResults": [
                {
                    "Title": "Python 官网",
                    "Url": "https://www.python.org",
                    "Summary": "Python 编程语言官方网站",
                    "RankScore": 0.98,
                    "SiteName": "Python Org",
                    "PublishTime": "2026-01-01T00:00:00+08:00",
                }
            ],
        },
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        doubao = _create_doubao_search()
        res = doubao.invoke(
            {
                "query": "python 3.13",
                "count": 5,
                "time_range": "OneWeek",
                "sites": ["python.org", "github.com"],
                "block_hosts": ["badsite.com"],
                "content_format": "markdown",
            }
        )

        assert res["query"] == "python 3.13"
        assert len(res["results"]) == 1
        item = res["results"][0]
        assert item["title"] == "Python 官网"
        assert item["url"] == "https://www.python.org"
        assert item["content"] == "Python 编程语言官方网站"
        assert item["score"] == 0.98
        assert item["site_name"] == "Python Org"
        assert item["publish_time"] == "2026-01-01T00:00:00+08:00"

        # Verify payload mapping
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["Query"] == "python 3.13"
        assert payload["Count"] == 5
        assert payload["TimeRange"] == "OneWeek"
        assert payload["Filter"]["Sites"] == "python.org|github.com"
        assert payload["Filter"]["BlockHosts"] == "badsite.com"
        assert payload["ContentFormats"] == "markdown"


def test_register_web_search_tool_provider_selection(monkeypatch):
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "doubao")
    monkeypatch.setenv("DOUBAO_SEARCH_API_KEY", "key1")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    instances_before = len(_all_tool_instances)

    _register_web_search_tool()

    assert _extra_registry["web_search"].display_name == "豆包 网页搜索"
    assert len(_all_tool_instances) == instances_before + 1
    assert _all_tool_instances[-1].name == "web_search"


def test_web_search_defaults_to_bing_without_api_keys(monkeypatch):
    monkeypatch.delenv("WEB_SEARCH_PROVIDER", raising=False)
    monkeypatch.delenv("DOUBAO_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert _resolve_web_search_provider() == "bing"


def test_bing_search_parses_results(monkeypatch):
    html = """
    <ol><li class="b_algo"><h2><a href="https://example.edu/item">地质资料</a></h2>
    <div class="b_caption"><p>权威资料摘要</p></div></li></ol>
    """
    response = MagicMock()
    response.text = html
    response.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=response):
        result = _create_bing_search().invoke({"query": "地质资料", "count": 5})

    assert result["results"] == [
        {"title": "地质资料", "url": "https://example.edu/item", "content": "权威资料摘要"}
    ]
