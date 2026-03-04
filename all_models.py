from iteration_test import run_iterations
import sys

models = [
	#"qwen2.5:1.5b",
	"qwen2.5:3b",
	"gemma:2b",
	#"gemma:latest",#7b
	#"phi3:mini",
	#"llama3:8b",
	"qwen3:1.7b",
	"llama3.1:latest",
	#"qwen3:4b",
	#"qwen3:8b",
]


def main():
	# Optional args: number_of_iterations email_path
	argv = sys.argv[1:]
	n = 50
	path = "emails_output/email_9590.txt"
	if len(argv) >= 1:
		try:
			n = int(argv[0])
		except Exception:
			pass
	if len(argv) >= 2:
		path = argv[1]

	# Run iterations for each model sequentially
	for model in models:
		print("Testing model:", model)
		rc = run_iterations(n=n, email_path=path, model=model)
		if rc != 0:
			print(f"Model {model} returned non-zero exit code: {rc}")


if __name__ == "__main__":
	sys.exit(main())
	