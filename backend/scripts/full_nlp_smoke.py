"""Real HTTP upload + demo workflows. No fixture model injection or synthetic API responses.

Run against an isolated, migrated database: python scripts/full_nlp_smoke.py
Weights must be available locally or downloadable from Hugging Face on first use.
"""

import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ingestion.sample_generator import generate_sample_dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--output", default="../.verification/full-nlp-smoke.json")
    args = parser.parse_args()
    client = httpx.Client(base_url=args.base_url, timeout=120)

    def call(method, path, **kwargs):
        response = client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None

    rows = list(csv.DictReader(io.StringIO(generate_sample_dataset())))
    # 90 real synthetic texts (explicitly demo data), distributed across themes/dates.
    rows = sorted(rows, key=lambda row: row["created_at"])[::10]
    content = io.StringIO()
    writer = csv.DictWriter(content, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    upload = call(
        "POST", "/datasets/upload", files={"file": ("smoke-custom.csv", content.getvalue())}
    )
    dataset_id = upload["id"]
    preview = call("GET", f"/datasets/{dataset_id}/preview")
    assert preview["kind"] == "raw" and preview["shown_rows"] > 0
    call("POST", f"/datasets/{dataset_id}/map-columns", json=upload["column_mapping"])
    validation = call("POST", f"/datasets/{dataset_id}/validate")
    assert validation["valid_rows"] == 90
    imported = call("POST", f"/datasets/{dataset_id}/import")
    assert imported["status"] == "imported"
    report = {"upload_validation": validation, "workflows": []}

    for label, target in (("uploaded_csv", dataset_id), ("bundled_demo", None)):
        if target is None:
            demo = call("POST", "/datasets/sample")
            target = demo["dataset_id"]
            assert demo["row_count"] == 900
        run = call("POST", "/analysis/run", json={"dataset_id": target})
        print(f"{label}: enqueued {run['id']}", flush=True)
        started = time.monotonic()
        previous = None
        while time.monotonic() - started < 1200:
            run = call("GET", f"/analysis/{run['id']}/status")
            if run["current_step"] != previous:
                print(f"{label}: {run['current_step']} ({run['progress_pct']}%)", flush=True)
                previous = run["current_step"]
            if run["status"] == "failed":
                raise RuntimeError(run["error_message"])
            if run["status"] == "completed":
                break
            time.sleep(1)
        assert run["status"] == "completed", "Timed out waiting for inference"
        query = {"dataset_id": target, "analysis_run_id": run["id"]}
        summary = call("GET", "/dashboard/summary", params=query)
        timeline = call("GET", "/dashboard/timeline", params=query)
        topics = call("GET", "/topics", params={"analysis_run_id": run["id"]})
        assert summary["dataset_id"] == target and summary["analysis_run_id"] == run["id"]
        assert timeline["total_points"] > 0 and topics["total_topics"] > 0
        topic = next(item for item in topics["topics"] if not item["is_outlier"])
        detail = call("GET", f"/topics/{topic['id']}", params={"analysis_run_id": run["id"]})
        assert detail["sample_posts"] and detail["trend_history"]
        search = call("GET", "/posts/search", params={**query, "q": "AI", "limit": 5})
        metadata = call("GET", "/pipeline/metadata", params={"analysis_run_id": run["id"]})
        report["workflows"].append(
            {
                "workflow": label,
                "run": run,
                "summary": summary,
                "topics": topics,
                "timeline": timeline,
                "topic_detail": detail,
                "explorer": search,
                "metadata": metadata,
                "seconds": round(time.monotonic() - started, 2),
            }
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"{label}: verified complete, {topics['total_topics']} topics", flush=True)


if __name__ == "__main__":
    main()
