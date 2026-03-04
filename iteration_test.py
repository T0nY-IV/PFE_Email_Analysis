import time
import statistics
import sys
from pathlib import Path

import model_test
import json

# Optional system monitoring libraries. psutil is used for CPU/memory.
# GPUtil or nvidia-smi is used for GPU stats when available.
try:
	import psutil
except Exception:
	psutil = None

try:
	import GPUtil
	_HAS_GPUTIL = True
except Exception:
	GPUtil = None
	_HAS_GPUTIL = False


def _get_gpu_status():
	"""Return GPU stats dict or None.

	Returned dict keys: 'util' (percent), 'mem_used' (MB), 'mem_total' (MB).
	"""
	# Try GPUtil first if installed
	gpus = None
	if _HAS_GPUTIL:
		gpus = GPUtil.getGPUs()
		if not gpus:
			return None
		g = gpus[0]
		return {"util": float(g.load * 100), "mem_used": float(g.memoryUsed), "mem_total": float(g.memoryTotal)}

	# Fallback: try nvidia-smi command-line (NVIDIA only)
	try:
		import subprocess
		cmd = 'nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits'
		out = subprocess.check_output(cmd, shell=True, universal_newlines=True)
		line = out.splitlines()[0].strip()
		util_str, mem_used_str, mem_total_str = [x.strip() for x in line.split(',')]
		return {"util": float(util_str), "mem_used": float(mem_used_str), "mem_total": float(mem_total_str)}
	except Exception:
		return None


