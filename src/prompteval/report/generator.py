"""HTML report generator."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from prompteval.config import Config
from prompteval.evaluator import EvalResult
from prompteval.security.pii import SecurityFinding


def _build_summary(results: list[EvalResult], security_findings: list[SecurityFinding]) -> dict:
    total = len(results)
    successful = [r for r in results if r.response and not r.error]
    errors = total - len(successful)
    total_cost = sum(r.estimated_cost for r in results)
    scored = [r for r in successful if r.quality_score is not None]
    avg_score = sum(r.quality_score for r in scored) / len(scored) if scored else 0
    avg_latency = sum(r.response.latency_ms for r in successful) / len(successful) if successful else 0

    return {
        "total_runs": total,
        "successful": len(successful),
        "errors": errors,
        "total_cost": round(total_cost, 6),
        "avg_quality_score": round(avg_score, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "security_issues": len(security_findings),
    }


def _build_token_chart_data(results: list[EvalResult]) -> dict:
    """Build Chart.js data for token usage by provider/model."""
    grouped = defaultdict(lambda: {"input": 0, "output": 0})
    for r in results:
        if r.response:
            key = f"{r.provider}/{r.model}"
            grouped[key]["input"] += r.response.input_tokens
            grouped[key]["output"] += r.response.output_tokens

    labels = list(grouped.keys())
    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Input Tokens",
                "data": [grouped[l]["input"] for l in labels],
                "backgroundColor": "rgba(54, 162, 235, 0.7)",
            },
            {
                "label": "Output Tokens",
                "data": [grouped[l]["output"] for l in labels],
                "backgroundColor": "rgba(255, 99, 132, 0.7)",
            },
        ],
    }


def _build_cost_chart_data(results: list[EvalResult]) -> dict:
    """Build Chart.js data for cost by provider/model."""
    grouped = defaultdict(float)
    for r in results:
        grouped[f"{r.provider}/{r.model}"] += r.estimated_cost

    labels = list(grouped.keys())
    return {
        "labels": labels,
        "datasets": [{
            "label": "Estimated Cost ($)",
            "data": [round(grouped[l], 6) for l in labels],
            "backgroundColor": [
                "rgba(75, 192, 192, 0.7)",
                "rgba(255, 159, 64, 0.7)",
                "rgba(153, 102, 255, 0.7)",
                "rgba(255, 205, 86, 0.7)",
                "rgba(201, 203, 207, 0.7)",
            ],
        }],
    }


def _build_latency_chart_data(results: list[EvalResult]) -> dict:
    """Build Chart.js data for latency by provider/model."""
    grouped = defaultdict(list)
    for r in results:
        if r.response:
            grouped[f"{r.provider}/{r.model}"].append(r.response.latency_ms)

    labels = list(grouped.keys())
    avgs = [round(sum(v) / len(v), 1) if v else 0 for v in [grouped[l] for l in labels]]
    return {
        "labels": labels,
        "datasets": [{
            "label": "Avg Latency (ms)",
            "data": avgs,
            "backgroundColor": "rgba(153, 102, 255, 0.7)",
        }],
    }


def _build_quality_table(results: list[EvalResult]) -> list[dict]:
    """Build quality comparison table rows."""
    grouped = defaultdict(list)
    for r in results:
        if r.response and not r.error:
            key = (r.prompt_name, r.provider, r.model)
            grouped[key].append(r)

    rows = []
    for (prompt, provider, model), group in sorted(grouped.items()):
        scores = [r.quality_score for r in group if r.quality_score is not None]
        latencies = [r.response.latency_ms for r in group if r.response]
        costs = [r.estimated_cost for r in group]

        rows.append({
            "prompt": prompt,
            "provider": provider,
            "model": model,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else "N/A",
            "avg_latency": round(sum(latencies) / len(latencies), 1) if latencies else "N/A",
            "total_cost": round(sum(costs), 6),
            "runs": len(group),
        })

    return rows


def _build_detail_rows(results: list[EvalResult]) -> list[dict]:
    """Build detailed result rows for the full results table."""
    rows = []
    for r in results:
        rows.append({
            "prompt_name": r.prompt_name,
            "dataset": r.dataset_name,
            "row_index": r.row_index,
            "provider": r.provider,
            "model": r.model,
            "rendered_prompt": r.rendered_prompt[:200],
            "response": r.response.text[:300] if r.response else "",
            "input_tokens": r.response.input_tokens if r.response else 0,
            "output_tokens": r.response.output_tokens if r.response else 0,
            "latency_ms": r.response.latency_ms if r.response else 0,
            "cost": round(r.estimated_cost, 6),
            "quality_score": r.quality_score,
            "quality_reasoning": r.quality_reasoning or "",
            "error": r.error or "",
        })
    return rows


def generate_report(
    results: list[EvalResult],
    security_findings: list[SecurityFinding],
    config: Config,
    output_path: str,
):
    """Generate self-contained HTML report."""
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("template.html")

    context = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": _build_summary(results, security_findings),
        "token_chart_data": _build_token_chart_data(results),
        "cost_chart_data": _build_cost_chart_data(results),
        "latency_chart_data": _build_latency_chart_data(results),
        "quality_rows": _build_quality_table(results),
        "detail_rows": _build_detail_rows(results),
        "security_findings": [
            {
                "check_type": f.check_type,
                "severity": f.severity,
                "description": f.description,
                "evidence": f.evidence,
                "provider": f.provider,
                "model": f.model,
            }
            for f in security_findings
        ],
    }

    html = template.render(**context)
    Path(output_path).write_text(html)
