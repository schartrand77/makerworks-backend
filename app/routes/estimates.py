# app/routes/estimates.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.schemas.estimate import EstimateRequest, EstimateResponse
from app.schemas.token import TokenPayload
from app.services.estimate_service import calculate_estimate  # Assume you modularized logic

router = APIRouter(prefix="/estimates", tags=["Estimates"])


@router.post(
    "/",
    summary="Calculate print time and cost estimate",
    response_model=EstimateResponse,
    status_code=status.HTTP_200_OK,
)
def estimate_model(
    data: EstimateRequest,
    db: Session = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Estimate print time and cost based on user-selected options and model metadata.
    """
    try:
        return calculate_estimate(data, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")
