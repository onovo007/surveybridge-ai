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
def countries(query: str | None = None, limit: int = 100, region: str | None = None):
    execute("list_countries", query=query, limit=limit, region=region)


@app.command()
def surveys(
    country_ids: Annotated[str | None, typer.Argument()] = None,
    from_year: int | None = None,
    to_year: int | None = None,
    region: str | None = None,
    countries: str | None = None,
):
    execute(
        "list_surveys",
        country_ids=(countries or country_ids).split(",") if countries or country_ids else None,
        from_year=from_year,
        to_year=to_year,
        region=region,
    )


@app.command()
def indicators(query: str, limit: int = 20):
    execute("search_indicators", query=query, limit=limit)


@app.command()
def series(
    indicator_id: str,
    countries: Annotated[str | None, typer.Argument()] = None,
    from_year: int | None = None,
    to_year: int | None = None,
    breakdown: str = "national",
    project_id: str | None = None,
    region: str | None = None,
    country_override: Annotated[str | None, typer.Option("--countries")] = None,
):
    execute(
        "get_indicator_series",
        indicator_id=indicator_id,
        country_ids=(country_override or countries).split(",")
        if country_override or countries
        else None,
        from_year=from_year,
        to_year=to_year,
        breakdown=breakdown,
        project_id=project_id,
        region=region,
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


@app.command()
def publications(
    region: str = "ssa",
    countries: str | None = None,
    publication_type: str | None = None,
    publication_year: int | None = None,
    fieldwork_year: int | None = None,
    indicator_category: str | None = None,
    from_year: int | None = None,
    to_year: int | None = None,
    include_web: bool = True,
    limit: int = 100,
):
    execute(
        "list_publications",
        region=region,
        country_ids=countries.split(",") if countries else None,
        publication_type=publication_type,
        publication_year=publication_year,
        fieldwork_year=fieldwork_year,
        indicator_category=indicator_category,
        from_year=from_year,
        to_year=to_year,
        include_web=include_web,
        limit=limit,
    )


@app.command("latest-surveys")
def latest_surveys(region: str = "ssa", countries: str | None = None):
    """Latest dated official reports per country, with fieldwork and completeness reported separately."""
    service = ResearchService(Settings())
    try:
        result = service.list_publications(
            region=region, country_ids=countries.split(",") if countries else None
        )
        result.data = {
            k: result.data[k]
            for k in ("latest_by_country", "country_checks", "source_completeness")
        }
        typer.echo(result.model_dump_json(indent=2))
    except (ValueError, OSError, DHSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    finally:
        service.close()


@app.command()
def report(report_url: str, verify_pdf: bool = False):
    execute("get_report_metadata", report_url=report_url, verify_pdf=verify_pdf)


@app.command("ssa-run")
def ssa_run(
    region: str = "ssa",
    countries: str | None = None,
    indicator_ids: str | None = None,
    from_year: int | None = None,
    to_year: int | None = None,
    all_available_rounds: bool = True,
    run_id: str | None = None,
    max_tasks: int | None = None,
    include_publications: bool = True,
    refresh_publications: bool = False,
):
    execute(
        "run_regional_project",
        region=region,
        country_ids=countries.split(",") if countries else None,
        indicator_ids=indicator_ids.split(",") if indicator_ids else None,
        from_year=from_year,
        to_year=to_year,
        all_available_rounds=all_available_rounds,
        run_id=run_id,
        max_tasks=max_tasks,
        include_publications=include_publications,
        refresh_publications=refresh_publications,
    )


@app.command("ssa-export")
def ssa_export(run_id: str, output_dir: str):
    execute("export_regional_project", run_id=run_id, output_dir=output_dir)


if __name__ == "__main__":
    app()
