import os
import typing as t

import jinja2
from piccolo_api.crud.serializers import create_pydantic_model
from starlette.responses import Response as StraletteResponse

from home.tables import Task
from starlite import (
    MediaType,
    Request,
    Response,
    Template,
    delete,
    get,
    post,
    put,
)

ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
)


@get(path="/")
def home(request: Request) -> Template:
    template = ENVIRONMENT.get_template("home.html.jinja")

    content = template.render(
        title="Piccolo + ASGI",
    )

    return Template(name="home.html.jinja", context={"request": request})


# create pydantic models for Piccolo table
TaskModelIn: t.Any = create_pydantic_model(
    table=Task, include_default_columns=True, model_name="TaskModelIn"
)
TaskModelOut: t.Any = create_pydantic_model(
    table=Task, include_default_columns=True, model_name="TaskModelOut"
)

# CRUD routes
@get(path="/tasks/")
async def tasks(request: Request) -> t.List[TaskModelOut]:
    schema = request.app.openapi_schema
    return await Task.select().order_by(Task.id)


@post(path="/tasks/")
async def create_task(request: Request, data: TaskModelIn) -> Response:
    schema = request.app.openapi_schema
    task = Task(**data.dict())
    await task.save()
    return Response(
        task.__dict__,
        status_code=200,
        media_type=MediaType.JSON,
    )


@put(path="/tasks/{task_id:int}/")
async def update_task(
    request: Request, task_id: int, data: TaskModelIn
) -> Response:
    schema = request.app.openapi_schema
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return Response(
            {},
            status_code=404,
            media_type=MediaType.JSON,
        )

    for key, value in data.dict().items():
        setattr(task, key, value)

    await task.save()
    return Response(
        task.__dict__,
        status_code=200,
        media_type=MediaType.JSON,
    )


# I had to use Starlette response here because Starlite status_code 204
# has error h11._util.LocalProtocolError: Too much data for declared Content-Length
# and RuntimeError: Expected ASGI message 'http.response.body', but got 'http.response.start'.
@delete(path="/tasks/{task_id:int}/")
async def delete_task(request: Request, task_id: int) -> StraletteResponse:
    schema = request.app.openapi_schema
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return Response(
            {},
            status_code=404,
            media_type=MediaType.JSON,
        )
    await task.remove()

    return StraletteResponse(status_code=204)
