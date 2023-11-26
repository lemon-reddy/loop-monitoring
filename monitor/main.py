from fastapi import APIRouter

router = APIRouter()

@router.post("/trigger_report")
async def trigger_report():
    return


@router.get("/get_report")
async def get_report():
    return