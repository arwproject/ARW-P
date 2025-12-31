from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .execution import ExecutionService
from .models import RunStatus, Workflow, WorkflowRun
from .serializers import (
    PauseRequestSerializer,
    ResumeRequestSerializer,
    RunRequestSerializer,
    WorkflowRunSerializer,
    WorkflowSerializer,
)


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().prefetch_related("nodes", "edges")
    serializer_class = WorkflowSerializer

    @action(detail=True, methods=["post"])
    def trigger(self, request, pk=None):
        workflow = self.get_object()
        serializer = RunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        execution_service = ExecutionService()
        run = execution_service.start_workflow(
            workflow=workflow,
            context=serializer.validated_data.get("context"),
            executor=serializer.validated_data.get("executor"),
        )
        run_serializer = WorkflowRunSerializer(run)
        return Response(run_serializer.data, status=status.HTTP_201_CREATED)


class WorkflowRunViewSet(
    mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = WorkflowRun.objects.select_related("workflow", "current_node").prefetch_related(
        "node_runs", "node_runs__node"
    )
    serializer_class = WorkflowRunSerializer

    def create(self, request, *args, **kwargs):
        run_request = RunRequestSerializer(data=request.data)
        run_request.is_valid(raise_exception=True)
        workflow_id = request.data.get("workflow")
        if not workflow_id:
            return Response({"detail": "workflow is required"}, status=status.HTTP_400_BAD_REQUEST)
        workflow = get_object_or_404(Workflow, pk=workflow_id)
        service = ExecutionService()
        run = service.start_workflow(
            workflow=workflow,
            context=run_request.validated_data.get("context"),
            executor=run_request.validated_data.get("executor"),
        )
        serializer = self.get_serializer(run)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        serializer = PauseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = self.get_object()
        service = ExecutionService()
        updated = service.pause_run(run, serializer.validated_data.get("reason", ""))
        return Response(WorkflowRunSerializer(updated).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        serializer = ResumeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = self.get_object()
        service = ExecutionService()
        updated = service.resume_run(run, serializer.validated_data.get("context"))
        return Response(WorkflowRunSerializer(updated).data)
