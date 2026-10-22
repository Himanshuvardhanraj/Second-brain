import os
import time
import logging

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiQuotaError(Exception):
    """Raised when Gemini rejects a request because the project quota is exhausted."""


class GeminiLLM:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

    def generate_answer(self, question: str, context: str) -> str:
        prompt = self._prompt(question, context)
        last_error = None

        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=1800,
                        temperature=0.2,
                    )
                )

                return response.text or (
                    "I couldn't generate an answer from the retrieved context."
                )
            except Exception as e:
                error_text = str(e)
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    logger.warning("Gemini quota exhausted for model %s", self.model)
                    raise GeminiQuotaError from e
                last_error = e
                if attempt < 1:
                    time.sleep(2 ** attempt)

        if last_error:
            raise last_error
        raise RuntimeError("Gemini returned no answer")

    def stream_answer(self, question: str, context: str):
        prompt = self._prompt(question, context)
        try:
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1800,
                    temperature=0.2,
                ),
            )
            for chunk in response:
                text = getattr(chunk, "text", None)
                if text:
                    yield text
        except Exception as exc:
            error_text = str(exc)
            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                logger.warning("Gemini quota exhausted for model %s", self.model)
                raise GeminiQuotaError from exc
            raise

    @staticmethod
    def _prompt(question: str, context: str) -> str:
        return f"""
You are Second Brain, a personal knowledge assistant.

Answer the user's question using ONLY the information
contained in the provided context. Treat the context as the
authoritative source for this user's uploaded documents.

Rules:
- Do not invent information.
- Do not use outside knowledge.
- If the answer cannot be found in the context, say:
  "I couldn't find this information in your uploaded documents."
- Answer every part of the question. If the question asks for
  an explanation, cover the definition, key concepts, and
  important points present in the context instead of stopping
  after the first matching passage.
- Do not say that information is missing when it is present in
  another supplied source.
- Give a complete, concise but useful answer with headings and numbered
  points when that improves exam revision.
- Never stop in the middle of a sentence. Always finish the
  answer before returning it.
- Use Markdown when appropriate.

USER QUESTION:
{question}

RETRIEVED CONTEXT:
{context}

ANSWER:
"""