from __future__ import annotations

from datetime import UTC, datetime

from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService
from seo_content_engine.services.markdown_renderer import MarkdownRenderer
from seo_content_engine.services.openai_client import OpenAIClient
from seo_content_engine.services.prompt_builder import PromptBuilder
from seo_content_engine.services.table_renderer import TableRenderer


class DraftGenerationService:
    @staticmethod
    def _generate_metadata(content_plan: dict, client: OpenAIClient) -> dict:
        system_prompt, user_prompt = PromptBuilder.metadata_prompts(content_plan)
        return client.generate_json(system_prompt, user_prompt)

    @staticmethod
    def _generate_sections(content_plan: dict, client: OpenAIClient) -> list[dict]:
        system_prompt, user_prompt = PromptBuilder.sections_prompts(content_plan)
        response = client.generate_json(system_prompt, user_prompt)
        return response.get("sections", [])

    @staticmethod
    def _generate_faqs(content_plan: dict, client: OpenAIClient) -> list[dict]:
        system_prompt, user_prompt = PromptBuilder.faq_prompts(content_plan)
        response = client.generate_json(system_prompt, user_prompt)
        return response.get("faqs", [])

    @staticmethod
    def generate(
        normalized: dict,
        keyword_intelligence: dict,
        openai_client: OpenAIClient | None = None,
    ) -> dict:
        content_plan = ContentPlanBuilder.build(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        client = openai_client or OpenAIClient()

        metadata = DraftGenerationService._generate_metadata(content_plan, client)
        sections = DraftGenerationService._generate_sections(content_plan, client)
        faqs = DraftGenerationService._generate_faqs(content_plan, client)
        tables = TableRenderer.render_all(content_plan["table_plan"], content_plan["data_context"])

        draft = {
            "version": "v2.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": content_plan["page_type"],
            "listing_type": content_plan["listing_type"],
            "entity": content_plan["entity"],
            "metadata": metadata,
            "sections": sections,
            "tables": tables,
            "faqs": faqs,
            "internal_links": content_plan["internal_links_plan"],
            "content_plan": content_plan,
            "keyword_intelligence_version": keyword_intelligence["version"],
        }

        draft["markdown_draft"] = MarkdownRenderer.render(draft)
        return draft