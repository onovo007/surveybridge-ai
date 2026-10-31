from typer.testing import CliRunner

from surveybridge.cli import app


def test_cli_health_and_invalid_project(monkeypatch, tmp_path):
    monkeypatch.setenv("SURVEYBRIDGE_WORKSPACE", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(app, ["healthcheck"])
    assert result.exit_code == 0 and '"remote_checked": false' in result.stdout
    result = runner.invoke(app, ["assess", "../escape"])
    assert result.exit_code == 1 and "Invalid project ID" in result.stderr


def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0 and "series" in result.stdout
