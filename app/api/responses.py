from typing import Any

from app.schemas.error import ProblemDetails


def problem_response(description: str) -> dict[str, Any]:
    """
    Build a reusable OpenAPI response definition
    for RFC 9457 Problem Details.
    """

    return {
        "description": description,
        "content": {
            "application/problem+json": {
                "schema": ProblemDetails.model_json_schema(),
            }
        },
    }


# Common errors that can occur across multiple endpoints.
COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: problem_response("Request validation failed."),
    500: problem_response("Internal server error."),
}