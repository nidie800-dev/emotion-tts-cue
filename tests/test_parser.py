import unittest

from emocue.parser import parse_script


class ParserTests(unittest.TestCase):
    def test_emotion_and_intensity(self):
        script = parse_script("[happy:0.8] 今天天气真好。\n[whisper:0.9] 靠近一点。\n")
        self.assertEqual(len(script.segments), 2)
        self.assertEqual(script.segments[0].emotion, "happy")
        self.assertAlmostEqual(script.segments[0].intensity, 0.8)
        self.assertEqual(script.segments[1].emotion, "whisper")
        self.assertAlmostEqual(script.segments[1].intensity, 0.9)

    def test_sticky_emotion_and_intensity(self):
        script = parse_script("[sad:0.6]\n第一句\n第二句\n")
        self.assertEqual(len(script.segments), 2)
        for segment in script.segments:
            self.assertEqual(segment.emotion, "sad")
            self.assertAlmostEqual(segment.intensity, 0.6)

    def test_pause_segment(self):
        script = parse_script("[pause:0.5]\n[happy] 你好\n")
        self.assertEqual(script.segments[0].kind, "pause")
        self.assertAlmostEqual(script.segments[0].pause, 0.5)
        self.assertEqual(script.segments[1].emotion, "happy")

    def test_pause_in_milliseconds(self):
        script = parse_script("[pause:500ms] 你好\n")
        self.assertAlmostEqual(script.segments[0].pause, 0.5)

    def test_unknown_tag_warns_but_does_not_break(self):
        script = parse_script("[wow] 你好\n")
        self.assertTrue(script.warnings)
        self.assertEqual(script.segments[0].emotion, "neutral")

    def test_alias(self):
        script = parse_script("[joy:0.7] 你好\n")
        self.assertEqual(script.segments[0].emotion, "happy")

    def test_comments_and_blank_lines(self):
        script = parse_script("# comment\n\n// another\n[neutral] 你好\n")
        self.assertEqual(len(script.segments), 1)
        self.assertEqual(script.segments[0].text, "你好")

    def test_empty_script_warns(self):
        script = parse_script("# only comments\n")
        self.assertTrue(script.is_empty())
        self.assertTrue(script.warnings)


if __name__ == "__main__":
    unittest.main()
