import unittest
from unittest.mock import Mock

import cv2
import numpy as np

from rainyun.main import (
    LazyDdddOcr,
    MatchResult,
    SiftMatcher,
    StrategyCaptchaSolver,
    TemplateMatcher,
    check_answer,
    compute_template_similarity,
)
from rainyun.utils.image import encode_image_bytes


class CaptchaStrategyTests(unittest.TestCase):
    def setUp(self):
        self.positions = [(8, 12), (28, 12), (48, 12)]
        rng = np.random.default_rng(20261006)
        self.sprites = [rng.integers(0, 256, (8, 8, 3), dtype=np.uint8) for _ in range(3)]
        self.background = np.full((24, 60, 3), 255, dtype=np.uint8)
        self.bboxes = [(4, 8, 12, 16), (24, 8, 32, 16), (44, 8, 52, 16)]
        for sprite, (x1, y1, x2, y2) in zip(self.sprites, self.bboxes):
            self.background[y1:y2, x1:x2] = sprite

    def matcher(self, name, positions=None, scores=None):
        matcher = Mock(name=name)
        matcher.name = name
        matcher.match.return_value = MatchResult(
            positions=self.positions if positions is None else positions,
            similarities=[1.0] * 3 if scores is None else scores,
            method=name,
        )
        return matcher

    def test_low_sift_scores_fall_through_to_template(self):
        sift = self.matcher("sift", scores=[0.0, 0.04, 0.0])
        solver = StrategyCaptchaSolver([sift, TemplateMatcher()])
        result = solver.solve(self.background, self.sprites, self.bboxes)
        self.assertIsNotNone(result)
        self.assertEqual(result.method, "template")
        self.assertEqual(result.positions, self.positions)
        self.assertTrue(check_answer(result))

    def test_real_sift_and_template_solve_small_sprites(self):
        solver = StrategyCaptchaSolver([SiftMatcher(), TemplateMatcher()])
        result = solver.solve(self.background, self.sprites, self.bboxes)
        self.assertIsNotNone(result)
        self.assertEqual(result.positions, self.positions)
        self.assertTrue(check_answer(result))

    def test_duplicate_coordinates_fall_through(self):
        invalid = self.matcher("sift", positions=[(8, 12)] * 3)
        result = StrategyCaptchaSolver([invalid, TemplateMatcher()]).solve(
            self.background, self.sprites, self.bboxes
        )
        self.assertEqual(result.method, "template")
        self.assertEqual(result.positions, self.positions)

    def test_valid_first_strategy_does_not_run_second(self):
        first, second = self.matcher("sift"), self.matcher("template")
        result = StrategyCaptchaSolver([first, second]).solve(
            self.background, self.sprites, self.bboxes
        )
        self.assertEqual(result.method, "sift")
        second.match.assert_not_called()

    def test_all_invalid_strategies_return_none(self):
        matchers = [self.matcher("sift", scores=[0.0] * 3), self.matcher("template", scores=[0.1] * 3)]
        self.assertIsNone(
            StrategyCaptchaSolver(matchers).solve(self.background, self.sprites, self.bboxes)
        )

    def test_missing_candidates_do_not_produce_clicks(self):
        self.assertIsNone(TemplateMatcher().match(self.background, self.sprites, []))
        result = TemplateMatcher().match(self.background, self.sprites, self.bboxes[:2])
        self.assertTrue(result is None or not check_answer(result))

    def test_nonfinite_scores_are_rejected(self):
        for score in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(score=score):
                self.assertFalse(check_answer(MatchResult(self.positions, [score, 1.0, 1.0], "test")))

    def test_wrong_result_lengths_are_rejected(self):
        for positions, scores in (
            (self.positions[:2], [1.0] * 3),
            (self.positions, [1.0] * 2),
            (self.positions + [(58, 12)], [1.0] * 4),
        ):
            with self.subTest(positions=positions, scores=scores):
                self.assertFalse(check_answer(MatchResult(positions, scores, "test")))

    def test_constant_templates_are_not_perfect_matches(self):
        blank = np.full((8, 8, 3), 255, dtype=np.uint8)
        self.assertEqual(compute_template_similarity(blank, self.sprites[0]), 0.0)
        self.assertEqual(compute_template_similarity(self.sprites[0], blank), 0.0)
        self.assertEqual(compute_template_similarity(blank, blank), 0.0)


class DdddOcrIntegrationTests(unittest.TestCase):
    def test_ocr_and_detection_inference_with_installed_models(self):
        image = np.full((64, 160, 3), 255, dtype=np.uint8)
        cv2.putText(image, "ABC", (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 2)
        payload = encode_image_bytes(image, "test")
        ocr = LazyDdddOcr()
        det = LazyDdddOcr(det=True)
        self.assertIsInstance(ocr.classification(payload), str)
        self.assertIsInstance(det.detection(payload), list)
        blank = encode_image_bytes(np.full_like(image, 255), "blank")
        self.assertEqual(det.detection(blank), [])


if __name__ == "__main__":
    unittest.main()
