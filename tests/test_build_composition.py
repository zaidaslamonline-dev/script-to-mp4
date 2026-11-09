"""Fast approval-gate tests for the composition builder."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_composition.py"

class BuilderGateTests(unittest.TestCase):
    def test_unapproved_script_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            campaign = tmp / "campaign.json"
            campaign.write_text(json.dumps({
                "campaign_id": "t", "client_id": "missing",
                "script": {"approved_by_user": False},
                "production": {"voiceover_approved": True},
                "variants": [{"variant_id": "A", "approved": True}]
            }))
            board = tmp / "board.json"
            board.write_text(json.dumps({"variant_id": "A", "duration_seconds": 2, "scenes": [{"text":"Hi","start":0,"end":2}]}))
            voice = tmp / "voice.wav"
            voice.write_bytes(b"not-a-real-wav-but-exists")
            result = subprocess.run([sys.executable, str(BUILDER), "--campaign", str(campaign),
                "--storyboard", str(board), "--voiceover", str(voice), "--output-dir", str(tmp / "out")],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("script approval is required", result.stderr)

if __name__ == "__main__":
    unittest.main()