def run_iterations(n, email_path, model):
	p = Path(email_path)
	if not p.exists():
		print(f"Email file not found: {email_path}")
		return 2

	email = p.read_text(encoding="utf-8")
	timings = []
	cpu_samples = []
	mem_samples = []
	gpu_utils = []
	gpu_mem_used = []
	gpu_mem_total = []
	conf_scores = []
	# Lists and counters for computed confidence based on domain/intent match
	computed_conf_scores = []
	both_match_count = 0
	domain_only_count = 0
	intent_only_count = 0
	none_match_count = 0

	print(f"Running {n} iterations...\n")

	# Track best responses: prefer those where both domain and intent match,
	# otherwise fall back to the best computed confidence overall.
	best_both = None
	best_overall = None
	for i in range(n):
		print(f"Iteration {i+1}/{n}: ", end="", flush=True)
		try:
			# Suppress printing of the model response during iterations
			# pass the desired model explicitly
			resp_content, elapsed = model_test.ll(email, test_model=model, print_response=False)
			# Attempt to parse JSON response and extract confidence, domain, intent
			conf_val = None
			parsed = None
			try:
				parsed = json.loads(resp_content)
				if isinstance(parsed, dict):
					# raw model-reported confidence (may be missing or non-numeric)
					conf_val = parsed.get("confidence_score")
					if conf_val is not None and not isinstance(conf_val, (int, float)):
						try:
							conf_val = float(conf_val)
						except Exception:
							conf_val = None
			except Exception:
				# parsing failed; leave parsed and conf_val as None
				parsed = None
		except Exception as e:
			print(f"failed: {e}")
			return 3
		timings.append(elapsed)
		print(f"{elapsed:.3f}s")

		# Sample system metrics immediately after the call to capture
		# the system load around each iteration.
		if psutil:
			try:
				# Short, non-blocking snapshot of CPU percent (system-wide)
				cpu = psutil.cpu_percent(interval=0.1)
				mem = psutil.virtual_memory().percent
			except Exception:
				cpu = None
				mem = None
		else:
			cpu = None
			mem = None

		gpu = _get_gpu_status()
		if gpu:
			gpu_utils.append(gpu.get("util"))
			gpu_mem_used.append(gpu.get("mem_used"))
			gpu_mem_total.append(gpu.get("mem_total"))
		else:
			# keep lists aligned; append None for missing values
			gpu_utils.append(None)
			gpu_mem_used.append(None)
			gpu_mem_total.append(None)

		cpu_samples.append(cpu)
		mem_samples.append(mem)
		conf_scores.append(conf_val)

		## Compare parsed domain/intent to expected values and compute a derived confidence
		expected_domain = "commercial"
		expected_intent = "request"
		# Compare parsed domain/intent to expected values (allow multiple) and compute a derived confidence
		#expected_domains = ["maintenance", "it"]
		#expected_intents = ["request", "quotation", "information"]
		# default base confidence if model didn't provide one
		base_conf = float(conf_val) if (conf_val is not None) else 0.5
		# Extract domain/intent from parsed JSON when available
		parsed_domain = None
		parsed_intent = None
		if isinstance(parsed, dict):
			parsed_domain = parsed.get("domain")
			parsed_intent = parsed.get("intent")
			if isinstance(parsed_domain, str):
				parsed_domain = parsed_domain.strip().lower()
			if isinstance(parsed_intent, str):
				parsed_intent = parsed_intent.strip().lower()

		## Determine match type
		domain_match = parsed_domain == expected_domain
		intent_match = parsed_intent == expected_intent
		# Determine match type (use membership checks against allowed lists)
		#domain_match = parsed_domain in expected_domains if parsed_domain else False
		#intent_match = parsed_intent in expected_intents if parsed_intent else False
		if domain_match and intent_match:
			both_match_count += 1
			# boost confidence slightly when both domain & intent match
			computed = min(1.0, base_conf + 0.2)
		elif domain_match and not intent_match:
			domain_only_count += 1
			# keep base confidence
			computed = base_conf
		elif intent_match and not domain_match:
			intent_only_count += 1
			computed = base_conf
		else:
			none_match_count += 1
			# penalize when neither matches
			computed = max(0.0, base_conf - 0.2)

		computed_conf_scores.append(computed)

		# Update best-overall (by computed confidence)
		candidate = {"computed": computed, "resp": resp_content, "parsed": parsed, "iter": i + 1, "elapsed": elapsed, "conf_val": conf_val}
		if best_overall is None or computed > best_overall["computed"]:
			best_overall = candidate

		# Update best among those with both domain and intent match
		if domain_match and intent_match:
			if best_both is None or computed > best_both["computed"]:
				best_both = candidate

	# Compute statistics
	total = sum(timings)
	minimum = min(timings)
	maximum = max(timings)
	mean = statistics.mean(timings)
	median = statistics.median(timings)
	stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
	p90 = sorted(timings)[int(len(timings) * 0.9) - 1]

	# Print a compact summary for quick analysis, with short explanations
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

	# Report CPU/memory statistics if samples were collected
	if any(x is not None for x in cpu_samples):
		cpu_vals = [x for x in cpu_samples if x is not None]
		print("\nCPU (system-wide):")
		print(f"  Avg: {statistics.mean(cpu_vals):.2f}%  Min: {min(cpu_vals):.2f}%  Max: {max(cpu_vals):.2f}%  Median: {statistics.median(cpu_vals):.2f}%")
	else:
		print("\nCPU: psutil not available; skipping CPU stats.")

	if any(x is not None for x in mem_samples):
		mem_vals = [x for x in mem_samples if x is not None]
		print("\nMemory (system-wide):")
		print(f"  Avg: {statistics.mean(mem_vals):.2f}%  Min: {min(mem_vals):.2f}%  Max: {max(mem_vals):.2f}%  Median: {statistics.median(mem_vals):.2f}%")
	else:
		print("\nMemory: psutil not available; skipping memory stats.")

	# GPU stats: only report if at least one sample had values
	if any(x is not None for x in gpu_utils):
		gpu_vals = [x for x in gpu_utils if x is not None]
		print("\nGPU utilization (%):")
		print(f"  Avg: {statistics.mean(gpu_vals):.2f}%  Min: {min(gpu_vals):.2f}%  Max: {max(gpu_vals):.2f}%  Median: {statistics.median(gpu_vals):.2f}%")
		# GPU memory used (MB) if available
		if any(x is not None for x in gpu_mem_used):
			mem_used_vals = [x for x in gpu_mem_used if x is not None]
			print("\nGPU memory used (MB):")
			print(f"  Avg: {statistics.mean(mem_used_vals):.1f}MB  Min: {min(mem_used_vals):.1f}MB  Max: {max(mem_used_vals):.1f}MB  Median: {statistics.median(mem_used_vals):.1f}MB")
	else:
		print("\nGPU: no GPU stats available (GPUtil/nvidia-smi not found or no GPU present).")

	# Confidence score statistics: compute only for parsed numeric scores
	if any(x is not None for x in conf_scores):
		conf_vals = [float(x) for x in conf_scores if x is not None]
		print("\nConfidence score (model-reported):")
		print(f"  Samples parsed: {len(conf_vals)} / {n}")
		print(f"  Avg: {statistics.mean(conf_vals):.3f}  Min: {min(conf_vals):.3f}  Max: {max(conf_vals):.3f}  Median: {statistics.median(conf_vals):.3f}  Stddev: {statistics.stdev(conf_vals) if len(conf_vals)>1 else 0.0:.3f}")
	else:
		print("\nConfidence score: no numeric confidence_score values parsed from responses.")

	# Computed confidence statistics based on domain/intent matching
	if computed_conf_scores:
		print("\nComputed confidence (adjusted by domain/intent match):")
		print(f"  Samples: {len(computed_conf_scores)} / {n}")
		print(f"  Avg: {statistics.mean(computed_conf_scores):.3f}  Min: {min(computed_conf_scores):.3f}  Max: {max(computed_conf_scores):.3f}  Median: {statistics.median(computed_conf_scores):.3f}  Stddev: {statistics.stdev(computed_conf_scores) if len(computed_conf_scores)>1 else 0.0:.3f}")
		print(f"  Matches: both={both_match_count}, domain_only={domain_only_count}, intent_only={intent_only_count}, none={none_match_count}")
	else:
		print("\nComputed confidence: no data collected.")

	# Choose best result to display: prefer both-match, else best overall
	chosen = best_both if best_both is not None else best_overall
	if chosen is not None:
		if best_both is not None:
			print("\nBest result (both domain and intent match):")
		else:
			print("\nBest overall result (no both-match found):")
		# Pretty-print parsed JSON if available, else raw response
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
	# Optional args: number_of_iterations email_path
	argv = sys.argv[1:]
	n = 50
	path = "emails_output/email_9589.txt"
	if len(argv) >= 1:
		try:
			n = int(argv[0])
		except Exception:
			pass
	if len(argv) >= 2:
		path = argv[1]

	sys.exit(run_iterations(n, path))
