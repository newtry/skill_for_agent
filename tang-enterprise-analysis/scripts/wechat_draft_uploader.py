#!/usr/bin/env python3
"""Upload a Markdown article to WeChat Official Account draft box.

Required .env values:
  WECHAT_APPID=...
  WECHAT_APPSECRET=...

Cover image:
  Either pass --cover-image path/to/wechat-cover.png to upload it as permanent thumb
  material, set WECHAT_THUMB_MEDIA_ID=... in .env, or let the script generate a
  title-aware cover automatically.
"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - handled at runtime with a clear error
    Image = None
    ImageDraw = None
    ImageFont = None


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
ADD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
ADD_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
UPDATE_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/update"
COVER_WIDTH = 900
COVER_HEIGHT = 383


class WeChatError(RuntimeError):
    pass


def find_env_files(start: Path) -> List[Path]:
    candidates = [
        start / ".env",
        start.parent / ".env",
        start.parent.parent / ".env",
        Path.cwd() / ".env",
    ]
    seen = set()
    result = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen and resolved.exists():
            seen.add(resolved)
            result.append(resolved)
    return result


def load_dotenv(paths: Iterable[Path]) -> None:
    for path in paths:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise WeChatError(f"Missing required environment variable: {name}")
    return value


def wx_get(url: str, params: Dict[str, str]) -> Dict:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("errcode"):
        raise WeChatError(f"WeChat API error {data.get('errcode')}: {data.get('errmsg')}")
    return data


def wx_post_json(url: str, params: Dict[str, str], payload: Dict) -> Dict:
    response = requests.post(
        url,
        params=params,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode"):
        raise WeChatError(f"WeChat API error {data.get('errcode')}: {data.get('errmsg')}")
    return data


def get_access_token(appid: str, appsecret: str) -> str:
    data = wx_get(
        TOKEN_URL,
        {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": appsecret,
        },
    )
    token = data.get("access_token")
    if not token:
        raise WeChatError("WeChat token response did not include access_token")
    return token


def upload_thumb_material(access_token: str, image_path: Path) -> str:
    if not image_path.exists():
        raise WeChatError(f"Cover image does not exist: {image_path}")

    content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    with image_path.open("rb") as image_file:
        files = {"media": (image_path.name, image_file, content_type)}
        response = requests.post(
            ADD_MATERIAL_URL,
            params={"access_token": access_token, "type": "thumb"},
            files=files,
            timeout=60,
        )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode"):
        raise WeChatError(f"WeChat API error {data.get('errcode')}: {data.get('errmsg')}")
    media_id = data.get("media_id")
    if not media_id:
        raise WeChatError("WeChat material response did not include media_id")
    return media_id


def split_table_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def render_table(lines: List[str]) -> str:
    rows = [split_table_row(line) for line in lines]
    if len(rows) >= 2 and is_separator_row(lines[1]):
        headers = rows[0]
        body_rows = rows[2:]
    else:
        headers = []
        body_rows = rows

    parts = [
        '<table style="border-collapse:collapse;width:100%;font-size:14px;line-height:1.7;">'
    ]
    if headers:
        parts.append("<thead><tr>")
        for cell in headers:
            parts.append(
                '<th style="border:1px solid #ddd;padding:6px;background:#f7f7f7;">'
                + inline_markdown(cell)
                + "</th>"
            )
        parts.append("</tr></thead>")

    parts.append("<tbody>")
    for row in body_rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(
                '<td style="border:1px solid #ddd;padding:6px;vertical-align:top;">'
                + inline_markdown(cell)
                + "</td>"
            )
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((https?://.+?)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def fallback_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    parts: List[str] = []
    paragraph: List[str] = []
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(item.strip() for item in paragraph if item.strip())
            parts.append(f"<p>{inline_markdown(text)}</p>")
            paragraph.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            parts.append(render_table(table_lines))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 3)
            text = inline_markdown(heading.group(2))
            parts.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            parts.append("<ul>" + "".join(f"<li>{inline_markdown(item)}</li>" for item in items) + "</ul>")
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return "\n".join(parts)


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown  # type: ignore

        return markdown.markdown(
            markdown_text,
            extensions=["extra", "tables", "sane_lists"],
            output_format="html5",
        )
    except Exception:
        return fallback_markdown_to_html(markdown_text)


def prepare_markdown_for_wechat(markdown_text: str) -> str:
    """Remove metadata that the Official Account editor renders separately."""
    lines = markdown_text.splitlines()
    prepared: List[str] = []
    title_removed = False

    for line in lines:
        stripped = line.strip()
        if not title_removed and re.match(r"^#\s+\S", stripped):
            title_removed = True
            continue
        if re.match(r"^>\s*系列导航：\[[^]]+\]\([^)]+\.md(?:#[^)]*)?\)\s*$", stripped):
            continue
        prepared.append(line)

    return "\n".join(prepared).strip()


def style_wechat_article_html(body_html: str) -> str:
    """Apply inline styles that survive pasting into the WeChat editor."""
    replacements = {
        "p": (
            '<p style="margin:0 0 20px;font-size:16px;line-height:1.9;'
            'color:#263238;text-align:justify;">'
        ),
        "h1": (
            '<h1 style="margin:34px 0 18px;font-size:23px;line-height:1.45;'
            'font-weight:700;color:#173f3c;">'
        ),
        "h2": (
            '<h2 style="margin:38px 0 18px;padding-left:12px;border-left:4px solid #176b65;'
            'font-size:20px;line-height:1.5;font-weight:700;color:#173f3c;">'
        ),
        "h3": (
            '<h3 style="margin:30px 0 14px;font-size:18px;line-height:1.55;'
            'font-weight:700;color:#263238;">'
        ),
        "ul": '<ul style="margin:0 0 22px;padding-left:1.4em;color:#263238;">',
        "ol": '<ol style="margin:0 0 22px;padding-left:1.4em;color:#263238;">',
        "li": '<li style="margin:8px 0;font-size:16px;line-height:1.8;">',
        "blockquote": (
            '<blockquote style="margin:24px 0;padding:14px 18px;border-left:4px solid #d35b3f;'
            'background:#f5f7f5;color:#465457;">'
        ),
        "pre": (
            '<pre style="margin:22px 0;padding:16px 18px;border:1px solid #dce5e2;'
            'border-radius:6px;background:#f5f7f6;white-space:pre-wrap;word-break:break-word;'
            'overflow-wrap:anywhere;font-size:13px;line-height:1.75;color:#263238;">'
        ),
        "table": (
            '<table style="margin:22px 0;border-collapse:collapse;width:100%;'
            'font-size:14px;line-height:1.7;color:#263238;">'
        ),
        "th": (
            '<th style="border:1px solid #d8e2df;padding:8px;background:#edf3f1;'
            'font-weight:700;text-align:left;">'
        ),
        "td": '<td style="border:1px solid #d8e2df;padding:8px;vertical-align:top;">',
    }
    styled = body_html
    for tag, replacement in replacements.items():
        styled = re.sub(rf"<{tag}(?:\s[^>]*)?>", replacement, styled, flags=re.IGNORECASE)

    styled = re.sub(
        r"<a(?:\s[^>]*)?href=([\"'])(https?://[^\"']+)\1(?:\s[^>]*)?>",
        r'<a href="\2" style="color:#176b65;text-decoration:underline;">',
        styled,
        flags=re.IGNORECASE,
    )
    styled = re.sub(
        r"<code(?:\s[^>]*)?>",
        '<code style="font-family:Consolas,Menlo,monospace;font-size:0.92em;color:#9c3f2d;">',
        styled,
        flags=re.IGNORECASE,
    )
    styled = re.sub(
        r"<strong(?:\s[^>]*)?>",
        '<strong style="font-weight:700;color:#173f3c;">',
        styled,
        flags=re.IGNORECASE,
    )
    return styled


def wrap_wechat_article_html(body_html: str) -> str:
    return f"""
