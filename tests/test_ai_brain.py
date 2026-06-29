import json
import pytest

from agents.ai_brain import AIBrain


def test_parse_json_pure_json():
    brain = AIBrain()
    text = '{"action": "search", "query": "python tutorials", "success": true}'
    parsed = brain._parse_json_action(text)
    assert isinstance(parsed, dict)
    assert parsed.get('action') == 'search'
    assert parsed.get('query') == 'python tutorials'


def test_parse_json_with_code_fence():
    brain = AIBrain()
    text = """
Here is the action:
```
{
  "action": "app_open",
  "app": "com.android.chrome"
}
```
"""
    parsed = brain._parse_json_action(text)
    assert isinstance(parsed, dict)
    assert parsed.get('action') == 'app_open'
    assert parsed.get('app') == 'com.android.chrome'


def test_parse_fallback_raw_response():
    brain = AIBrain()
    text = 'I would open Chrome and search for python tutorials.'
    parsed = brain._parse_json_action(text)
    assert isinstance(parsed, dict)
    assert '__raw_response__' in parsed
