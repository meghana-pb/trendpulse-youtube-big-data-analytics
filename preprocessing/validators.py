"""
TrendPulse - Data Validators and Quality Checker
"""
import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger("trendpulse.validators")


class DataQualityReport:
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []
        self.total_records = 0
        self.failed_records = 0

    def add_check(self, name: str, passed: int, failed: int, details: str = ""):
        self.checks.append({
            "check": name, "passed": passed, "failed": failed,
            "pass_rate": round(passed / max(passed + failed, 1) * 100, 2),
            "details": details})

    @property
    def quality_score(self) -> float:
        if not self.checks:
            return 100.0
        return round(sum(c["pass_rate"] for c in self.checks) / len(self.checks), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {"quality_score": self.quality_score, "total_records": self.total_records,
                "failed_records": self.failed_records, "checks": self.checks}

    def __str__(self):
        lines = [f"Data Quality Score: {self.quality_score}%"]
        for c in self.checks:
            st = "PASS" if c["pass_rate"] >= 95 else ("WARN" if c["pass_rate"] >= 80 else "FAIL")
            lines.append(f"  [{st}] {c['check']}: {c['pass_rate']}% ({c['details']})")
        return "\n".join(lines)


def validate_dataframe(df: pd.DataFrame) -> DataQualityReport:
    report = DataQualityReport()
    report.total_records = n = len(df)
    if "video_id" in df.columns:
        missing = df["video_id"].isna().sum() + (df["video_id"].astype(str).str.strip() == "").sum()
        report.add_check("video_id_present", n - missing, missing, f"{missing} missing")
    if "video_id" in df.columns:
        dupes = df["video_id"].duplicated().sum()
        report.add_check("no_duplicate_ids", n - dupes, dupes, f"{dupes} duplicates")
    if "views" in df.columns:
        neg = (df["views"] < 0).sum()
        report.add_check("non_negative_views", n - neg, neg)
    if "likes" in df.columns:
        neg = (df["likes"] < 0).sum()
        report.add_check("non_negative_likes", n - neg, neg)
    if "category_id" in df.columns:
        inv = (df["category_id"] == 0).sum()
        report.add_check("valid_category_id", n - inv, inv, f"{inv} uncategorized")
    if "publish_time" in df.columns:
        null_ts = df["publish_time"].isna().sum()
        null_ts += (df["publish_time"].astype(str).str.lower() == "nat").sum()
        report.add_check("valid_publish_time", n - null_ts, null_ts)
    if "engagement_rate" in df.columns:
        inv = ((df["engagement_rate"] < 0) | (df["engagement_rate"] > 10)).sum()
        report.add_check("valid_engagement_rate", n - inv, inv)
    if "trending_duration_days" in df.columns:
        inv = (df["trending_duration_days"] < 1).sum()
        report.add_check("positive_trending_duration", n - inv, inv)
    report.failed_records = sum(c["failed"] for c in report.checks)
    logger.info(f"Data quality check complete.\n{report}")
    return report


def validate_event(event: Dict[str, Any]) -> tuple:
    errors = []
    for field in ["video_id", "title", "views"]:
        if field not in event or event[field] is None:
            errors.append(f"Missing required field: {field}")
    if "views" in event:
        try:
            if float(event["views"]) < 0:
                errors.append("Negative views value")
        except (ValueError, TypeError):
            errors.append("Non-numeric views value")
    return len(errors) == 0, errors
