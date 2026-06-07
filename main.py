#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bilibili-sub-md CLI 入口"""

import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from config import DEFAULT_OUTPUT_DIR
from core.downloader import download_one
from core.extractor import (
    extract_bvid,
    extract_page_index,
    has_explicit_page_param,
    is_collection_url,
    extract_collection_info,
)
from core.metadata import fetch_video_meta, fetch_collection_videos, set_cookie
from models import DownloadResult, DownloadTask

app = typer.Typer(add_completion=False)
console = Console()


def _safe_folder_name(name: str) -> str:
    """清理文件夹名称。"""
    bad = '\\/:*?"<>|'
    for ch in bad:
        name = name.replace(ch, "_")
    name = name.strip(" ._")
    if len(name) > 80:
        name = name[:80].rstrip(" ._")
    return name or "untitled"


def _expand_collection(url: str) -> tuple:
    """展开播放列表 URL，返回 (playlist_name, bvids)。"""
    ctype, params = extract_collection_info(url)
    bvids = fetch_collection_videos(ctype, params)

    # 尝试获取播放列表名称
    name = "Bilibili Playlist"
    try:
        # 如果是单个 BV 的多 P，用视频标题作为列表名
        bvid = extract_bvid(url)
        if bvid and not bvids:
            # 可能是多P视频链接，需要单独处理
            meta = fetch_video_meta(bvid)
            if meta.pages and len(meta.pages) > 1:
                return meta.title, [f"https://www.bilibili.com/video/{meta.bvid}?p={p.page}" for p in meta.pages]
            return meta.title, [f"https://www.bilibili.com/video/{meta.bvid}"]
    except Exception:
        pass

    return name, [f"https://www.bilibili.com/video/{bvid}" for bvid in bvids]


def _ask_all_parts(
    bvid: str, title: str, page_count: int, current_page: Optional[int] = None
) -> bool:
    """交互式询问是否下载全部分 P。

    current_page: 用户链接中显式指定的分 P。为 None 时表示未指定，默认只下 P1。
    """
    console.print(
        f"[cyan]?[/cyan] 视频 [bold]{title}[/bold]（{bvid}）共有 [bold]{page_count}[/bold] 个分 P。"
    )
    if current_page is not None:
        console.print(f"  [A] 只下载第 {current_page} P（当前链接指定）")
    else:
        console.print("  [A] 只下载第 1 P（默认）")
    console.print(f"  [B] 下载全部 {page_count} 个分 P，保存到 '{_safe_folder_name(title)}/' 文件夹")
    try:
        choice = input("请选择 [A/B]: ").strip().upper()
    except EOFError:
        choice = "A"
    return choice == "B"


def _collect_tasks(
    raw_urls: List[str],
    base_output: Path,
    all_parts: bool = False,
) -> List[DownloadTask]:
    """收集所有下载任务，自动识别播放列表和多 P 视频。"""
    tasks: List[DownloadTask] = []
    seen = set()

    for raw in raw_urls:
        raw = raw.strip()
        if not raw:
            continue

        if is_collection_url(raw):
            try:
                playlist_name, urls = _expand_collection(raw)
                folder_name = _safe_folder_name(playlist_name)
                playlist_output = base_output / folder_name
                console.print(
                    f"[blue]info[/blue] 播放列表 '{playlist_name}' -> {len(urls)} 个视频 -> 文件夹 '{folder_name}/'"
                )
                for u in urls:
                    bvid = extract_bvid(u)
                    key = (bvid, str(playlist_output))
                    if key not in seen:
                        seen.add(key)
                        tasks.append(DownloadTask(url=u, output_dir=playlist_output))
            except Exception as e:
                console.print(f"[yellow]warn[/yellow] 播放列表展开失败: {raw} — {e}")
            continue

        # 单个视频链接
        bvid = extract_bvid(raw)
        if not bvid:
            console.print(f"[yellow]warn[/yellow] 跳过无效链接: {raw}")
            continue

        try:
            meta = fetch_video_meta(bvid)
        except Exception as e:
            console.print(f"[yellow]warn[/yellow] 无法获取视频信息: {raw} — {e}")
            continue

        # 多 P 视频：询问或按 --all-parts 参数决定
        if meta.pages and len(meta.pages) > 1:
            page_count = len(meta.pages)
            current_page = extract_page_index(raw) if has_explicit_page_param(raw) else None
            should_download_all = all_parts
            if not should_download_all and sys.stdin.isatty():
                should_download_all = _ask_all_parts(bvid, meta.title, page_count, current_page)

            if should_download_all:
                folder_name = _safe_folder_name(meta.title)
                parts_output = base_output / folder_name
                console.print(
                    f"[blue]info[/blue] 多 P 视频 '{meta.title}' -> {page_count} 个分 P -> 文件夹 '{folder_name}/'"
                )
                for page in meta.pages:
                    page_url = f"https://www.bilibili.com/video/{meta.bvid}?p={page.page}"
                    key = (f"{meta.bvid}_p{page.page}", str(parts_output))
                    if key not in seen:
                        seen.add(key)
                        tasks.append(DownloadTask(url=page_url, output_dir=parts_output))
            else:
                # 只下载指定的 P（显式 ?p=N）或 P1（未指定）
                target_page = current_page if current_page is not None else 1
                target_url = raw if has_explicit_page_param(raw) else f"https://www.bilibili.com/video/{meta.bvid}"
                key = (f"{meta.bvid}_p{target_page}", str(base_output))
                if key not in seen:
                    seen.add(key)
                    tasks.append(DownloadTask(url=target_url, output_dir=base_output))
        else:
            # 单 P 视频
            key = (bvid, str(base_output))
            if key not in seen:
                seen.add(key)
                tasks.append(DownloadTask(url=raw, output_dir=base_output))

    return tasks


