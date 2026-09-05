import pytest

from pdf_search.ingestion.cli import main


def test_cli_rejects_missing_input_folder(tmp_path):
    missing_folder = tmp_path / "missing"

    with pytest.raises(SystemExit):
        main([str(missing_folder)])


def test_cli_rejects_empty_input_folder(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path)])
