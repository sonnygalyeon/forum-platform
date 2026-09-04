#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def percentile(values, q):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def hit(url, timeout, headers):
    started = time.perf_counter()
    status = None
    error = None
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            response.read(512)
    except urllib.error.HTTPError as exc:
        status = exc.code
        error = str(exc)
    except Exception as exc:
        error = str(exc)
    return {
        "url": url,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "status": status,
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description="Dependency-free Night Iris HTTP load gate")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--requests", type=int, default=300)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--bearer-token", default="")
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    parser.add_argument("--max-p99-ms", type=float, default=3000.0)
    parser.add_argument("--min-rps", type=float, default=10.0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must be positive")

    paths = args.path or ["/live/", "/publications/", "/search/?q=django&scope=publications"]
    urls = [args.base_url.rstrip("/") + "/" + path.lstrip("/") for path in paths]
    headers = {"User-Agent": "Night-Iris-Load-Gate/0.8.12"}
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"

    for index in range(args.warmup):
        hit(urls[index % len(urls)], args.timeout, headers)

    jobs = [urls[i % len(urls)] for i in range(args.requests)]
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda url: hit(url, args.timeout, headers), jobs))
    elapsed = time.perf_counter() - started

    latencies = [item["latency_ms"] for item in results]
    failures = [
        item
        for item in results
        if item["error"] or not item["status"] or item["status"] >= 500
    ]
    status_counts = {}
    endpoint_counts = {}
    for item in results:
        key = str(item["status"] or "network_error")
        status_counts[key] = status_counts.get(key, 0) + 1
        endpoint_counts[item["url"]] = endpoint_counts.get(item["url"], 0) + 1

    rps = len(results) / elapsed if elapsed else 0.0
    error_rate = len(failures) / len(results) if results else 1.0
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)

    violations = []
    if error_rate > args.max_error_rate:
        violations.append(
            f"error_rate {error_rate:.4f} exceeds {args.max_error_rate:.4f}"
        )
    if p95 > args.max_p95_ms:
        violations.append(f"p95 {p95:.2f}ms exceeds {args.max_p95_ms:.2f}ms")
    if p99 > args.max_p99_ms:
        violations.append(f"p99 {p99:.2f}ms exceeds {args.max_p99_ms:.2f}ms")
    if rps < args.min_rps:
        violations.append(f"rps {rps:.2f} below {args.min_rps:.2f}")

    report = {
        "gate": "pass" if not violations else "fail",
        "requests": len(results),
        "concurrency": args.concurrency,
        "warmup": args.warmup,
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(rps, 2),
        "error_rate": round(error_rate, 5),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "max": round(max(latencies), 2) if latencies else 0,
        },
        "thresholds": {
            "max_error_rate": args.max_error_rate,
            "max_p95_ms": args.max_p95_ms,
            "max_p99_ms": args.max_p99_ms,
            "min_rps": args.min_rps,
        },
        "status_counts": status_counts,
        "endpoint_counts": endpoint_counts,
        "failures": len(failures),
        "violations": violations,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(1 if violations else 0)


if __name__ == "__main__":
    main()
