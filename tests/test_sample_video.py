"""Integration checks using generated video only; no private training media."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" /
          "gym-video-private-coach-zh" / "scripts" / "sample_video.py")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "requires FFmpeg")
class SampleVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="gym-skill-check-")
        cls.work = Path(cls.temporary.name)
        cls.source = cls.work / "合成训练 29.97.mp4"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
            "testsrc2=size=320x240:rate=30000/1001", "-t", "3",
            "-c:v", "mpeg4", "-pix_fmt", "yuv420p", str(cls.source),
        ], check=True, capture_output=True, timeout=30)
        cls.original = cls.source.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def invoke(self, *args, source=None):
        import sys
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(source or self.source), *map(str, args)],
            capture_output=True, text=True, timeout=60,
        )

    def test_overview_and_no_overwrite(self):
        out = self.work / "overview"
        result = self.invoke("--out", out, "--every", 0.5)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual([f["requested_source_seconds"] for f in manifest["frames"]],
                         [0, 0.5, 1, 1.5, 2, 2.5])
        self.assertNotIn(str(self.work), (out / "manifest.json").read_text())
        self.assertEqual(manifest["skipped_requests"], [{
            "requested_source_seconds": 3.0,
            "reason": "no frame decoded after seek near source end",
        }])
        for frame in manifest["frames"]:
            self.assertGreater((out / frame["file"]).stat().st_size, 0)
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "stream=width,height",
            "-of", "json", str(out / "frame_0001.jpg"),
        ], capture_output=True, text=True, check=True, timeout=30)
        self.assertEqual(json.loads(probe.stdout)["streams"][0], {"width": 320, "height": 240})
        self.assertNotEqual(self.invoke("--out", out).returncode, 0)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_detail_source_offsets(self):
        out = self.work / "detail"
        result = self.invoke("--out", out, "--start", 1, "--end", 2, "--every", 0.2)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((out / "manifest.json").read_text())
        self.assertEqual([f["requested_source_seconds"] for f in data["frames"]],
                         [1, 1.2, 1.4, 1.6, 1.8])

    def test_reject_invalid_requests_before_creating_output(self):
        cases = [
            ["--every", "0.01"], ["--start", "2", "--end", "1"],
            ["--end", "999"], ["--every", "0"], ["--every", "nan"],
            ["--every", "1e-320"], ["--max-frames", "201"],
        ]
        for index, args in enumerate(cases):
            with self.subTest(args=args):
                out = self.work / f"invalid-{index}"
                result = self.invoke("--out", out, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(out.exists())

    def test_non_video(self):
        source = self.work / "not-video.txt"
        source.write_text("synthetic input")
        out = self.work / "not-video-output"
        result = self.invoke("--out", out, source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
