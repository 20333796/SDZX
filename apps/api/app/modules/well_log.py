from dataclasses import dataclass
import csv
from io import StringIO
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator


class WellLogPoint(BaseModel):
    depth: float = Field(ge=0)
    gr: float = Field(ge=0, le=250)
    rt: float = Field(ge=0, le=10000)
    nphi: float = Field(ge=-0.2, le=1)


class WellLogAnalysisRequest(BaseModel):
    points: list[WellLogPoint] = Field(min_length=3, max_length=5000)

    @model_validator(mode="after")
    def ensure_monotonic_depth(self) -> "WellLogAnalysisRequest":
        depths = [point.depth for point in self.points]
        if depths != sorted(depths):
            raise ValueError("Depth must be in ascending order")
        return self


class ReservoirInterval(BaseModel):
    top_depth: float
    bottom_depth: float
    sample_count: int
    mean_gr: float
    mean_rt: float
    confidence: str


class WellLogAnalysisResponse(BaseModel):
    intervals: list[ReservoirInterval]
    interpretation: str
    evidence: list[str]


class WellLogFileAnalysisResponse(BaseModel):
    points: list[WellLogPoint]
    analysis: WellLogAnalysisResponse


@dataclass(frozen=True)
class Thresholds:
    gr_max: float = 75.0
    rt_min: float = 20.0
    nphi_min: float = 0.05
    nphi_max: float = 0.35


def classify_points(points: list[WellLogPoint], thresholds: Thresholds = Thresholds()) -> list[bool]:
    return [
        point.gr <= thresholds.gr_max
        and point.rt >= thresholds.rt_min
        and thresholds.nphi_min <= point.nphi <= thresholds.nphi_max
        for point in points
    ]


def analyze_well_log(request: WellLogAnalysisRequest) -> WellLogAnalysisResponse:
    flags = classify_points(request.points)
    intervals: list[ReservoirInterval] = []
    start_index: int | None = None

    def close_interval(end_index: int) -> None:
        nonlocal start_index
        if start_index is None:
            return
        candidates = request.points[start_index:end_index]
        if len(candidates) >= 2:
            intervals.append(
                ReservoirInterval(
                    top_depth=candidates[0].depth,
                    bottom_depth=candidates[-1].depth,
                    sample_count=len(candidates),
                    mean_gr=round(sum(point.gr for point in candidates) / len(candidates), 1),
                    mean_rt=round(sum(point.rt for point in candidates) / len(candidates), 1),
                    confidence="教学判识：中等",
                )
            )
        start_index = None

    for index, is_candidate in enumerate(flags):
        if is_candidate and start_index is None:
            start_index = index
        if not is_candidate:
            close_interval(index)
    close_interval(len(request.points))

    if intervals:
        interpretation = f"识别到 {len(intervals)} 段可能储层。结果仅用于课程训练，应结合岩性、录井和区域地质资料复核。"
    else:
        interpretation = "未识别到满足教学阈值的连续储层段。建议核对曲线质量与课程案例背景。"

    return WellLogAnalysisResponse(
        intervals=intervals,
        interpretation=interpretation,
        evidence=[
            "GR 较低通常提示泥质含量相对较低。",
            "RT 较高可作为流体与孔隙条件的辅助证据，不能单独定性。",
            "NPHI 位于教学设定区间时，作为孔隙度响应的辅助判断。",
        ],
    )


DEMO_LOG = [
    WellLogPoint(depth=2100.0, gr=108, rt=5, nphi=0.12),
    WellLogPoint(depth=2100.5, gr=96, rt=7, nphi=0.13),
    WellLogPoint(depth=2101.0, gr=68, rt=24, nphi=0.17),
    WellLogPoint(depth=2101.5, gr=54, rt=37, nphi=0.21),
    WellLogPoint(depth=2102.0, gr=49, rt=42, nphi=0.23),
    WellLogPoint(depth=2102.5, gr=62, rt=31, nphi=0.19),
    WellLogPoint(depth=2103.0, gr=84, rt=13, nphi=0.14),
    WellLogPoint(depth=2103.5, gr=92, rt=9, nphi=0.11),
]


CSV_ALIASES = {
    "depth": {"depth", "dept", "de", "md"},
    "gr": {"gr", "gamma", "gamma_ray"},
    "rt": {"rt", "resistivity", "ild", "lld"},
    "nphi": {"nphi", "phi", "neutron_porosity"},
}

REQUIRED_CURVES = {"depth", "gr", "rt", "nphi"}
TEACHING_RANGES = "GR 0-250, RT 0-10000, NPHI -0.2-1"


def _enforce_required_curves(headers: dict[str, str | None], kind: str) -> None:
    """Accept files that carry the four teaching curves, ignoring extra curves."""
    missing = REQUIRED_CURVES - set(headers.values())
    if missing:
        raise ValueError(
            f"{kind} must contain depth, GR, RT and NPHI curves (missing: {', '.join(sorted(missing))})"
        )


def _canonical_curve_name(name: str) -> str | None:
    normalized = name.lower().strip().replace(" ", "_")
    return next((target for target, aliases in CSV_ALIASES.items() if normalized in aliases), None)


def _points_from_rows(rows: list[dict[str, object]]) -> list[WellLogPoint]:
    points: list[WellLogPoint] = []
    for row in rows:
        values: dict[str, float] = {}
        for key, value in row.items():
            try:
                values[key] = float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError) as error:
                raise ValueError(f"Well-log file contains a non-numeric {key} value") from error
        try:
            points.append(WellLogPoint(**values))
        except ValidationError as error:
            raise ValueError(
                f"Well-log file contains values outside teaching ranges ({TEACHING_RANGES})"
            ) from error
    return points


def parse_well_log_file(filename: str, content: bytes) -> list[WellLogPoint]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        reader = csv.DictReader(StringIO(content.decode("utf-8-sig")))
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row")
        headers = {header: _canonical_curve_name(header) for header in reader.fieldnames}
        _enforce_required_curves(headers, "CSV")
        rows = [{canonical: row[header] for header, canonical in headers.items() if canonical} for row in reader]
        return _points_from_rows(rows)
    if suffix == ".las":
        import lasio

        las = lasio.read(StringIO(content.decode("utf-8-sig")))
        headers = {curve.mnemonic: _canonical_curve_name(curve.mnemonic) for curve in las.curves}
        _enforce_required_curves(headers, "LAS")
        # Do not assume the first curve is the depth track; resolve it from the matched alias.
        depth_mnemonic = next((mnemonic for mnemonic, canonical in headers.items() if canonical == "depth"), None)
        row_count = len(las[depth_mnemonic]) if depth_mnemonic else len(las.index)
        rows = []
        for index in range(row_count):
            rows.append({canonical: las[header][index] for header, canonical in headers.items() if canonical})
        return _points_from_rows(rows)
    raise ValueError("Only LAS and CSV teaching files are supported")
