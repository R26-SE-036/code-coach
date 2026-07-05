import unittest

from app.analysis.error_catalog import ERROR_CATALOG
from app.analysis.hint_engine import ERROR_KNOWLEDGE_BASE
from app.services.collaboration_service import COLLABORATION_CONTENT
from app.services.gamification_service import GAMIFICATION_CONTENT
from app.services.study_guider_service import STUDY_GUIDER_CONTENT


class ConceptContentCoverageTests(unittest.TestCase):
    """Every concept tag produced by a detectable error type must have
    learning content in each downstream service, so a struggling student
    always gets a concept-specific lesson, game, and collaboration prompt
    instead of the generic fallback."""

    def _detectable_concept_tags(self) -> set[str]:
        tags = set()
        for error_type in ERROR_CATALOG:
            self.assertIn(
                error_type,
                ERROR_KNOWLEDGE_BASE,
                f"{error_type} has no knowledge-base hints entry",
            )
            tags.add(ERROR_KNOWLEDGE_BASE[error_type].concept_tag)
        return tags

    def test_study_guider_covers_all_detectable_concepts(self) -> None:
        for concept_tag in self._detectable_concept_tags():
            self.assertIn(
                concept_tag,
                STUDY_GUIDER_CONTENT,
                f"study_guider_lessons.json is missing content for {concept_tag}",
            )

    def test_gamification_covers_all_detectable_concepts(self) -> None:
        for concept_tag in self._detectable_concept_tags():
            self.assertIn(
                concept_tag,
                GAMIFICATION_CONTENT,
                f"gamification_catalog.json is missing content for {concept_tag}",
            )

    def test_collaboration_covers_all_detectable_concepts(self) -> None:
        for concept_tag in self._detectable_concept_tags():
            self.assertIn(
                concept_tag,
                COLLABORATION_CONTENT,
                f"collaboration_prompts.json is missing content for {concept_tag}",
            )

    def test_content_ids_are_unique_across_concepts(self) -> None:
        lesson_ids = [item.lesson.lesson_id for item in STUDY_GUIDER_CONTENT.values()]
        quiz_ids = [item.quiz.quiz_id for item in STUDY_GUIDER_CONTENT.values()]
        game_ids = [item.game_id for item in GAMIFICATION_CONTENT.values()]

        self.assertEqual(len(lesson_ids), len(set(lesson_ids)), "duplicate lesson_id")
        self.assertEqual(len(quiz_ids), len(set(quiz_ids)), "duplicate quiz_id")
        self.assertEqual(len(game_ids), len(set(game_ids)), "duplicate game_id")


if __name__ == "__main__":
    unittest.main()
