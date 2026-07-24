from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


async def http_exception_handler(request: Request, exc: HTTPException,) -> JSONResponse: 
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        }),
    ) 

async def validation_exception_handler(request: Request, exc: RequestValidationError,) -> JSONResponse:
     
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=jsonable_encoder(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": exc.errors(),
                },
            }
        ),
    )


async def general_exception_handler(request: Request, exc: Exception,) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
        }),
    )