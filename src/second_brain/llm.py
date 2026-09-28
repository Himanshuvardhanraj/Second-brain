import os
import time

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


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

        prompt = f"""
You are Second Brain, a personal knowledge assistant.

Answer the user's question using ONLY the information
contained in the provided context.

Rules:
- Do not invent information.
- Do not use outside knowledge.
- If the answer cannot be found in the context, say:
  "I couldn't find this information in your uploaded documents."
- Give a concise but useful answer.
- Use Markdown when appropriate.

USER QUESTION:
{question}

RETRIEVED CONTEXT:
{context}

ANSWER:
"""

        last_error = None

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=1000,
                    )
                )

                return response.text or (
                    "I couldn't generate an answer from the retrieved context."
                )

            except Exception as e:
                last_error = e

                if attempt < 2:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

        raise last_error