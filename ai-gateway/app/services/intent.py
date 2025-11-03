from typing import Dict

# Very naive placeholder classifier

def classify_intent(text: str) -> Dict[str, float]:
    text_l = (text or "").lower()
    intents = {
        "bug_diagnosis": 0.0,
        "how_to": 0.0,
        "incident": 0.0,
    }
    if any(k in text_l for k in ["error", "exception", "stack", "trace", "crash"]):
        intents["bug_diagnosis"] = 0.8
    if any(k in text_l for k in ["how", "configure", "setup", "steps"]):
        intents["how_to"] = 0.6
    if any(k in text_l for k in ["outage", "down", "sev", "incident"]):
        intents["incident"] = 0.7
    return intents
