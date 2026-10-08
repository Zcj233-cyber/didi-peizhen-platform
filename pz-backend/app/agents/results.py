"""Validate model output before it becomes input to another planning stage."""
import json


def parse_result(text, *, string_fields=(), list_fields=(), required_text=()):
    if not isinstance(text, str) or "{" not in text:
        raise ValueError("missing JSON result")
    data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if not isinstance(data, dict):
        raise ValueError("result must be an object")
    for name in string_fields:
        if not isinstance(data.get(name, ""), str):
            raise ValueError("invalid text field")
    for name in list_fields:
        if not isinstance(data.get(name, []), list):
            raise ValueError("invalid list field")
    for name in required_text:
        if not isinstance(data.get(name), str) or not data[name].strip():
            raise ValueError("missing required text")
    return data
