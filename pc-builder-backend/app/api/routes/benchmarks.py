from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models.entities import Product, ProductBenchmark, WorkloadProfile
from app.schemas.analysis import (
    BenchmarkImportRequest,
    BenchmarkImportResponse,
    WorkloadCreate,
    WorkloadOut,
)
from app.services.audit import audit
from app.services.i18n import normalize_language

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


def workload_to_schema(item: WorkloadProfile, language: str) -> WorkloadOut:
    lang = normalize_language(language)
    return WorkloadOut(
        slug=item.slug,
        name=item.names.get(lang) or item.names.get("en") or item.slug,
        names=item.names,
        kind=item.kind,
        unit=item.unit,
        lower_is_better=item.lower_is_better,
        accelerator=item.accelerator,
        default_resolution=item.default_resolution,
        settings=item.settings,
        source_url=item.source_url,
    )


@router.get("/workloads", response_model=list[WorkloadOut])
async def list_workloads(
    session: DbSession,
    language: str = Query(default="en", pattern="^(uk|en|pl|ru)$"),
    kind: str | None = Query(default=None, pattern="^(game|render|productivity)$"),
) -> list[WorkloadOut]:
    filters = [WorkloadProfile.is_active.is_(True)]
    if kind:
        filters.append(WorkloadProfile.kind == kind)
    result = await session.execute(
        select(WorkloadProfile).where(*filters).order_by(WorkloadProfile.kind, WorkloadProfile.slug)
    )
    return [workload_to_schema(item, language) for item in result.scalars()]


@router.post(
    "/admin/workloads",
    response_model=WorkloadOut,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_workload(
    payload: WorkloadCreate,
    session: DbSession,
    request: Request,
    admin: AdminUser,
) -> WorkloadOut:
    item = await session.scalar(select(WorkloadProfile).where(WorkloadProfile.slug == payload.slug))
    created = item is None
    values = payload.model_dump()
    if item is None:
        item = WorkloadProfile(**values)
        session.add(item)
    else:
        for key, value in values.items():
            setattr(item, key, value)
        item.is_active = True
    await audit(
        session,
        request,
        "benchmark.workload_upsert",
        "workload_profile",
        item.id,
        user_id=admin.id,
        details={"slug": payload.slug, "created": created},
    )
    await session.commit()
    await session.refresh(item)
    return workload_to_schema(item, "en")


@router.post("/admin/results/import", response_model=BenchmarkImportResponse)
async def import_results(
    payload: BenchmarkImportRequest,
    session: DbSession,
    request: Request,
    admin: AdminUser,
) -> BenchmarkImportResponse:
    created = 0
    updated = 0
    for row in payload.results:
        product = await session.get(Product, row.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {row.product_id} not found")
        workload = await session.scalar(
            select(WorkloadProfile).where(WorkloadProfile.slug == row.workload_slug)
        )
        if workload is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workload {row.workload_slug} not found",
            )
        filters = [
            ProductBenchmark.product_id == row.product_id,
            ProductBenchmark.workload == row.workload_slug,
        ]
        if row.resolution is None:
            filters.append(ProductBenchmark.resolution.is_(None))
        else:
            filters.append(ProductBenchmark.resolution == row.resolution)
        benchmark = await session.scalar(select(ProductBenchmark).where(*filters))
        if benchmark is None:
            session.add(
                ProductBenchmark(
                    product_id=row.product_id,
                    workload=row.workload_slug,
                    resolution=row.resolution,
                    score=row.score,
                    unit=row.unit,
                    source=row.source,
                )
            )
            created += 1
        else:
            benchmark.score = row.score
            benchmark.unit = row.unit
            benchmark.source = row.source
            updated += 1
    await audit(
        session,
        request,
        "benchmark.results_import",
        "product_benchmark",
        None,
        user_id=admin.id,
        details={"created": created, "updated": updated},
    )
    await session.commit()
    return BenchmarkImportResponse(created=created, updated=updated)
