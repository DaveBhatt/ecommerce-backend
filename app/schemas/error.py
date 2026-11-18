from pydantic import BaseModel, ConfigDict, Field


class ProblemDetails(BaseModel):
    """
    RFC 9457 Problem Details response schema.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "about:blank",
                    "title": "Not Found",
                    "status": 404,
                    "detail": "Product not found",
                    "instance": "/api/v1/products/123",
                    "code": "PRODUCT_NOT_FOUND",
                }
            ]
        }
    )

    type: str = Field(
        default="about:blank",
        description="URI reference identifying the problem type.",
    )

    title: str = Field(
        description="Short, human-readable summary of the problem.",
    )

    status: int = Field(
        description="HTTP status code.",
        ge=400,
        le=599,
    )

    detail: str = Field(
        description="Human-readable explanation specific to this occurrence.",
    )

    instance: str = Field(
        description="URI reference identifying this occurrence.",
    )

    code: str = Field(
        description="Application-specific error code.",
    )

    errors: list[dict] | None = Field(
        default=None,
        description="Optional validation error details.",
    )
