from ollama import chat
import time
from prompt import prompt_1, prompt_2, murged_prompt, prompt_orange



def ll(message, test_model="qwen2.5:3b", print_response: bool = True):
    # Refine the prompt with clearer instructions and examples
    
    prompt = prompt_orange #choode a prompt to test: prompt_1, prompt_2, murged_prompt, prompt_orange


    start_perf = time.perf_counter()
    response = chat(
        model=test_model,
        messages=[
            {'role': 'user', 'content': f"{prompt}\n\nEmail: {message}"}
        ]
    )
    end_perf = time.perf_counter()
    elapsed = end_perf - start_perf
    if print_response:
        print(response.message.content)
        print(f"Elapsed time: {elapsed:.3f} seconds")

    # Return the response content and elapsed seconds for programmatic use
    return response.message.content, elapsed


if __name__ == "__main__":
    try:
        with open("emails_output/email_9590.txt", "r", encoding="utf-8") as f: #normal email: 9589, complex email: 9590
            email_content = f.read()
    except FileNotFoundError:
        print("emails_output/email_9590.txt not found - please provide an email file.")
        raise

    ll(email_content)