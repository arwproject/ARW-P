from time import sleep
from typing import Any, Dict


def echo(message: str, context: Dict) -> Dict[str, Any]:
    return {"message": message, "context": context}


def add(a: int, b: int, context: Dict) -> Dict[str, Any]:
    return {"sum": a + b}


def slow_task(duration: int = 1, context: Dict = None) -> Dict[str, Any]:
    sleep(duration)
    return {"slept": duration}
