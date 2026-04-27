import logging
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Anthropic Claude API를 호출하는 얇은 wrapper.

    모델별로 인스턴스를 따로 만들어 사용한다.
    예: sonnet_client = ClaudeClient(api_key, "claude-sonnet-4-5")
        haiku_client = ClaudeClient(api_key, "claude-haiku-4-5")
    """

    def __init__(self, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key, max_retries=3)
        self._model = model

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> dict:
        """prompt를 Claude에 보내고 응답을 dict로 반환한다.

        반환 dict 키:
            - text: 응답 텍스트
            - input_tokens: 입력 토큰 수
            - output_tokens: 출력 토큰 수
            - stop_reason: 응답 종료 사유
            - model: 응답한 모델명
            - id: Anthropic 응답 ID
        """
        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as e:
            logger.error(f"Claude API call failed: {type(e).__name__}: {e}")
            raise

        return {
            "text": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "stop_reason": response.stop_reason,
            "model": response.model,
            "id": response.id,
        }
