import typing as t

from piccolo.engine import engine_finder
from piccolo_admin.endpoints import create_admin
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.types import ASGIApp, Receive, Scope, Send

from home.endpoints import create_task, delete_task, home, tasks, update_task
from home.piccolo_app import APP_CONFIG
from home.tables import Task
from starlite import (
    MiddlewareProtocol,
    OpenAPIConfig,
    Request,
    Router,
    Starlite,
    StaticFilesConfig,
    TemplateConfig,
    asgi,
)
from starlite.template.jinja import JinjaTemplateEngine

# Piccolo Admin asgi app
admin_app = create_admin(
    tables=APP_CONFIG.table_classes,
    # Required when running under HTTPS:
    # allowed_hosts=['my_site.com']
)


# I don't know how to pass Piccolo Admin app to this route with asgi decorator
# because this function returns response and not asgi app and if response is not ok
# we get 500 error ImproperlyConfiguredException: Unable to serialize response content

# @asgi(path="/admin")
# async def admin(scope: Scope, receive: Receive, send: Send) -> None:
#     if scope["type"] == "http":
#         if scope["method"] == "GET":
#             response = Response({"hello": "world"}, status_code=HTTP_200_OK) ????
#             await response(scope=scope, receive=receive, send=send)
#         return
#     response = Response(
#         {"detail": "unsupported request"}, status_code=HTTP_400_BAD_REQUEST
#     )
#     await response(scope=scope, receive=receive, send=send)

# middleware for Piccolo Admin
class AdminMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp):
        self.app = admin_app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http":
            request = Request(scope)
        await self.app(scope, receive, send)


async def open_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        print("Unable to connect to the database")


async def close_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")


app = Starlite(
    debug=True,
    route_handlers=[home, tasks, create_task, update_task, delete_task],
    template_config=TemplateConfig(
        directory="home/templates", engine=JinjaTemplateEngine
    ),
    # uncomment this line to use Piccolo Admin middleware but
    # Piccolo Admin is mount to root path and any other route like
    # /tasks does not work
    # middleware=[AdminMiddleware],
    openapi_config=OpenAPIConfig(
        title="Starlite API",
        version="1.0.0",
    ),
    static_files_config=[
        StaticFilesConfig(directories=["static"], path="/static"),
    ],
    on_startup=[open_database_connection_pool],
    on_shutdown=[close_database_connection_pool],
)
