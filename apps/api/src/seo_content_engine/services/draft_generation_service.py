from __future__ import annotations

from datetime import UTC, datetime

from seo_content_engine.core.config import settings
from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.factual_validator import FactualValidator
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
    def _resolve_internal_links(internal_links: dict) -> dict:
        from seo_content_engine.services.output_formatter import OutputFormatter

        resolved: dict = {}
        for group_name, group_links in internal_links.items():
            if not isinstance(group_links, list):
                resolved[group_name] = group_links
                continue

            resolved_group = []
            for item in group_links:
                if isinstance(item, list):
                    nested_group = []
                    for nested in item:
                        updated = dict(nested)
                        if "url" in updated:
                            updated["url"] = OutputFormatter.resolve_url(updated.get("url"))
                        nested_group.append(updated)
                    resolved_group.append(nested_group)
                elif isinstance(item, dict):
                    updated = dict(item)
                    if "url" in updated:
                        updated["url"] = OutputFormatter.resolve_url(updated.get("url"))
                    resolved_group.append(updated)
            resolved[group_name] = resolved_group
        return resolved

    @staticmethod
    def _repair_metadata(content_plan: dict, metadata: dict, validation_report: dict, client: OpenAIClient) -> dict:
        issues_by_field = {
            field_name: report["issues"]
            for field_name, report in validation_report["metadata_checks"].items()
            if report["issues"]
        }
        if not issues_by_field:
            return metadata

        system_prompt, user_prompt = PromptBuilder.repair_metadata_prompt(content_plan, metadata, issues_by_field)
        repaired = client.generate_json(system_prompt, user_prompt)
        return repaired if isinstance(repaired, dict) else metadata

    @staticmethod
    def _repair_sections(content_plan: dict, sections: list[dict], validation_report: dict, client: OpenAIClient) -> list[dict]:
        check_map = {item["id"]: item["validation"] for item in validation_report["section_checks"]}
        repaired_sections: list[dict] = []

        for section in sections:
            validation = check_map.get(section.get("id"), {})
            issues = validation.get("issues", [])
            if not issues:
                repaired_sections.append(section)
                continue

            system_prompt, user_prompt = PromptBuilder.repair_section_prompt(content_plan, section, issues)
            repaired = client.generate_json(system_prompt, user_prompt)
            if isinstance(repaired, dict) and repaired.get("body"):
                repaired_sections.append(repaired)
            else:
                repaired_sections.append(section)

        return repaired_sections

    @staticmethod
    def _repair_faqs(content_plan: dict, faqs: list[dict], validation_report: dict, client: OpenAIClient) -> list[dict]:
        check_map = {item["question"]: item["validation"] for item in validation_report["faq_checks"]}
        repaired_faqs: list[dict] = []

        for faq in faqs:
            validation = check_map.get(faq.get("question"), {})
            issues = validation.get("issues", [])
            if not issues:
                repaired_faqs.append(faq)
                continue

            system_prompt, user_prompt = PromptBuilder.repair_faq_prompt(content_plan, faq, issues)
            repaired = client.generate_json(system_prompt, user_prompt)
            if isinstance(repaired, dict) and repaired.get("answer"):
                repaired_faqs.append(repaired)
            else:
                repaired_faqs.append(faq)

        return repaired_faqs

    @staticmethod
    def _build_base_draft(content_plan: dict, keyword_intelligence_version: str, metadata: dict, sections: list[dict], faqs: list[dict]) -> dict:
        tables = TableRenderer.render_all(content_plan["table_plan"], content_plan["data_context"])
        internal_links = DraftGenerationService._resolve_internal_links(content_plan["internal_links_plan"])

        return {
            "version": "v2.2",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": content_plan["page_type"],
            "listing_type": content_plan["listing_type"],
            "entity": content_plan["entity"],
            "metadata": metadata,
            "sections": sections,
            "tables": tables,
            "faqs": faqs,
            "internal_links": internal_links,
            "content_plan": content_plan,
            "keyword_intelligence_version": keyword_intelligence_version,
        }

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

        draft = DraftGenerationService._build_base_draft(
            content_plan=content_plan,
            keyword_intelligence_version=keyword_intelligence["version"],
            metadata=metadata,
            sections=sections,
            faqs=faqs,
        )

        validation_report = FactualValidator.validate_draft(draft)

        repair_passes = 0
        while not validation_report["passed"] and repair_passes < settings.draft_repair_max_passes:
            metadata = DraftGenerationService._repair_metadata(content_plan, draft["metadata"], validation_report, client)
            sections = DraftGenerationService._repair_sections(content_plan, draft["sections"], validation_report, client)
            faqs = DraftGenerationService._repair_faqs(content_plan, draft["faqs"], validation_report, client)

            draft = DraftGenerationService._build_base_draft(
                content_plan=content_plan,
                keyword_intelligence_version=keyword_intelligence["version"],
                metadata=metadata,
                sections=sections,
                faqs=faqs,
            )

            validation_report = FactualValidator.validate_draft(draft)
            repair_passes += 1

        draft = FactualValidator.apply_sanitization(draft, validation_report)
        draft["repair_passes_used"] = repair_passes
        draft["markdown_draft"] = MarkdownRenderer.render(draft)
        return draft