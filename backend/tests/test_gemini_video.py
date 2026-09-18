import unittest

from services.gemini_video import parse_visual_response


class GeminiVideoParsingTests(unittest.TestCase):
    def test_visual_response_is_normalized(self):
        result = parse_visual_response(
            '{"detected_language":"en","summary":"Demo","segments":['
            '{"start_seconds":1,"end_seconds":3,"spoken_text":"Hello",'
            '"on_screen_text":"VS Code","visual_actions":["open file"],'
            '"important":true}],"flowchart":[]}'
        )

        self.assertEqual(result["detected_language"], "en")
        self.assertEqual(result["segments"][0]["start_time"], 1000)
        self.assertEqual(result["segments"][0]["on_screen_text"], "VS Code")
        self.assertNotIn("html", result)


if __name__ == "__main__":
    unittest.main()