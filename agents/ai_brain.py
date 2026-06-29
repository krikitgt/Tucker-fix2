"""AI Brain - The AI that makes decisions.

This is the core AI that understands commands and plans actions.
You can swap different AI backends here (OpenAI, Claude, local models, etc.)
"""

import json
import re
from typing import Dict
from loguru import logger
from config import Config


class AIBrain:
    """The AI brain that processes commands and makes decisions."""

    def __init__(self, model: str = None):
        self.model = model or Config.AI_MODEL
        self.temperature = Config.AI_TEMPERATURE
        self.max_tokens = Config.AI_MAX_TOKENS
        self.api_backend = None
        self.client = None

        self._initialize_backend()
        logger.info(f"AIBrain initialized with model: {self.model}")

    def _initialize_backend(self):
        """Initialize the appropriate AI backend."""
        if "gpt" in self.model.lower():
            if not Config.OPENAI_API_KEY:
                logger.warning("OpenAI API key not found")
                return
            try:
                import openai  # type: ignore
                openai.api_key = Config.OPENAI_API_KEY
                self.api_backend = "openai"
                self.client = openai
                logger.info("✓ OpenAI backend ready")
            except ImportError:
                logger.error("OpenAI library not installed: pip install openai")

        elif "claude" in self.model.lower():
            if not Config.ANTHROPIC_API_KEY:
                logger.warning("Anthropic API key not found")
                return
            try:
                import anthropic  # type: ignore
                self.client = anthropic
                self.api_backend = "anthropic"
                logger.info("✓ Anthropic backend ready")
            except ImportError:
                logger.error("Anthropic library not installed: pip install anthropic")

        else:
            try:
                from transformers import pipeline  # type: ignore
                self.api_backend = "local"
                self.client = pipeline
                logger.info("✓ Local model backend ready")
            except ImportError:
                logger.error("Transformers not installed: pip install transformers torch")

    def process_command(self, user_input: str, context: str = "") -> Dict:
        """Process a user command and return action plan."""
        logger.info(f"Processing command: {user_input}")

        if not self.api_backend:
            return self._simple_response(user_input)

        if self.api_backend == "openai":
            return self._process_openai(user_input, context)
        elif self.api_backend == "anthropic":
            # Fallback to simple response for now; implement Anthropic parsing when tested
            return self._simple_response(user_input)
        else:
            return self._simple_response(user_input)

    def _parse_json_action(self, text: str) -> Dict:
        """Try to extract and parse a JSON object from model output."""
        # Try to find a JSON object/block in the response
        try:
            # First attempt: direct json.loads if the text is pure JSON
            return json.loads(text)
        except Exception:
            pass

        # Try to extract the first {...} block
        m = re.search(r"(\{(?:.|\n)*\})", text)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        # No JSON found
        return {"__raw_response__": text}

    def _process_openai(self, user_input: str, context: str) -> Dict:
        """Process command using OpenAI API and return structured action dict."""
        try:
            openai = self.client
            system_prompt = """You are Tucker AI, an intelligent agent that controls an Android tablet. 
You can:
- Open apps (provide package name)
- Take screenshots
- Tap on screen coordinates
- Type text
- Search the web
- Navigate apps

Respond with a JSON action plan ONLY. Example:
{
    "action": "app_open" | "tap" | "type" | "swipe" | "search" | "navigate" | "screenshot",
    "app": "package name",
    "activity": "activity name",
    "x": 100, "y": 200,
    "text": "some text",
    "query": "search term",
    "reason": "why"
}"""

            response = openai.ChatCompletion.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nCommand: {user_input}"},
                ],
            )

            raw_text = ""
            try:
                raw_text = response.choices[0].message.content
            except Exception:
                # fallback for different client versions
                raw_text = getattr(response.choices[0], "text", "")

            parsed = self._parse_json_action(raw_text)

            # If parsed contains the special key, parsing failed
            if "__raw_response__" in parsed:
                logger.warning("Failed to parse JSON from model response. Returning raw response.")
                return {"success": False, "reason": "Could not parse model response", "raw": raw_text}

            # Merge into standard return shape
            result = {"success": True, "backend": "openai", "response": raw_text}
            result.update(parsed)
            return result
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._simple_response(user_input)

    def _simple_response(self, user_input: str) -> Dict:
        """Fallback: Simple command parsing without AI."""
        logger.info("Using simple response (no AI backend)")

        text = user_input.lower()

        if "open" in text:
            if "chrome" in text or "browser" in text:
                return {
                    "success": True,
                    "action": "app_open",
                    "app": "com.android.chrome",
                    "activity": "com.google.android.apps.chrome.Main",
                    "reason": "User asked to open Chrome",
                }
            elif "youtube" in text:
                return {
                    "success": True,
                    "action": "app_open",
                    "app": "com.google.android.youtube",
                    "reason": "User asked to open YouTube",
                }

        elif "search" in text:
            query = text.replace("search", "").replace("for", "").strip()
            return {
                "success": True,
                "action": "search",
                "query": query,
                "reason": f"User asked to search for: {query}",
            }

        elif "screenshot" in text or "capture" in text:
            return {"success": True, "action": "screenshot", "reason": "User asked for screenshot"}

        return {
            "success": False,
            "reason": "Could not understand command",
            "suggestion": "Try: 'Open Chrome', 'Search for..', 'Take screenshot'",
        }


if __name__ == "__main__":
    brain = AIBrain()
    result = brain.process_command("Open Chrome")
    print(result)
