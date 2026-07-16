from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.config import settings
from app.models.entities import Build, Offer, Product
from app.schemas.builds import BuildComponentOut, BuildOut
from app.schemas.products import BenchmarkOut, OfferOut, ProductOut, StoreOut
from app.services.bottleneck import bottleneck_service
from app.services.compatibility import compatibility_engine


def store_to_schema(store) -> StoreOut:
    return StoreOut(
        id=store.id,
        slug=store.slug,
        name=store.name,
        base_url=store.base_url,
        country=store.country,
        is_active=store.is_active,
        parser_type=store.parser_type,
        parser_config=store.parser_config or {},
        last_success_at=store.last_success_at,
    )


def offer_to_schema(offer: Offer) -> OfferOut:
    stale_before = datetime.now(UTC) - timedelta(hours=settings.offer_stale_hours)
    fetched = offer.fetched_at
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=UTC)
    return OfferOut(
        id=offer.id,
        store=store_to_schema(offer.store),
        external_id=offer.external_id,
        url=offer.url,
        price=offer.price,
        shipping_price=offer.shipping_price,
        effective_price=offer.price + offer.shipping_price,
        currency=offer.currency,
        in_stock=offer.in_stock,
        stock_quantity=offer.stock_quantity,
        source_metadata=offer.source_metadata or {},
        fetched_at=offer.fetched_at,
        stale=fetched < stale_before,
    )


def product_to_schema(product: Product) -> ProductOut:
    offers = sorted(
        [offer for offer in product.offers if offer.is_active],
        key=lambda offer: (not offer.in_stock, offer.price + offer.shipping_price),
    )[:10]
    return ProductOut(
        id=product.id,
        category=product.category,
        brand=product.brand,
        name=product.name,
        sku=product.sku,
        ean=product.ean,
        mpn=product.mpn,
        image_url=product.image_url,
        gallery_urls=product.gallery_urls or [],
        canonical_source=product.canonical_source,
        canonical_id=product.canonical_id,
        source_url=product.source_url,
        release_date=product.release_date,
        performance_score=product.performance_score,
        noise_score=product.noise_score,
        upgrade_score=product.upgrade_score,
        quality_score=product.quality_score,
        specs=product.specs,
        status=product.status,
        version=product.version,
        offers=[offer_to_schema(offer) for offer in offers],
        benchmarks=[
            BenchmarkOut(
                workload=item.workload,
                resolution=item.resolution,
                score=item.score,
                unit=item.unit,
                source=item.source,
                measured_at=item.measured_at,
            )
            for item in getattr(product, "benchmarks", [])
        ],
    )


def build_to_schema(build: Build) -> BuildOut:
    product_map = {component.category: component.product for component in build.components}
    language = (build.requirements or {}).get("language", "ru")
    issues = compatibility_engine.validate(product_map, language)
    component_price = sum(
        (
            component.selected_offer.price * component.quantity
            for component in build.components
            if component.selected_offer is not None
        ),
        Decimal("0"),
    )
    requirements = build.requirements or {}
    bottleneck = bottleneck_service.assess(
        product_map, requirements.get("resolution"), requirements.get("language", "ru")
    )
    cpu = product_map.get("cpu")
    gpu = product_map.get("gpu")
    peak_power = compatibility_engine.estimated_peak_power_w(product_map)
    recommended_psu = (
        compatibility_engine.required_psu_w(cpu, gpu) if cpu is not None and gpu is not None else 0
    )
    return BuildOut(
        id=build.id,
        profile=build.profile,
        title=build.title,
        name=build.name,
        prompt=build.prompt,
        requirements=build.requirements,
        explanation=build.explanation,
        budget=build.budget,
        currency=build.currency,
        component_price=component_price,
        delivery_price=build.delivery_price,
        total_price=build.total_price,
        store_count=build.store_count,
        is_saved=build.is_saved,
        visibility=build.visibility,
        public_slug=build.public_slug,
        version=build.version,
        expires_at=build.expires_at,
        compatibility_status=compatibility_engine.status(issues),
        compatibility_issues=issues,
        bottleneck=bottleneck,
        estimated_peak_power_w=peak_power,
        recommended_psu_w=recommended_psu,
        components=[
            BuildComponentOut(
                category=component.category,
                product=product_to_schema(component.product),
                selected_offer=(
                    offer_to_schema(component.selected_offer)
                    if component.selected_offer is not None
                    else None
                ),
                quantity=component.quantity,
            )
            for component in sorted(build.components, key=lambda item: item.category)
        ],
    )