def _prompt_links() -> List[str]:
    """交互式多行链接输入。"""
    console.print("请输入 Bilibili 视频或播放列表链接（每行一个，空行结束，输入 exit 退出）：")
    lines = []
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            break
        if line.lower() in ("exit", "quit", "q"):
            return ["__EXIT__"]
        lines.extend(line.replace(",", "\n").split("\n"))
    return [l.strip() for l in lines if l.strip()]


def _download_with_delay(
    task: DownloadTask,
    fmt: str,
    preferred_lang: Optional[str],
) -> DownloadResult:
    """带随机延迟的下载任务。"""
    time.sleep(random.uniform(1.0, 2.5))
    return download_one(
        task.url,
        task.output_dir,
        fmt,
        preferred_lang,
    )


@app.command()
def download(
    urls: Optional[List[str]] = typer.Argument(None, help="一个或多个 Bilibili URL"),
    output: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output", "-o", help="输出目录"),
    fmt: str = typer.Option("md", "--format", "-f", help="输出格式: md / srt / txt"),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="首选字幕语言代码，如 zh-CN / en"),
    max_workers: int = typer.Option(3, "--workers", "-w", help="并发数"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="交互模式输入链接"),
    cookie: Optional[str] = typer.Option(None, "--cookie", "-c", help="Bilibili Cookie 中的 SESSDATA 值（用于获取需要登录的字幕）"),
    all_parts: bool = typer.Option(False, "--all-parts", "-a", help="自动下载多 P 视频的全部分 P，保存到以视频标题命名的文件夹"),
):
    """批量下载 Bilibili 视频字幕。"""
    # 设置全局 Cookie：优先命令行参数，其次环境变量
    effective_cookie = cookie or os.environ.get("BILI_COOKIE") or os.environ.get("BILIBILI_SESSDATA")
    if effective_cookie:
        raw_len = len(effective_cookie)
        set_cookie(effective_cookie)
        from core.metadata import _global_cookie
        clean_len = len(_global_cookie)
        if clean_len == 0:
            console.print("[red]警告: Cookie 过滤后为空，字幕可能无法获取[/red]")
        elif clean_len < raw_len * 0.8:
            console.print(f"[yellow]警告: Cookie 过滤后长度从 {raw_len} 变为 {clean_len}，部分字符被移除[/yellow]")
        else:
            console.print(f"[dim]已设置登录 Cookie (原始 {raw_len} 字符, 有效 {clean_len} 字符)[/dim]")
    else:
        console.print("[dim]提示：如需下载登录后才能看到的字幕，请用 --cookie 参数或 BILI_COOKIE 环境变量传入 SESSDATA[/dim]")

    console.print("[bold cyan]bilibili-sub-md[/bold cyan] — 批量字幕下载工具\n")

    def _run_once(raw_urls: List[str]) -> bool:
        """执行一次下载批次，返回是否有失败。"""
        if not raw_urls:
            console.print("[yellow]没有可处理的链接[/yellow]")
            return False

        tasks = _collect_tasks(raw_urls, output, all_parts=all_parts)
        if not tasks:
            console.print("[yellow]没有可下载的任务[/yellow]")
            return False

        console.print(f"\n共 {len(tasks)} 个下载任务，输出格式: {fmt}")

        results: List[DownloadResult] = []
        with Progress(console=console) as progress:
            task_id = progress.add_task("[cyan]下载中...", total=len(tasks))

            def run(task: DownloadTask) -> DownloadResult:
                result = _download_with_delay(task, fmt, lang)
                progress.advance(task_id)
                return result

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(run, t): t for t in tasks}
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        task = futures[future]
                        results.append(
                            DownloadResult(
                                bvid=extract_bvid(task.url) or "",
                                cid="",
                                status="failed",
                                error=f"线程异常: {e}",
                            )
                        )

        # 结果表格
        table = Table(title="下载结果")
        table.add_column("BV 号", style="cyan")
        table.add_column("标题", style="green")
        table.add_column("状态", style="bold")
        table.add_column("语言")
        table.add_column("文件路径")

        success = skipped = failed = 0
        for r in results:
            if r.status == "success":
                success += 1
                status_text = f"[green]{r.status}[/green]"
            elif r.status == "skipped":
                skipped += 1
                status_text = f"[yellow]{r.status}[/yellow]"
            else:
                failed += 1
                status_text = f"[red]{r.status}[/red]"

            path_text = str(r.filepath) if r.filepath else "-"
            if r.error:
                path_text = f"{path_text}\n[yellow]{r.error}[/yellow]"

            table.add_row(r.bvid, r.title or "-", status_text, r.language or "-", path_text)

        console.print(table)
        console.print(
            f"\n[bold]汇总:[/bold] 成功 {success} | 跳过 {skipped} | 失败 {failed} | 总计 {len(results)}"
        )
        console.print("─" * 60)
        return failed == 0

    if urls:
        # 命令行传入 URL，保持单次执行后退出
        ok = _run_once(urls)
        if not ok:
            raise typer.Exit(1)
    else:
        # 交互模式：循环输入，直到用户输入 exit 或关闭窗口
        while True:
            raw_urls = _prompt_links()
            if raw_urls == ["__EXIT__"]:
                console.print("[dim]已退出交互模式，再见 👋[/dim]")
                break
            _run_once(raw_urls)


if __name__ == "__main__":
    app()
