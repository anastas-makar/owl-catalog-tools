from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import unittest

from PIL import Image

from owl_catalog_tools.build_catalog import (
    CatalogValidationError,
    build_image_url,
    require_coordinate,
    require_complete_unique_location_assignment,
    require_positive_integer,
    normalize_locale,
    validate_s3_images,
    validate_version_locale,
)


def make_png(width: int, height: int) -> bytes:
    output = BytesIO()
    Image.new(
        "RGBA",
        (width, height),
        (255, 255, 255, 0),
    ).save(output, format="PNG")
    return output.getvalue()


class ImageHandler(BaseHTTPRequestHandler):
    image_bytes = make_png(200, 100)
    requests_by_path: dict[str, int] = {}

    def do_HEAD(self) -> None:
        self._respond(include_body=False)

    def do_GET(self) -> None:
        self._respond(include_body=True)

    def _respond(self, include_body: bool) -> None:
        self.requests_by_path[self.path] = (
            self.requests_by_path.get(self.path, 0) + 1
        )

        if self.path == "/bucket/missing.png":
            self.send_error(404)
            return

        if self.path == "/bucket/wrong-content.webp":
            content_type = "application/octet-stream"
        else:
            content_type = "image/png"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length",
            str(len(self.image_bytes)),
        )
        self.end_headers()

        if include_body:
            self.wfile.write(self.image_bytes)

    def log_message(self, format: str, *args: object) -> None:
        pass


class ValidationHelpersTest(unittest.TestCase):
    def test_positive_integer_accepts_positive_value(self) -> None:
        self.assertEqual(
            require_positive_integer("test", "amount", 2),
            2,
        )

    def test_positive_integer_rejects_zero(self) -> None:
        with self.assertRaises(CatalogValidationError):
            require_positive_integer("test", "amount", 0)

    def test_coordinate_rejects_boolean(self) -> None:
        with self.assertRaises(CatalogValidationError):
            require_coordinate("test", "x", True)

    def test_location_assignment_reassigns_flexible_slot(self) -> None:
        require_complete_unique_location_assignment(
            "Map 'test'",
            [
                ("flexible", ["rare", "common"]),
                ("strict", ["rare"]),
            ],
        )

    def test_location_assignment_rejects_insufficient_pool(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "matched 1 of 2",
        ):
            require_complete_unique_location_assignment(
                "Map 'test'",
                [
                    ("first", ["only-location"]),
                    ("second", ["only-location"]),
                ],
            )

    def test_location_assignment_accepts_no_random_slots(self) -> None:
        require_complete_unique_location_assignment(
            "Map 'test'",
            [],
        )

    def test_locale_is_normalized(self) -> None:
        self.assertEqual(normalize_locale(" RU "), "ru")
        self.assertEqual(normalize_locale("pt_BR"), "pt-br")

    def test_invalid_locale_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "locale must be",
        ):
            normalize_locale("russian")

    def test_release_version_must_match_locale(self) -> None:
        validate_version_locale("catalog-ru-v0.1.4", "ru")

        with self.assertRaisesRegex(
                CatalogValidationError,
                "does not match",
        ):
            validate_version_locale("catalog-en-v0.1.4", "ru")

    def test_old_release_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "catalog-<locale>-vX.Y.Z",
        ):
            validate_version_locale("catalog-v0.1.4", "ru")

    def test_development_version_is_allowed(self) -> None:
        validate_version_locale("dev-0123456789ab", "ru")


class S3ImageValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            ImageHandler,
        )
        cls.thread = Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()
        cls.base_url = (
            f"http://127.0.0.1:{cls.server.server_port}/bucket/"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        ImageHandler.requests_by_path.clear()

    @staticmethod
    def catalog_with_images(
            image_keys: list[str],
            furniture: list[dict[str, object]] | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        return {
            "animals": [
                {
                    "templateId": f"animal-{index}",
                    "imageKey": image_key,
                }
                for index, image_key in enumerate(image_keys)
            ],
            "furniture": furniture or [],
        }

    def test_image_url_quotes_path_without_escaping_slashes(self) -> None:
        self.assertEqual(
            build_image_url(
                "https://example.test/bucket/",
                "locations/a file.webp",
            ),
            "https://example.test/bucket/locations/a%20file.webp",
        )

    def test_existing_image_with_correct_content_type_passes(self) -> None:
        validate_s3_images(
            self.catalog_with_images(["ok.png"]),
            image_base_url=self.base_url,
            furniture_aspect_ratio_tolerance=0.05,
        )

    def test_duplicate_image_key_is_requested_once(self) -> None:
        validate_s3_images(
            self.catalog_with_images(["ok.png", "ok.png"]),
            image_base_url=self.base_url,
            furniture_aspect_ratio_tolerance=0.05,
        )

        self.assertEqual(
            ImageHandler.requests_by_path["/bucket/ok.png"],
            1,
        )

    def test_missing_image_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "HTTP 404",
        ):
            validate_s3_images(
                self.catalog_with_images(["missing.png"]),
                image_base_url=self.base_url,
                furniture_aspect_ratio_tolerance=0.05,
            )

    def test_wrong_content_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(
                CatalogValidationError,
                "invalid Content-Type",
        ):
            validate_s3_images(
                self.catalog_with_images(["wrong-content.webp"]),
                image_base_url=self.base_url,
                furniture_aspect_ratio_tolerance=0.05,
            )

    def test_matching_furniture_aspect_ratio_passes(self) -> None:
        furniture = {
            "templateId": "wide-table",
            "imageKey": "furniture.png",
            "width": 0.4,
            "height": 0.2,
        }

        validate_s3_images(
            self.catalog_with_images([], [furniture]),
            image_base_url=self.base_url,
            furniture_aspect_ratio_tolerance=0.05,
        )

    def test_distorted_furniture_aspect_ratio_is_rejected(self) -> None:
        furniture = {
            "templateId": "distorted-table",
            "imageKey": "furniture.png",
            "width": 0.2,
            "height": 0.2,
        }

        with self.assertRaisesRegex(
                CatalogValidationError,
                "aspect ratio mismatch",
        ):
            validate_s3_images(
                self.catalog_with_images([], [furniture]),
                image_base_url=self.base_url,
                furniture_aspect_ratio_tolerance=0.05,
            )


if __name__ == "__main__":
    unittest.main()
