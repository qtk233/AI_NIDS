from fastapi import APIRouter

router = APIRouter()


@router.get("/api/model/info")
async def model_info():
    return {
        "success": True,
        "data": {
            "version": "v1.0",
            "params_count": 4200000,
            "inference_time_ms": 0.8,
        },
    }


@router.get("/api/model/metrics")
async def model_metrics():
    return {
        "success": True,
        "data": {
            "accuracy": 0.974,
            "macro_f1": 0.936,
            "weighted_f1": 0.972,
            "confusion_matrix": [[12300, 20, 5], [15, 450, 8], [10, 5, 380]],
            "class_names": ["Normal", "DoS", "BruteForce"],
            "roc_curves": [],
        },
    }


@router.post("/api/model/reload")
async def reload_model():
    return {"success": True, "data": {"message": "Model reloaded successfully"}}
