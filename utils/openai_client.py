"""
OpenAI Client wrapper with cost tracking
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import config
from tenacity import retry, stop_after_attempt, wait_exponential
import instructor


class OpenAIClient:
    """Wrapper for OpenAI API with cost tracking"""

    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.inst_client = instructor.from_openai(self.client)
        self.session_costs = []
        self.total_cost = 0.0

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=config.RETRY_DELAY, max=10),
    )
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = config.EXTRACTION_MODEL,
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get chat completion with automatic retries and cost tracking

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            response_format: Optional format specification (e.g., {"type": "json_object"})
            max_tokens: Maximum tokens to generate

        Returns:
            Response dict with content and cost info
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if response_format:
            kwargs["response_format"] = response_format

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**kwargs)

        # Track costs
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        model_costs = config.COSTS.get(model, config.COSTS[config.EXTRACTION_MODEL])
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        total_cost = input_cost + output_cost

        self.session_costs.append(
            {
                "operation": "chat_completion",
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost,
            }
        )
        self.total_cost += total_cost

        return {
            "content": response.choices[0].message.content,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost,
            "finish_reason": response.choices[0].finish_reason,
        }

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=config.RETRY_DELAY, max=10),
    )
    def chat_completion_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Any,
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> Any:
        """
        Chat completion with structured Pydantic output

        Args:
            messages: List of message dicts
            response_format: Pydantic BaseModel class for structured output
            model: Model to use (defaults to EXTRACTION_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed Pydantic object
        """
        if model is None:
            model = config.EXTRACTION_MODEL

        try:
            completion = self.inst_client.chat.completions.create(
                model=model,
                messages=messages,
                response_model=response_format,
                # temperature=temperature,
                # max_tokens=max_tokens,
            )

            # Track usage
            usage = 0  # completion.usage
            input_tokens = 0  # usage.prompt_tokens
            output_tokens = 0  # usage.completion_tokens

            model_costs = config.COSTS.get(model, config.COSTS[config.EXTRACTION_MODEL])
            input_cost = (input_tokens / 1000) * model_costs["input"]
            output_cost = (output_tokens / 1000) * model_costs["output"]
            total_cost = input_cost + output_cost

            self.session_costs.append(
                {
                    "operation": "structured_chat_completion",
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": total_cost,
                }
            )
            self.total_cost += total_cost

            # Return parsed Pydantic object
            return completion

        except Exception as e:
            print(f"Error in structured chat completion: {e}")
            raise

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=config.RETRY_DELAY, max=10),
    )
    def create_embeddings(
        self, texts: List[str], model: str = config.EMBEDDING_MODEL
    ) -> Dict[str, Any]:
        """
        Create embeddings with cost tracking

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            Dict with embeddings and cost info
        """
        response = self.client.embeddings.create(model=model, input=texts)

        # Track costs
        total_tokens = response.usage.total_tokens
        model_costs = config.COSTS.get(model, config.COSTS[config.EMBEDDING_MODEL])
        total_cost = (total_tokens / 1000) * model_costs["input"]

        self.session_costs.append(
            {
                "operation": "embeddings",
                "model": model,
                "input_tokens": total_tokens,
                "cost": total_cost,
            }
        )
        self.total_cost += total_cost

        embeddings = [item.embedding for item in response.data]

        return {
            "embeddings": embeddings,
            "model": model,
            "tokens": total_tokens,
            "cost": total_cost,
        }

    def get_session_cost(self) -> float:
        """Get total cost for current session"""
        return self.total_cost

    def get_cost_breakdown(self) -> List[Dict[str, Any]]:
        """Get detailed cost breakdown"""
        return self.session_costs

    def reset_session_costs(self):
        """Reset session cost tracking"""
        self.session_costs = []
        self.total_cost = 0.0
