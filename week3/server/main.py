from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from config import configure_logging, get_settings
from schemas import GetMovieDetailsInput, SearchMoviesInput
from tmdb_client import TMDBClient, TMDBClientError

logger = configure_logging()
settings = get_settings()
client = TMDBClient(settings)

mcp = FastMCP("TMDB MCP Server", json_response=True)


def _serialize_error(error: TMDBClientError) -> dict[str, Any]:
    logger.warning("TMDB client error: %s", error.message)
    return error.to_dict()


@mcp.tool()
def search_movies(query: str, year: int | None = None, page: int = 1) -> dict[str, Any]:
    """Search TMDB movies by title, with optional year and page filters."""
    params = SearchMoviesInput(query=query, year=year, page=page)
    logger.info("search_movies called with query=%r year=%r page=%r", params.query, params.year, params.page)
    try:
        result = client.search_movies(query=params.query, year=params.year, page=params.page)
        return result.model_dump()
    except TMDBClientError as exc:
        return _serialize_error(exc)


@mcp.tool()
def get_movie_details(movie_id: int) -> dict[str, Any]:
    """Get detailed metadata for a TMDB movie by ID."""
    params = GetMovieDetailsInput(movie_id=movie_id)
    logger.info("get_movie_details called with movie_id=%r", params.movie_id)
    try:
        result = client.get_movie_details(movie_id=params.movie_id)
        return result.model_dump()
    except TMDBClientError as exc:
        return _serialize_error(exc)


@mcp.resource("tmdb://movie/{movie_id}")
def movie_resource(movie_id: str) -> str:
    """Read movie details as a resource using a TMDB movie ID."""
    try:
        numeric_id = int(movie_id)
        result = client.get_movie_details(movie_id=numeric_id)
        return result.model_dump_json(indent=2)
    except ValueError:
        return '{"error": "validation_error", "message": "movie_id must be an integer"}'
    except TMDBClientError as exc:
        return str(exc.to_dict())


@mcp.prompt()
def summarize_movie(title: str, focus: str = "plot and audience appeal") -> str:
    """Create a prompt for summarizing a movie after fetching its details."""
    return (
        f"Use the TMDB movie tools to find the movie titled '{title}'. "
        f"Then write a concise summary focused on {focus}. "
        "Include release year, genres, runtime, and a spoiler-light overview."
    )


def main() -> None:
    logger.info("Starting TMDB MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()