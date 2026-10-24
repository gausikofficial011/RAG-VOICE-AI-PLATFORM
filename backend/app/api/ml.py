"""
AI / ML Administration API Router
Provides access to Model Registry, Training Pipelines, Evaluation Metrics, and Deployment Lifecycle.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel

from backend.app.models.user import User
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import require_permission
from ml.registry.registry import model_registry
import ml.intent_classifier.train as intent_train
import ml.document_classifier.train as doc_train

router = APIRouter(prefix="/ml", tags=["MLOps & AI Models"])


class TrainModelRequest(BaseModel):
    dataset_version: str = "v1.0.0"
    hyperparameters: Dict[str, Any] = {}


class DeployVersionRequest(BaseModel):
    version: str


@router.get("/models")
async def list_models(current_user: User = Depends(require_permission(Permission.MODELS_READ))):
    """List all registered ML models with active versions and health status."""
    return model_registry.list_models()


@router.get("/models/{model_name}")
async def get_model(
    model_name: str,
    current_user: User = Depends(require_permission(Permission.MODELS_READ)),
):
    """Get specific ML model metadata, version history, and metrics."""
    m = model_registry.get_model(model_name)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found.")
    return m


@router.post("/models/{model_name}/train")
async def train_model(
    model_name: str,
    data: TrainModelRequest,
    current_user: User = Depends(require_permission(Permission.MODELS_TRAIN)),
):
    """
    Trigger controlled retraining of a specific ML component.
    Executes in a safe Python worker environment without arbitrary shell execution.
    """
    if model_name == "query_intent_classifier":
        metrics = intent_train.train()
    elif model_name == "document_classifier":
        metrics = doc_train.train()
    else:
        raise HTTPException(status_code=400, detail=f"Retraining not supported for '{model_name}'.")

    return {
        "success": True,
        "message": f"Successfully trained {model_name}.",
        "metrics": metrics,
    }


@router.post("/models/{model_name}/deploy")
async def deploy_model(
    model_name: str,
    data: DeployVersionRequest,
    current_user: User = Depends(require_permission(Permission.MODELS_DEPLOY)),
):
    """Promote a candidate model version to active DEPLOYED status."""
    deployed = model_registry.deploy_version(model_name, data.version)
    if not deployed:
        raise HTTPException(status_code=400, detail="Failed to deploy version. Version not found.")
    return {"success": True, "message": f"Version {data.version} deployed for {model_name}."}


@router.post("/models/{model_name}/rollback")
async def rollback_model(
    model_name: str,
    data: DeployVersionRequest,
    current_user: User = Depends(require_permission(Permission.MODELS_DEPLOY)),
):
    """Roll back active model to a previous stable version."""
    success = model_registry.rollback_version(model_name, data.version)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to rollback. Version not found.")
    return {"success": True, "message": f"Rolled back {model_name} to {data.version}."}


@router.get("/evaluation/overview")
async def get_evaluation_overview(current_user: User = Depends(require_permission(Permission.MODELS_READ))):
    """Retrieve system-wide ML evaluation summary."""
    models = model_registry.list_models()
    summary = []
    for m in models:
        active_ver = m.get("active_version")
        ver_info = m.get("versions", {}).get(active_ver, {})
        summary.append({
            "model_name": m["name"],
            "type": m["type"],
            "version": active_ver,
            "status": ver_info.get("status", "DEPLOYED"),
            "metrics": ver_info.get("metrics") or {},
        })
    return summary
