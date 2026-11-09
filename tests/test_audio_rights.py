"""Ensure unlicensed or unverified music cannot enter the mix."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mix_audio.py"

class AudioRightsTests(unittest.TestCase):
    def test_unverified_bgm_is_rejected_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            voice = tmp / "voice.wav"
            bgm = tmp / "music.wav"
            manifest = tmp / "assets.json"
            voice.write_bytes(b"placeholder")
            bgm.write_bytes(b"placeholder")
            manifest.write_text(json.dumps({"assets": [{"asset_id": "music-1"}]}), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--voiceover", str(voice), "--bgm", str(bgm),
                "--asset-id", "music-1", "--manifest", str(manifest), "--output", str(tmp / "mix.wav")
            ], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lacks verified commercial-use rights", result.stderr)

if __name__ == "__main__":
    unittest.main()
