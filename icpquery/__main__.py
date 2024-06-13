import asyncio
import inspect
import sys
from enum import Enum
from functools import partial, wraps

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typer import Argument, Option, Typer

from icpquery import ICPQueryError, SearchType, query


class AsyncTyper(Typer):
    @staticmethod
    def maybe_run_async(decorator, f):
        if inspect.iscoroutinefunction(f):

            @wraps(f)
            def runner(*args, **kwargs):
                return asyncio.run(f(*args, **kwargs))

            decorator(runner)
        else:
            decorator(f)
        return f

    def callback(self, *args, **kwargs):
        decorator = super().callback(*args, **kwargs)
        return partial(self.maybe_run_async, decorator)

    def command(self, *args, **kwargs):
        decorator = super().command(*args, **kwargs)
        return partial(self.maybe_run_async, decorator)


app = AsyncTyper(add_completion=False)
console = Console()


class SearchTypeChoice(str, Enum):
    """搜索类型"""

    DOMAIN = "domain"
    APP = "app"
    MINI_PROG = "mini_prog"
    FAST_PROG = "fast_prog"


class FormatTypeChoice(str, Enum):
    TTY = "tty"
    JSON = "json"
    TEXT = "text"


@app.command(help="查询ICP备案记录")
async def query_icp(
    keyword: str = Argument(
        help="域名/APP或备案号",
        show_default=False,
    ),
    search_type: SearchTypeChoice = Option(
        SearchTypeChoice.DOMAIN,
        "-t",
        "--type",
        help="搜索类型",
    ),
    format: FormatTypeChoice = Option(
        FormatTypeChoice.TTY,
        "-f",
        "--format",
        help="输出格式",
    ),
    captcha_max_retry: int = Option(
        10,
        "--max-retry",
        help="验证码最大重试次数",
    ),
):
    if format == FormatTypeChoice.TTY:
        table = Table.grid()
        table.add_row(
            Panel(
                Align(
                    f"正在查询ICP备案...\n"
                    f"关键字：[green]{keyword}[/]\n"
                    f"查询类型：[green]{search_type}[/]"
                )
            )
        )
        progress = Progress(
            SpinnerColumn(),
            "{task.description}",
            TextColumn("[green]{task.completed} / {task.total}"),
        )
        progress_task = progress.add_task("验证码识别中", total=captcha_max_retry, completed=1)
        table.add_row(progress)

        def on_captcha_try(count: int):
            progress.update(progress_task, completed=count + 1)

        with Live(table, console=console) as live:
            try:
                results = await query(
                    keyword,
                    SearchType[search_type.name],
                    captcha_cb=on_captcha_try,
                    captcha_max_retry=captcha_max_retry,
                )
            except ICPQueryError:
                live.update(
                    Panel(
                        Align(
                            "[bold red]ICP查询调用失败",
                            align="center",
                            vertical="middle",
                        ),
                        border_style="red",
                        height=5,
                    )
                )
            else:
                if results:
                    panel = Panel(results, title_align="left")
                    if results.search_type == SearchType.DOMAIN:
                        panel.title = "[green]域名备案查询成功"
                    elif results.search_type == SearchType.APP:
                        panel.title = "[green]APP备案查询成功"
                    else:
                        raise NotImplementedError
                    live.stop()
                    console.print(panel)
                else:
                    live.update(
                        Panel(
                            Align(
                                "[bold yellow]未查询到该备案",
                                align="center",
                                vertical="middle",
                            ),
                            border_style="yellow",
                            height=5,
                        )
                    )
    elif format == FormatTypeChoice.JSON:
        try:
            results = await query(
                keyword,
                SearchType[search_type.name],
                captcha_max_retry=captcha_max_retry,
            )
        except ICPQueryError:
            sys.stderr.write("ICP查询调用失败")
            sys.exit(-1)
        else:
            sys.stdout.write(results.to_json())
    elif format == FormatTypeChoice.TEXT:
        try:
            results = await query(
                keyword,
                SearchType[search_type.name],
                captcha_max_retry=captcha_max_retry,
            )
        except ICPQueryError:
            sys.stderr.write("ICP查询调用失败")
            sys.exit(-1)
        else:
            sys.stdout.write(results.to_text())


if __name__ == "__main__":
    app()
