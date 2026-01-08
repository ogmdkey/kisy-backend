import datetime
import os
from typing import Sequence
import uuid

import aiofiles
from fastapi import Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db.session import get_session
from app.modules.goods.entities import (
    GoodEntity,
    GoodVariationEntity,
    GoodVariationPhotoEntity,
)
from app.modules.goods.schemas.create import CreateGoodSchema
from app.modules.goods.schemas.create_variation_schema import CreateVariationSchema
from app.modules.goods.schemas.get_schemas import GetGoodsSchema
from app.modules.goods.schemas.set_remaining_stock_schema import SetRemainingStockSchema


class GoodsService:
    def __init__(self, db: AsyncSession = Depends(get_session)):
        self.db = db

    async def get_by_id(self, _id: str) -> GoodEntity:
        stmt = (
            select(GoodEntity)
            .where(GoodEntity.id == _id)
            .options(
                selectinload(GoodEntity.variations).selectinload(
                    GoodVariationEntity.photos
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().one_or_none()

    async def update(self, data: CreateGoodSchema) -> GoodEntity:
        async with self.db.begin():
            stmt = select(GoodEntity).where(GoodEntity.id == data.id)
            result = await self.db.execute(stmt)
            good = result.scalars().one_or_none()
            if good is None:
                raise ValueError("Good not found")

            good.title = data.title
            good.description = data.description
            good.show_in_catalog = (
                data.show_in_catalog
                if data.show_in_catalog is not None
                else good.show_in_catalog
            )

            self.db.add(good)

        return good

    async def get_variation_by_id(self, _id: str) -> GoodVariationEntity:
        stmt = (
            select(GoodVariationEntity)
            .options(selectinload(GoodVariationEntity.photos))
            .where(GoodVariationEntity.id == _id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().one_or_none()

    async def get_goods(self, data: GetGoodsSchema) -> Sequence[GoodEntity]:
        stmt = (
            select(GoodEntity)
            # .offset((data.page - 1) * data.size)
            # .limit(data.size)
            .options(
                selectinload(GoodEntity.variations).selectinload(
                    GoodVariationEntity.photos
                )
            )
        )
        if data.id:
            stmt = stmt.where(GoodEntity.id == data.id)

        if not data.show_hidden:
            stmt = stmt.where(GoodEntity.show_in_catalog == True)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, data: CreateGoodSchema):
        async with self.db.begin():
            good = GoodEntity(
                title=data.title,
                description=data.description,
            )
            self.db.add(good)

            variation = GoodVariationEntity(
                good=good,
                title=data.title,
                description=data.description,
            )
            self.db.add(variation)

        return good

    async def delete(self, good_id: str):
        async with self.db.begin():
            stmt = select(GoodEntity).where(GoodEntity.id == good_id)
            result = await self.db.execute(stmt)
            good = result.scalars().one_or_none()
            if good is None:
                raise ValueError("Good not found")
            await self.db.delete(good)

    async def create_variation(self, good_id: str, data: CreateGoodSchema):
        async with self.db.begin():
            variation = GoodVariationEntity(
                good_id=good_id,
                title=data.title,
                description=data.description,
            )
            self.db.add(variation)

        return variation

    async def delete_variation(self, variation_id: str):
        async with self.db.begin():
            stmt = select(GoodVariationEntity).where(
                GoodVariationEntity.id == variation_id
            )
            result = await self.db.execute(stmt)
            variation = result.scalars().one_or_none()
            if variation is None:
                raise ValueError("Variation not found")
            await self.db.delete(variation)

    async def update_variation(self, variation_id: str, data: CreateVariationSchema):
        async with self.db.begin():
            stmt = select(GoodVariationEntity).where(
                GoodVariationEntity.id == variation_id
            )
            result = await self.db.execute(stmt)
            variation = result.scalars().one_or_none()
            if variation is None:
                raise ValueError("Variation not found")

            variation.title = data.title
            variation.description = data.description
            variation.length = data.length
            variation.width = data.width
            variation.height = data.height
            variation.weight = data.weight

            self.db.add(variation)

        return variation

    async def upload_photos(
        self, variation_id: str, url: str
    ) -> GoodVariationEntity:
        async with self.db.begin():
            stmt = (
                select(GoodVariationEntity)
                .where(GoodVariationEntity.id == variation_id)
                .options(selectinload(GoodVariationEntity.photos))
            )
            result = await self.db.execute(stmt)
            variation = result.scalars().one_or_none()
            if variation is None:
                raise ValueError("Variation not found")

            photo = GoodVariationPhotoEntity(url=f"{url}", is_main=False)
            variation.photos.append(photo)

            self.db.add(variation)

        return variation

    async def delete_photo(self, variation_id: str, id: str) -> GoodVariationEntity:
        async with self.db.begin():
            stmt = (
                select(GoodVariationEntity)
                .where(GoodVariationEntity.id == variation_id)
                .options(selectinload(GoodVariationEntity.photos))
            )
            result = await self.db.execute(stmt)
            variation = result.scalars().one_or_none()
            if variation is None:
                raise ValueError("Variation not found")

            photo = next((p for p in variation.photos if p.id == id), None)
            if photo is None:
                raise ValueError("Photo not found")

            # delete file
            try:
                os.remove(f".{photo.url}")
            except FileNotFoundError:
                pass

            await self.db.delete(photo)

        return variation

    async def set_remaining_stock(
        self, data: SetRemainingStockSchema
    ) -> GoodVariationEntity:
        async with self.db.begin():
            stmt = select(GoodVariationEntity).where(
                GoodVariationEntity.id == data.variation_id
            )
            result = await self.db.execute(stmt)
            variation = result.scalars().one_or_none()
            if variation is None:
                raise ValueError("Variation not found")

            variation.remaining_stock = data.remaining_stock
            variation.remaining_stock_date = datetime.datetime.now()

            self.db.add(variation)

        return variation
