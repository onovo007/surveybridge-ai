"""Human CLI; all operations use the same services as MCP."""

import json
from typing import Annotated

import typer

from surveybridge.clients.dhs import DHSError
from surveybridge.config import Settings
from surveybridge.services.application import ResearchService
from surveybridge.utils.logging import configure_logging

app = typer.Typer(
    help="SurveyBridge AI: auditable public DHS aggregated research", no_args_is_help=True
)


def execute(method, **kwargs):
    configure_logging()
    service = ResearchService(Settings())
    try:
        result = getattr(service, method)(**kwargs)
        typer.echo(result.model_dump_json(indent=2))
        if result.status == "error":
            raise typer.Exit(1)
    except (ValueError, OSError, DHSError) as exc:
        typer.echo(json.dumps({"status": "error", "error": str(exc)}), err=True)
        raise typer.Exit(1) from exc
    finally:
        service.close()


@app.command()
def healthcheck():
    execute("healthcheck")


@app.command()
def countries(query: str | None = None, limit: int = 100):
    execute("list_countries", query=query, limit=limit)


@app.command()
def surveys(country_ids: str, from_year: int | None = None, to_year: int | None = None):
    execute(
        "list_surveys", country_ids=country_ids.split(","), from_year=from_year, to_year=to_year
    )


@app.command()
def indicators(query: str, limit: int = 20):
    execute("search_indicators", query=query, limit=limit)


@app.command()
def series(
    indicator_id: str,
    countries: str,
    from_year: int | None = None,
    to_year: int | None = None,
    breakdown: str = "national",
    project_id: str | None = None,
):
    execute(
        "get_indicator_series",
        indicator_id=indicator_id,
        country_ids=countries.split(","),
        from_year=from_year,
        to_year=to_year,
        breakdown=breakdown,
        project_id=project_id,
    )


@app.command()
def assess(project_id: str):
    execute("assess_comparability", project_id=project_id)


@app.command("export")
def export_command(
    project_id: str,
    output_dir: str,
    formats: Annotated[str, typer.Option()] = "csv,json,xlsx,notebook",
):
    execute(
        "export_project", project_id=project_id, output_dir=output_dir, formats=formats.split(",")
    )


@app.command()
def serve():
    from surveybridge.mcp_server import main

    main()


if __name__ == "__main__":
    app()
