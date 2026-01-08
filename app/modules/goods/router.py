from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.params import Query

from app.modules.goods.schemas.create import CreateGoodSchema
from app.modules.goods.schemas.create_variation_schema import CreateVariationSchema
from app.modules.goods.schemas.get_schemas import GetGoodsSchema
from app.modules.goods.schemas.set_remaining_stock_schema import SetRemainingStockSchema
from app.modules.goods.schemas.upload_photo_schema import UploadPhotoSchema
from app.modules.goods.service import GoodsService

router = APIRouter()


@router.get("/")
async def get_all(
    data: GetGoodsSchema = Depends(),
    service: GoodsService = Depends(),
):
    goods = await service.get_goods(data)
    return goods


@router.get("/{good_id}")
async def get_by_id(good_id: str, service: GoodsService = Depends()):
    good = await service.get_by_id(good_id)
    if good is None:
        raise HTTPException(
            detail="Good with provided id can not be found", status_code=404
        )
    return good


@router.put("/update")
async def update(data: CreateGoodSchema, service: GoodsService = Depends()):
    try:
        good = await service.update(data)
    except ValueError:
        raise HTTPException(
            detail="Good with provided id can not be found", status_code=404
        )
    return good


@router.post("/create")
async def create(data: CreateGoodSchema, service: GoodsService = Depends()):
    result = await service.create(data)
    return {
        "status": "success"
    }


@router.post("/variations/set-remaining-stock")
async def set_remaining_stock(
    data: SetRemainingStockSchema, service: GoodsService = Depends()
):
    return await service.set_remaining_stock(data)


@router.delete("/{good_id}")
async def delete(good_id: str, service: GoodsService = Depends()):
    try:
        await service.delete(good_id)
    except ValueError:
        raise HTTPException(
            detail="Good with provided id can not be found", status_code=404
        )
    return {"detail": "Good deleted successfully"}


@router.get("/variation/{variation_id}")
async def get_variation_by_id(variation_id: str, service: GoodsService = Depends()):
    variation = await service.get_variation_by_id(variation_id)
    if variation is None:
        raise HTTPException(
            detail="Good variation with provided id can not be found", status_code=404
        )
    return variation


@router.delete("/variation/{variation_id}")
async def delete_variation(variation_id: str, service: GoodsService = Depends()):
    try:
        await service.delete_variation(variation_id)
    except ValueError:
        raise HTTPException(
            detail="Good variation with provided id can not be found", status_code=404
        )
    return {"detail": "Good variation deleted successfully"}


@router.post("/variation/{good_id}", description="Create variation")
async def create_variation(
    good_id: str, data: CreateGoodSchema, service: GoodsService = Depends()
):
    return await service.create_variation(good_id, data)


@router.put("/variation/{variation_id}", description="Update variation")
async def update_variation(
    variation_id: str, data: CreateVariationSchema, service: GoodsService = Depends()
):
    try:
        variation = await service.update_variation(variation_id, data)
    except ValueError:
        raise HTTPException(
            detail="Good variation with provided id can not be found", status_code=404
        )
    return variation


@router.post("/variation/{variation_id}/upload-photo")
async def upload_variation_photo(
    variation_id: str, data: UploadPhotoSchema, service: GoodsService = Depends()
):
    try:
        await service.upload_photos(variation_id, data.url)
    except ValueError:
        raise HTTPException(
            detail="Good variation with provided id can not be found", status_code=404
        )
    return {"status": "success"}


@router.delete("/variation/{variation_id}/delete-photo/{id}")
async def delete_variation_photo(
    variation_id: str, id: str, service: GoodsService = Depends()
):
    try:
        variation = await service.delete_photo(variation_id, id)
    except ValueError:
        raise HTTPException(
            detail="Good variation with provided id can not be found", status_code=404
        )
    return variation
