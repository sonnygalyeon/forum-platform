#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.error
import urllib.request


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
        "latency_ms": (time.perf_counter() - started) * 1000,
        "status": status,
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description="Small dependency-free Night Iris HTTP load smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--bearer-token", default="")
    args = parser.parse_args()

    paths = args.path or ["/live/", "/publications/", "/search/?q=django"]
    urls = [args.base_url.rstrip("/") + "/" + path.lstrip("/") for path in paths]
    headers = {"User-Agent": "Night-Iris-Load-Smoke/0.8.11"}
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"

    jobs = [urls[i % len(urls)] for i in range(args.requests)]
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda url: hit(url, args.timeout, headers), jobs))
    elapsed = time.perf_counter() - started

    latencies = [item["latency_ms"] for item in results]
    failures = [item for item in results if item["error"] or not item["status"] or item["status"] >= 500]
    status_counts = {}
    for item in results:
        key = str(item["status"] or "network_error")
        status_counts[key] = status_counts.get(key, 0) + 1

    report = {
        "requests": len(results),
        "concurrency": args.concurrency,
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / elapsed, 2) if elapsed else 0,
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "max": round(max(latencies), 2) if latencies else 0,
        },
        "status_counts": status_counts,
        "failures": len(failures),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
