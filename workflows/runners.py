import importlib
from typing import Any, Dict

from .models import WorkflowNode


class NodeRunner:
    def run(self, node: WorkflowNode, context: Dict) -> Dict:
        if node.kind != WorkflowNode.TASK:
            return {}
        if not node.callable_path:
            raise ValueError(f"No callable configured for node {node.ref}")
        callable_path = node.callable_path
        module_path, function_name = callable_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        kwargs = self._build_kwargs(node=node, context=context)
        result: Any = func(**kwargs, context=context)
        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        return {"result": result}

    def _build_kwargs(self, node: WorkflowNode, context: Dict) -> Dict:
        kwargs: Dict[str, Any] = {}
        for parameter in node.parameters.all():
            value = parameter.value
            if isinstance(value, dict) and "from_context" in value:
                context_key = value["from_context"]
                kwargs[parameter.key] = context.get(context_key)
            else:
                kwargs[parameter.key] = value
        return kwargs
