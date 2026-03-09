from fastapi import FastAPI

from seo_content_engine.api.routes.generation import router as generation_router
from seo_content_engine.api.routes.health import router as health_router
from seo_content_engine.api.routes.keywords import router as keywords_router
from seo_content_engine.api.routes.review import router as review_router
from seo_content_engine.core.config import settings
from seo_content_engine.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(generation_router)
app.include_router(keywords_router)
app.include_router(review_router)