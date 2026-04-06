from google import genai
import time
import statistics
import sys
import json
import os
from pathlib import Path



def call_genai(client, model: str, prompt: str):
    resp = client.models.generate_content(model=model, contents=prompt)
    # prefer .text when available
    text = None
    try:
        text = getattr(resp, "text")
    except Exception:
        pass
    if text is None:
        try:
            text = str(resp)
        except Exception:
            text = ""
    return text, resp


def run_iterations(n: int = 50, email_path: str = "emails_output/email_9589.txt", model: str = "gemini-2.5-flash", api_key: str | None = None):
    p = Path(email_path)
    if not p.exists():
        print(f"Email file not found: {email_path}")
        return 2

    prompt_template = (
        "You are an enterprise email analysis agent specialized in business email understanding. "
        "Analyze the provided email and return ONLY a valid JSON object that EXACTLY matches this schema:\n\n"
        "{\n"
        "  \"email_id\": \"string\",\n"
        "  \"domain\": \"rh|maintenance|commercial|support|finance|other\",\n"
        "  \"intent\": \"request|complaint|information|incident|follow_up|other\",\n"
        "  \"entities\": {},\n"
        "  \"confidence_score\": 0.0\n"
        "}\n\n"
        "Instructions:\n"
        "- Determine the business domain.\n"
        "- Identify the primary intent (main need).\n"
        "- Extract ALL relevant entities dynamically based on the email content.\n"
        "- Add entity names as keys inside the 'entities' object.\n"
        "- If no entities are found, return an empty object {}.\n"
        "- If unsure about domain or intent, use \"other\".\n"
        "- Return ONLY the JSON. No explanations, no extra text.\n\n"
        "Email:\n"
    )

    email = p.read_text(encoding="utf-8")

    api_key = "AIzaSyDFRfNEyZNC631IwzMVYao1f0igd33SbHw"

    client = genai.Client(api_key=api_key)

    timings = []
    conf_scores = []
    computed_conf_scores = []
    both_match_count = domain_only_count = intent_only_count = none_match_count = 0

    best_both = None
    best_overall = None

    print(f"Running {n} iterations against model {model}...\n")
    for i in range(n):
        print(f"Iteration {i+1}/{n}: ", end="", flush=True)
        all_prompt = f"{prompt_template}\n\nEmail: {email}"
        print(all_prompt)
        start = time.perf_counter()
        try:
            text, raw = call_genai(client, model, all_prompt)
        except Exception as e:
            print(f"failed: {e}")
            return 3
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        print(f"{elapsed:.3f}s")

        # system metrics sampling removed

        # Try parse generated text as JSON
        parsed = None
        conf_val = None
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                conf_val = parsed.get("confidence_score")
                if conf_val is not None and not isinstance(conf_val, (int, float)):
                    try:
                        conf_val = float(conf_val)
                    except Exception:
                        conf_val = None
        except Exception:
            parsed = None

        conf_scores.append(conf_val)

        expected_domain = "commercial"
        expected_intent = "request"
        base_conf = float(conf_val) if (conf_val is not None) else 0.5
        parsed_domain = parsed.get("domain") if isinstance(parsed, dict) else None
        parsed_intent = parsed.get("intent") if isinstance(parsed, dict) else None
        if isinstance(parsed_domain, str):
            parsed_domain = parsed_domain.strip().lower()
        if isinstance(parsed_intent, str):
            parsed_intent = parsed_intent.strip().lower()

        domain_match = parsed_domain == expected_domain
        intent_match = parsed_intent == expected_intent
        if domain_match and intent_match:
            both_match_count += 1
            computed = min(1.0, base_conf + 0.2)
        elif domain_match and not intent_match:
            domain_only_count += 1
            computed = base_conf
        elif intent_match and not domain_match:
            intent_only_count += 1
            computed = base_conf
        else:
            none_match_count += 1
            computed = max(0.0, base_conf - 0.2)

        computed_conf_scores.append(computed)

        candidate = {"computed": computed, "resp": text, "parsed": parsed, "iter": i + 1, "elapsed": elapsed, "conf_val": conf_val}
        if best_overall is None or computed > best_overall["computed"]:
            best_overall = candidate
        if domain_match and intent_match:
            if best_both is None or computed > best_both["computed"]:
                best_both = candidate

    # Statistics
    total = sum(timings)
    minimum = min(timings)
    maximum = max(timings)
    mean = statistics.mean(timings)
    median = statistics.median(timings)
    stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
    p90 = sorted(timings)[int(len(timings) * 0.9) - 1]

    print("\nSummary:")
    print(f"  Iterations: {n}  (number of calls made)")
    print(f"  Total time: {total:.3f}s  (sum of all iteration durations)")
    print(f"  Min: {minimum:.3f}s  (fastest single call)")
    print(f"  Max: {maximum:.3f}s  (slowest single call)")
    print(f"  Mean: {mean:.3f}s  (average call duration)")
    print(f"  Median: {median:.3f}s  (middle value; less affected by outliers)")
    print(f"  Stddev: {stdev:.3f}s  (spread of timings; lower = more consistent)")
    print(f"  90th perc: {p90:.3f}s  (90% of calls were this fast or faster)")
    print(f"  Calls/sec (avg): {n/total:.3f}  (average throughput)")

    # System metrics reporting removed

    if any(x is not None for x in conf_scores):
        conf_vals = [float(x) for x in conf_scores if x is not None]
        print("\nConfidence score (model-reported):")
        print(f"  Samples parsed: {len(conf_vals)} / {n}")
        print(f"  Avg: {statistics.mean(conf_vals):.3f}  Min: {min(conf_vals):.3f}  Max: {max(conf_vals):.3f}  Median: {statistics.median(conf_vals):.3f}  Stddev: {statistics.stdev(conf_vals) if len(conf_vals)>1 else 0.0:.3f}")
    else:
        print("\nConfidence score: no numeric confidence_score values parsed from responses.")

    if computed_conf_scores:
        print("\nComputed confidence (adjusted by domain/intent match):")
        print(f"  Samples: {len(computed_conf_scores)} / {n}")
        print(f"  Avg: {statistics.mean(computed_conf_scores):.3f}  Min: {min(computed_conf_scores):.3f}  Max: {max(computed_conf_scores):.3f}  Median: {statistics.median(computed_conf_scores):.3f}  Stddev: {statistics.stdev(computed_conf_scores) if len(computed_conf_scores)>1 else 0.0:.3f}")
        print(f"  Matches: both={both_match_count}, domain_only={domain_only_count}, intent_only={intent_only_count}, none={none_match_count}")
    else:
        print("\nComputed confidence: no data collected.")

    chosen = best_both if best_both is not None else best_overall
    if chosen is not None:
        if best_both is not None:
            print("\nBest result (both domain and intent match):")
        else:
            print("\nBest overall result (no both-match found):")
        try:
            if isinstance(chosen["parsed"], dict):
                pretty = json.dumps(chosen["parsed"], indent=2, ensure_ascii=False)
            else:
                pretty = str(chosen["parsed"])
        except Exception:
            pretty = str(chosen["resp"]) if chosen.get("resp") is not None else "(no response content)"

        print(f"  Iteration: {chosen['iter']}  Elapsed: {chosen['elapsed']:.3f}s  Computed confidence: {chosen['computed']:.3f}  Model confidence: {chosen.get('conf_val')}")
        print(pretty)

    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    n = 50
    path = "emails_output/email_9589.txt"
    api_key = None
    model = "gemini-3-flash-preview"
    if len(argv) >= 1:
        try:
            n = int(argv[0])
        except Exception:
            pass
    if len(argv) >= 2:
        path = argv[1]
    if len(argv) >= 3:
        api_key = argv[2]
    if len(argv) >= 4:
        model = argv[3]

    sys.exit(run_iterations(n, path, model=model, api_key=api_key))

