import pytest

from app.data import EXTERNAL_RESOURCES
from app.routers.chat import build_reply
from app.schemas import ChatRequest
from app.modules.well_log import DEMO_LOG, WellLogAnalysisRequest, analyze_well_log, parse_well_log_file


def test_external_resources_have_unique_ids_and_safe_status() -> None:
    resource_ids = [resource.id for resource in EXTERNAL_RESOURCES]
    assert len(resource_ids) == len(set(resource_ids))
    assert all(resource.url or resource.status.value == "pending" for resource in EXTERNAL_RESOURCES)


def test_chat_reply_changes_by_mode() -> None:
    response = build_reply(ChatRequest(mode="inquiry", message="如何识别储层"))
    assert "如何识别储层" in response
    assert "证据" in response


def test_chat_reply_declares_when_no_published_source_exists() -> None:
    response = build_reply(ChatRequest(mode="conversation", message="储层"), has_citations=False)
    assert "没有可引用" in response


def test_demo_log_has_a_teaching_reservoir_interval() -> None:
    result = analyze_well_log(WellLogAnalysisRequest(points=DEMO_LOG))
    assert result.intervals[0].top_depth == 2101.0
    assert result.intervals[0].bottom_depth == 2102.5
    assert result.intervals[0].sample_count == 4


def test_csv_well_log_parser_normalizes_teaching_headers() -> None:
    points = parse_well_log_file(
        "teaching-log.csv",
        b"DEPT,GAMMA,ILD,PHI\n2100,100,5,0.12\n2100.5,60,30,0.2\n2101,55,35,0.22\n",
    )
    assert points[1].depth == 2100.5
    assert points[1].gr == 60
    assert points[1].rt == 30
    assert points[1].nphi == 0.2


def test_csv_well_log_parser_accepts_additional_curves() -> None:
    """Real teaching exports carry extra curves; they must not be rejected."""
    points = parse_well_log_file(
        "teaching-log.csv",
        b"DEPT,GAMMA,ILD,PHI,SP,CAL\n2100,100,5,0.12,-20,8.5\n2100.5,60,30,0.2,-18,8.4\n",
    )
    assert len(points) == 2
    assert points[1].depth == 2100.5
    assert points[1].gr == 60
    assert points[1].rt == 30
    assert points[1].nphi == 0.2


def test_well_log_parser_names_the_missing_curve() -> None:
    with pytest.raises(ValueError, match="missing: rt"):
        parse_well_log_file("teaching-log.csv", b"DEPT,GAMMA,PHI\n2100,100,0.12\n")


def test_well_log_parser_separates_non_numeric_from_out_of_range() -> None:
    with pytest.raises(ValueError, match="non-numeric gr"):
        parse_well_log_file("teaching-log.csv", b"DEPT,GAMMA,ILD,PHI\n2100,shale,5,0.12\n")
    with pytest.raises(ValueError, match="outside teaching ranges"):
        parse_well_log_file("teaching-log.csv", b"DEPT,GAMMA,ILD,PHI\n2100,300,5,0.12\n")


LAS_WITH_TRAILING_DEPTH = """~VERSION
 VERS. 2.0 : CWLS LOG ASCII STANDARD - VERSION 2.0
 WRAP. NO : ONE LINE PER DEPTH STEP
~WELL
 STRT.M 2100.0 : START DEPTH
 STOP.M 2101.0 : STOP DEPTH
 STEP.M 0.5 : STEP
 NULL. -999.25 : NULL VALUE
~CURVE INFORMATION
 GR.GAPI : GAMMA RAY
 RT.OHMM : RESISTIVITY
 NPHI.V/V : NEUTRON POROSITY
 DEPT.M : DEPTH
~A
 108 5 0.12 2100.0
 60 30 0.2 2100.5
 55 35 0.22 2101.0
"""


def test_las_well_log_parser_resolves_depth_by_mnemonic() -> None:
    """The depth track is not always the first curve in a LAS file."""
    points = parse_well_log_file("teaching-log.las", LAS_WITH_TRAILING_DEPTH.encode())
    assert len(points) == 3
    assert points[0].depth == 2100.0
    assert points[2].depth == 2101.0
    assert points[2].gr == 55
    assert points[2].rt == 35
