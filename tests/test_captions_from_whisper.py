"""Unit-level tests for the deterministic caption preparation stage."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "captions_from_whisper.py"

class CaptionBuilderTests(unittest.TestCase):
    def test_groups_word_timestamps_and_preserves_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "transcript.json"
            source.write_text(json.dumps({"segments": [{"words": [
                {"word": "Stop", "start": 0.1, "end": 0.4},
                {"word": "scrolling", "start": 0.4, "end": 0.9},
                {"word": "right", "start": 1.0, "end": 1.2},
                {"word": "now!", "start": 1.2, "end": 1.5}
            ]}]}), encoding="utf-8")
            output = tmp / "captions.json"
            subprocess.run([sys.executable, str(SCRIPT), str(source), "--output", str(output)], check=True)
            captions = json.loads(output.read_text(encoding="utf-8"))["captions"]
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0]["text"], "Stop scrolling right now!")
            self.assertEqual(captions[0]["start"], 0.1)
            self.assertEqual(captions[0]["end"], 1.5)

if __name__ == "__main__":
    unittest.main()
