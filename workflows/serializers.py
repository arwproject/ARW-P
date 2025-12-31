from typing import Dict, Optional

from rest_framework import serializers

from .models import (
    ExecutorChoices,
    NodeParameter,
    NodeRun,
    RunStatus,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowRun,
)


class NodeParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeParameter
        fields = ["id", "key", "value", "required", "description"]
        read_only_fields = ["id"]


class WorkflowNodeSerializer(serializers.ModelSerializer):
    parameters = NodeParameterSerializer(many=True, required=False)

    class Meta:
        model = WorkflowNode
        fields = [
            "id",
            "name",
            "ref",
            "kind",
            "callable_path",
            "executor",
            "allow_parallel",
            "order",
            "metadata",
            "parameters",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: Dict) -> WorkflowNode:
        parameters = validated_data.pop("parameters", [])
        workflow = self.context.get("workflow")
        node = WorkflowNode.objects.create(workflow=workflow, **validated_data)
        for parameter in parameters:
            NodeParameter.objects.create(node=node, **parameter)
        return node


class WorkflowEdgeSerializer(serializers.ModelSerializer):
    from_ref = serializers.CharField(write_only=True)
    to_ref = serializers.CharField(write_only=True)
    from_node = serializers.CharField(source="from_node.ref", read_only=True)
    to_node = serializers.CharField(source="to_node.ref", read_only=True)

    class Meta:
        model = WorkflowEdge
        fields = ["id", "from_ref", "to_ref", "from_node", "to_node", "condition"]
        read_only_fields = ["id", "from_node", "to_node"]


class WorkflowSerializer(serializers.ModelSerializer):
    nodes = WorkflowNodeSerializer(many=True, required=False)
    edges = WorkflowEdgeSerializer(many=True, required=False)

    class Meta:
        model = Workflow
        fields = [
            "id",
            "name",
            "description",
            "default_executor",
            "is_active",
            "nodes",
            "edges",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data: Dict) -> Workflow:
        nodes_data = validated_data.pop("nodes", [])
        edges_data = validated_data.pop("edges", [])
        workflow = Workflow.objects.create(**validated_data)
        ref_map = {}
        for node_data in nodes_data:
            parameters = node_data.pop("parameters", [])
            node = WorkflowNode.objects.create(workflow=workflow, **node_data)
            for parameter_data in parameters:
                NodeParameter.objects.create(node=node, **parameter_data)
            ref_map[node.ref] = node

        for edge_data in edges_data:
            from_node = ref_map.get(edge_data["from_ref"])
            to_node = ref_map.get(edge_data["to_ref"])
            if not from_node or not to_node:
                raise serializers.ValidationError("Edge references unknown node ref.")
            WorkflowEdge.objects.create(
                workflow=workflow,
                from_node=from_node,
                to_node=to_node,
                condition=edge_data.get("condition", ""),
            )
        return workflow


class NodeRunSerializer(serializers.ModelSerializer):
    node_ref = serializers.CharField(source="node.ref", read_only=True)
    node_name = serializers.CharField(source="node.name", read_only=True)

    class Meta:
        model = NodeRun
        fields = [
            "id",
            "node_ref",
            "node_name",
            "status",
            "output",
            "error",
            "executor",
            "started_at",
            "finished_at",
        ]
        read_only_fields = [
            "id",
            "node_ref",
            "node_name",
            "status",
            "output",
            "error",
            "executor",
            "started_at",
            "finished_at",
        ]


class WorkflowRunSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source="workflow.name", read_only=True)
    node_runs = NodeRunSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRun
        fields = [
            "id",
            "workflow",
            "workflow_name",
            "status",
            "executor",
            "context",
            "pause_reason",
            "current_node",
            "started_at",
            "finished_at",
            "node_runs",
        ]
        read_only_fields = [
            "id",
            "workflow_name",
            "status",
            "pause_reason",
            "current_node",
            "started_at",
            "finished_at",
            "node_runs",
        ]


class RunRequestSerializer(serializers.Serializer):
    context = serializers.DictField(required=False)
    executor = serializers.ChoiceField(
        choices=ExecutorChoices.choices, required=False, allow_null=True
    )


class PauseRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ResumeRequestSerializer(serializers.Serializer):
    context = serializers.DictField(required=False)
