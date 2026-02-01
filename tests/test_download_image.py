import os
import requests
from unittest.mock import Mock

from af.cli.make_local import download_image


class MockResponse:
    def __init__(self, status_code, content_chunks):
        self.status_code = status_code
        self.content_chunks = content_chunks

    def iter_content(self, chunk_size):
        return self.content_chunks

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_skip_existing_file(monkeypatch, capsys):
    mock_get = Mock()
    mock_exists = Mock(return_value=True)

    monkeypatch.setattr(os.path, 'exists', mock_exists)
    monkeypatch.setattr(requests, "get", mock_get)

    download_image("http://example.com/img.jpg", "path/to/img.jpg", force=False)

    mock_exists.assert_called_once_with("path/to/img.jpg")
    mock_get.assert_not_called()


def test_calls_download_when_forced(monkeypatch):
    mock_get = Mock(return_value=Mock(status_code=404))
    mock_exists = Mock(return_value=True)

    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(requests, "get", mock_get)

    download_image("http://example.com/img.jpg", "path/to/img.jpg", force=True)

    # Even though file exists, force=True means requests.get SHOULD be called
    mock_get.assert_called_once()


def test_no_file_write_on_http_error(monkeypatch):
    mock_exists = Mock(return_value=False)
    mock_get = Mock(return_value=Mock(status_code=404))
    mock_open = Mock()

    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr("builtins.open", mock_open)

    download_image("http://example.com/url.jpg", "dest.jpg", force=False)

    mock_get.assert_called_once()
    mock_open.assert_not_called()


def test_full_download_logic(monkeypatch):
    # 1. Setup Data
    mock_chunks = [b"data_part_1", b"data_part_2"]

    # 2. Setup Mocks
    mock_exists = Mock(return_value=False)

    # Mock the response object and its iter_content method
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content = Mock(return_value=mock_chunks)

    # Mock requests.get to return our mock_response
    mock_get = Mock(return_value=mock_response)

    # Mock file operations
    mock_file = Mock()
    mock_open = Mock(return_value=mock_file)
    # Mocking the context manager 'with open(...) as file'
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)

    # 3. Apply Mocks
    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr("builtins.open", mock_open)

    # 4. Execute
    download_image("http://example.com/img.jpg", "path/to/img.jpg", force=False)

    # 5. Assertions
    # Check that we actually tried to write the chunks
    assert mock_file.write.call_count == 2
    mock_file.write.assert_any_call(b"data_part_1")
    mock_file.write.assert_any_call(b"data_part_2")

    mock_response.iter_content.assert_called_once()
