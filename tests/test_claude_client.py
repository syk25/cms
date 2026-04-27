from app.config import settings
from app.llm.claude_client import ClaudeClient


def main():
    client = ClaudeClient(
        api_key=settings.anthropic_api_key,
        model="claude-sonnet-4-5",
    )

    result = client.complete(
        prompt="'hello world'를 한국어로 한 줄로 답해줘.",
        max_tokens=100,
    )

    print("=== 응답 결과 ===")
    print(f"text: {result['text']}")
    print(f"input_tokens: {result['input_tokens']}")
    print(f"output_tokens: {result['output_tokens']}")
    print(f"stop_reason: {result['stop_reason']}")
    print(f"model: {result['model']}")
    print(f"id: {result['id']}")


if __name__ == "__main__":
    main()
