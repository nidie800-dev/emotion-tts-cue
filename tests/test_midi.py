import tempfile
import unittest
from pathlib import Path

from emocue.midi import write_marker_midi


class MidiTests(unittest.TestCase):
    def test_marker_midi(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cues.mid"
            write_marker_midi(
                path,
                [(0.5, "01 happy 0.8"), (1.25, "02 whisper 0.9")],
                total_duration=3.0,
            )
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"MThd"))
            self.assertIn(b"MTrk", data)
            self.assertIn(b"01 happy 0.8", data)
            self.assertIn(b"02 whisper 0.9", data)
            self.assertIn(b"START", data)
            self.assertIn(b"END", data)


if __name__ == "__main__":
    unittest.main()
