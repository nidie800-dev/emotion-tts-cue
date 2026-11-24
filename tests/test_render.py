import tempfile
import unittest
from pathlib import Path

from emocue.audio import wav_info
from emocue.backends.mock import MockBackend
from emocue.parser import parse_script
from emocue.render import render_script


class RenderTests(unittest.TestCase):
    def test_render_with_mock_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = parse_script("[happy:0.8] 你好\n[pause:0.3]\n[whisper] 小声说话\n")
            result = render_script(
                script,
                MockBackend(),
                out_dir=tmp,
                gap=0.1,
                sample_rate=16000,
            )

            self.assertTrue(result.full_wav.exists())
            self.assertTrue(result.cues_csv.exists())
            self.assertTrue(result.cues_mid.exists())
            self.assertTrue(result.project_json.exists())
            self.assertEqual(len(result.cues), 3)

            sample_rate, channels, duration = wav_info(result.full_wav)
            self.assertEqual(sample_rate, 16000)
            self.assertEqual(channels, 1)
            self.assertGreater(duration, 0.5)
            self.assertAlmostEqual(duration, result.total_duration, places=2)

            csv_text = result.cues_csv.read_text(encoding="utf-8-sig")
            self.assertIn("happy", csv_text)
            self.assertIn("pause", csv_text)

    def test_empty_script_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_script(parse_script("# empty"), MockBackend(), tmp)


if __name__ == "__main__":
    unittest.main()