<section style="font-size:16px;line-height:1.9;color:#263238;letter-spacing:0;">
{style_wechat_article_html(body_html)}
</section>
""".strip()


def load_font(size: int, bold: bool = False):
    if ImageFont is None:
        raise WeChatError("Pillow is required for auto cover generation. Install dependency: pillow")

    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def text_width(draw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def fit_font(draw, text: str, max_width: int, size: int, min_size: int, bold: bool = False):
    while size > min_size:
        font = load_font(size, bold=bold)
        if text_width(draw, text, font) <= max_width:
            return font
        size -= 2
    return load_font(min_size, bold=bold)


def wrap_cjk_text(draw, text: str, font, max_width: int, max_lines: int) -> List[str]:
    cleaned = re.sub(r"\s+", "", text.strip())
    if not cleaned:
        return []

    lines: List[str] = []
    current = ""
    for char in cleaned:
        candidate = current + char
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) >= max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and len("".join(lines)) < len(cleaned):
        line = lines[-1]
        while line and text_width(draw, line + "...", font) > max_width:
            line = line[:-1]
        lines[-1] = line + "..."
    return lines


def infer_cover_company(title: str) -> str:
    company = re.sub(r"[：:｜|].*$", "", title).strip()
    company = re.sub(r"(投资分析报告|企业分析报告|分析报告|深度分析|投资分析)$", "", company).strip()
    return company or title.strip() or "企业分析"


def build_cover_subtitle(digest: str) -> str:
    cleaned = re.sub(r"\s+", "", digest.strip())
    if not cleaned:
        return "业务模式 · 资产质量 · 管理层 · 估值"

    phrases = []
    if "现金流" in cleaned:
        phrases.append("现金流")
    if "资产" in cleaned or "应收" in cleaned:
        phrases.append("资产质量")
    if "管理层" in cleaned or "资本配置" in cleaned:
        phrases.append("管理层")
    if "估值" in cleaned or "内在价值" in cleaned or "安全边际" in cleaned:
        phrases.append("估值")
    if len(phrases) >= 2:
        return " · ".join(dict.fromkeys(phrases[:4]))
    return "业务模式 · 资产质量 · 管理层 · 估值"


def generate_cover_image(title: str, digest: str, output_path: Path) -> Path:
    if Image is None or ImageDraw is None:
        raise WeChatError("Pillow is required for auto cover generation. Install dependency: pillow")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), "#f7f8f5")
    draw = ImageDraw.Draw(image)

    # Restrained finance-style cover: clear title, light data motif, strong thumbnail contrast.
    for x in range(COVER_WIDTH):
        ratio = x / COVER_WIDTH
        r = int(247 - ratio * 18)
        g = int(248 - ratio * 20)
        b = int(245 - ratio * 12)
        draw.line([(x, 0), (x, COVER_HEIGHT)], fill=(r, g, b))

    draw.rectangle((0, 0, COVER_WIDTH, 8), fill="#1f5f6f")
    draw.rectangle((0, COVER_HEIGHT - 10, COVER_WIDTH, COVER_HEIGHT), fill="#b84a3a")

    for i, height in enumerate([48, 78, 54, 108, 86, 126, 96]):
        x0 = 604 + i * 35
        draw.rounded_rectangle(
            (x0, 250 - height, x0 + 18, 250),
            radius=5,
            fill="#d8e3df",
            outline="#b9cbc6",
        )

    points = [(600, 270), (646, 238), (690, 252), (734, 202), (778, 216), (824, 164)]
    draw.line(points, fill="#1f5f6f", width=5)
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#b84a3a")

    label_font = load_font(24)
    title_font = fit_font(draw, infer_cover_company(title), 470, 60, 40, bold=True)
    report_font = load_font(34, bold=True)
    subtitle_font = load_font(24)
    digest_font = load_font(20)

    company = infer_cover_company(title)
    subtitle = build_cover_subtitle(digest)
    digest_lines = wrap_cjk_text(draw, digest, digest_font, 500, 2)

    draw.text((56, 60), "企业投资分析", font=label_font, fill="#1f5f6f")
    draw.rectangle((56, 98, 150, 103), fill="#b84a3a")
    draw.text((56, 126), company, font=title_font, fill="#172026")
    draw.text((56, 204), "投资分析报告", font=report_font, fill="#172026")
    draw.text((56, 254), subtitle, font=subtitle_font, fill="#38545a")

    y = 302
    for line in digest_lines:
        draw.text((56, y), line, font=digest_font, fill="#606a6d")
        y += 28

    image.save(output_path, "PNG", optimize=True)
    return output_path


def is_metadata_or_disclaimer(line: str) -> bool:
    return (
        line.startswith("数据口径")
        or line.startswith("资料来源")
        or "不是投资建议" in line
        or "不构成投资建议" in line
    )


def extract_title_and_digest(markdown_text: str, title_arg: Optional[str], digest_arg: Optional[str]) -> Tuple[str, str]:
    title = title_arg
    if not title:
        match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
        title = match.group(1).strip() if match else "未命名文章"

    if digest_arg:
        digest = digest_arg.strip()
    else:
        plain_lines = []
        for line in markdown_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("- "):
                continue
            if is_metadata_or_disclaimer(stripped):
                continue
            plain_lines.append(re.sub(r"[*_`>\[\]()]|https?://\S+", "", stripped))
            if len("".join(plain_lines)) >= 120:
                break
        digest = "".join(plain_lines)[:120]

    return title[:64], digest[:120]


def create_draft(
    access_token: str,
    title: str,
    author: str,
    digest: str,
    content_html: str,
    thumb_media_id: str,
    source_url: str,
    need_open_comment: int,
    only_fans_can_comment: int,
) -> str:
    payload = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content_html,
                "content_source_url": source_url,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": need_open_comment,
                "only_fans_can_comment": only_fans_can_comment,
            }
        ]
    }
    data = wx_post_json(ADD_DRAFT_URL, {"access_token": access_token}, payload)
    media_id = data.get("media_id")
    if not media_id:
        raise WeChatError("WeChat draft response did not include media_id")
    return media_id


def update_draft(
    access_token: str,
    media_id: str,
    title: str,
    author: str,
    digest: str,
    content_html: str,
    thumb_media_id: str,
    source_url: str,
    need_open_comment: int,
    only_fans_can_comment: int,
) -> None:
    payload = {
        "media_id": media_id,
        "index": 0,
        "articles": {
            "title": title,
            "author": author,
            "digest": digest,
            "content": content_html,
            "content_source_url": source_url,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": need_open_comment,
            "only_fans_can_comment": only_fans_can_comment,
        },
    }
    wx_post_json(UPDATE_DRAFT_URL, {"access_token": access_token}, payload)


def build_parser() -> argparse.ArgumentParser:
    default_article = (
        Path(__file__).resolve().parents[2]
        / "tang-enterprise-analysis-workspace"
        / "focus-media-analysis-report.md"
    )
    parser = argparse.ArgumentParser(description="Upload Markdown article to WeChat draft box.")
    parser.add_argument("--article", type=Path, default=default_article, help="Markdown article path.")
    parser.add_argument("--env-file", type=Path, action="append", help="Optional .env file path.")
    parser.add_argument("--title", help="Draft title. Defaults to first H1 in Markdown.")
    parser.add_argument("--author", default=os.environ.get("WECHAT_AUTHOR", ""), help="Article author.")
    parser.add_argument("--digest", help="Article digest. Defaults to first paragraph.")
    parser.add_argument("--source-url", default="", help="Original article URL.")
    parser.add_argument("--cover-image", type=Path, help="Cover image to upload as permanent thumb material.")
    parser.add_argument("--cover-output", type=Path, help="Where to write the generated cover image.")
    parser.add_argument(
        "--no-auto-cover",
        action="store_true",
        help="Disable automatic cover generation when no cover image or thumb media id is provided.",
    )
    parser.add_argument("--thumb-media-id", help="Existing cover thumb media_id.")
    parser.add_argument("--draft-media-id", help="Update article index 0 in an existing draft.")
    parser.add_argument("--open-comment", action="store_true", help="Enable comments.")
    parser.add_argument("--fans-only-comment", action="store_true", help="Only fans can comment.")
    parser.add_argument("--dry-run", action="store_true", help="Render HTML and show metadata without uploading.")
    parser.add_argument("--output-html", type=Path, help="Write rendered HTML to this file.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    env_files = args.env_file or find_env_files(script_dir)
    load_dotenv(env_files)

    article_path = args.article.resolve()
    if not article_path.exists():
        raise WeChatError(f"Article does not exist: {article_path}")

    markdown_text = article_path.read_text(encoding="utf-8")
    title, digest = extract_title_and_digest(markdown_text, args.title, args.digest)
    body_html = markdown_to_html(prepare_markdown_for_wechat(markdown_text))
    content_html = wrap_wechat_article_html(body_html)
    env_thumb_media_id = os.environ.get("WECHAT_THUMB_MEDIA_ID", "").strip()
    thumb_media_id = args.thumb_media_id or (env_thumb_media_id if args.no_auto_cover else "")
    generated_cover_path: Optional[Path] = None

    if not args.cover_image and not thumb_media_id and not args.no_auto_cover:
        cover_output = args.cover_output or article_path.with_name(f"{article_path.stem}-wechat-cover.png")
        generated_cover_path = generate_cover_image(title, digest, cover_output.resolve())
        args.cover_image = generated_cover_path

    if args.output_html:
        args.output_html.parent.mkdir(parents=True, exist_ok=True)
        args.output_html.write_text(content_html, encoding="utf-8")

    if args.dry_run:
        print("Dry run OK")
        print(f"article: {article_path}")
        print(f"title: {title}")
        print(f"digest: {digest}")
        if generated_cover_path:
            print(f"cover: {generated_cover_path}")
        if args.output_html:
            print(f"html: {args.output_html.resolve()}")
        return 0

    appid = require_env("WECHAT_APPID")
    appsecret = require_env("WECHAT_APPSECRET")
    access_token = get_access_token(appid, appsecret)

    if args.cover_image:
        thumb_media_id = upload_thumb_material(access_token, args.cover_image.resolve())
        print(f"Uploaded cover thumb_media_id: {thumb_media_id}")
    if not thumb_media_id:
        raise WeChatError("Provide --cover-image, --thumb-media-id, WECHAT_THUMB_MEDIA_ID in .env, or enable auto cover generation")

    article_args = {
        "access_token": access_token,
        "title": title,
        "author": args.author,
        "digest": digest,
        "content_html": content_html,
        "thumb_media_id": thumb_media_id,
        "source_url": args.source_url,
        "need_open_comment": 1 if args.open_comment else 0,
        "only_fans_can_comment": 1 if args.fans_only_comment else 0,
    }
    if args.draft_media_id:
        update_draft(media_id=args.draft_media_id, **article_args)
        print(f"Draft updated. media_id: {args.draft_media_id}")
    else:
        media_id = create_draft(**article_args)
        print(f"Draft created. media_id: {media_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WeChatError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
