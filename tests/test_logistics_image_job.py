import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from logistics_image_job import generate_logistics_image


class GenerateLogisticsImageTest(unittest.TestCase):
    @patch.dict(os.environ, {"INFRAI_API_KEY": "test-key"})
    @patch("logistics_image_job.OpenAI")
    def test_saves_png_under_stable_job_id(self, openai: MagicMock) -> None:
        png = b"\x89PNG\r\n\x1a\nexample"
        openai.return_value.images.generate.return_value.data = [
            MagicMock(b64_json=base64.b64encode(png).decode("ascii"))
        ]

        with tempfile.TemporaryDirectory() as directory:
            saved = generate_logistics_image(
                job_id="shipment-4821",
                prompt="A sealed parcel at a staffed dispatch counter",
                output_dir=Path(directory),
            )

            self.assertEqual(saved.name, "shipment-4821.png")
            self.assertEqual(saved.read_bytes(), png)
            openai.return_value.images.generate.assert_called_once_with(
                model="auto",
                prompt="A sealed parcel at a staffed dispatch counter",
                size="1024x1024",
                response_format="b64_json",
                extra_headers={"Idempotency-Key": "shipment-4821"},
            )


if __name__ == "__main__":
    unittest.main()
