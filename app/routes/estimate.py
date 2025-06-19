from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db  # ✅ correct
from app.dependencies import get_current_user  # ✅ correct
from app.schemas.estimate import EstimateRequest, EstimateResponse  # ✅ correct
from app.models import User  # ✅ correct

router = APIRouter()

@router.post("/", response_model=EstimateResponse)
def estimate_model(
    data: EstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estimate print time and cost based on model metadata and user-selected options.
    """
    try:
        return calculate_estimate(data, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")