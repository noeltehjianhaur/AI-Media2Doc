import hashlib
import html
import json
import re
import unicodedata
import base64
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def sanitize_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.findall(r"[A-Za-z0-9]+", normalized.lower())[:12]
    stem = "-".join(words)[:90].strip("-")
    return stem or "untitled-record"


def _transcript_text(transcript: Any) -> str:
    if isinstance(transcript, list):
        return "\n".join(str(item.get("text", "")) for item in transcript if isinstance(item, dict))
    return str(transcript or "")


def _metadata_lines(metadata: Dict[str, Any]) -> list[str]:
    lines = [f"Created UTC: {metadata['created_at']}", f"Source mode: {metadata['processing_mode']}"]
    if metadata.get("source_type") == "link" and metadata.get("source_url"):
        lines.append(f"Source URL: {metadata['source_url']}")
    elif metadata.get("original_name"):
        lines.append(f"Original file: {metadata['original_name']}")
    for key in ("detected_language", "target_language", "content_style", "model"):
        if metadata.get(key):
            lines.append(f"{key.replace('_', ' ').title()}: {metadata[key]}")
    return lines


def _render_flowchart_svg(edges: list[dict]) -> Optional[str]:
    if not edges:
        return None
    height = max(120, len(edges) * 90 + 30)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}">',
        '<style>text{font:14px sans-serif}.node{fill:#f7f9fc;stroke:#52647a;stroke-width:1.5}.edge{stroke:#52647a;stroke-width:1.5}</style>',
    ]
    for index, edge in enumerate(edges):
        y = 20 + index * 90
        source = html.escape(str(edge.get("source", "")))
        target = html.escape(str(edge.get("target", "")))
        label = html.escape(str(edge.get("label", "")))
        parts.extend(
            [
                f'<rect class="node" x="20" y="{y}" width="250" height="48" rx="4"/>',
                f'<text x="35" y="{y + 29}">{source}</text>',
                f'<line class="edge" x1="270" y1="{y + 24}" x2="445" y2="{y + 24}"/>',
                f'<text x="300" y="{y + 17}">{label}</text>',
                f'<rect class="node" x="445" y="{y}" width="250" height="48" rx="4"/>',
                f'<text x="460" y="{y + 29}">{target}</text>',
            ]
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_html(
    title: str,
    transcript: Any,
    generated_content: str,
    metadata: Dict[str, Any],
    visual_analysis: Dict[str, Any],
    screenshot_paths: list[tuple[str, int]],
) -> tuple[str, Optional[str]]:
    segments = []
    for segment in visual_analysis.get("segments", []):
        start = int(segment.get("start_time", 0)) // 1000
        context = " ".join(
            value
            for value in (
                str(segment.get("text", "")).strip(),
                str(segment.get("on_screen_text", "")).strip(),
                ", ".join(segment.get("visual_actions", [])),
            )
            if value
        )
        segments.append(f"<li><time>{start // 60:02d}:{start % 60:02d}</time> {html.escape(context)}</li>")
    diagram = _render_flowchart_svg(visual_analysis.get("flowchart", []))
    diagram_markup = '<img src="diagram.svg" alt="Process flowchart">' if diagram else ""
    screenshots_markup = "".join(
        f'<figure><img src="{html.escape(path)}" alt="Frame at {timestamp} seconds">'
        f'<figcaption>Frame at {timestamp // 60:02d}:{timestamp % 60:02d}</figcaption></figure>'
        for path, timestamp in screenshot_paths
    )
    meta_rows = "".join(f"<li>{html.escape(line)}</li>" for line in _metadata_lines(metadata))
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>body{{max-width:900px;margin:32px auto;padding:0 20px;font:16px/1.6 sans-serif;color:#182231}}h1,h2{{line-height:1.2}}time{{font-family:monospace;color:#52647a}}img{{max-width:100%}}pre{{white-space:pre-wrap}}</style></head>
<body><h1>{html.escape(title)}</h1><ul>{meta_rows}</ul><h2>Summary</h2><pre>{html.escape(generated_content)}</pre>
<h2>Visual transcript</h2><ol>{''.join(segments)}</ol>{screenshots_markup}{diagram_markup}
<h2>Transcript</h2><pre>{html.escape(_transcript_text(transcript))}</pre></body></html>"""
    return document, diagram


def build_output_bundle(
    title: str,
    processing_mode: str,
    transcript: Any,
    generated_content: str,
    metadata: Dict[str, Any],
    visual_analysis: Optional[Dict[str, Any]] = None,
    screenshots: Optional[list[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    stem = sanitize_title(title)
    mode = getattr(processing_mode, "value", processing_mode)
    complete_metadata = {
        **metadata,
        "created_at": metadata.get("created_at", now.isoformat()),
        "processing_mode": mode,
    }
    files: Dict[str, Any] = {}
    if mode == "audio_video":
        directory = f"records/audio-video/{now:%Y/%m}/{stem}_{timestamp}"
        output_path = f"{directory}/index.html"
        screenshot_paths = []
        for index, screenshot in enumerate(screenshots or [], start=1):
            match = re.fullmatch(
                r"data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)",
                str(screenshot.get("data_url", "")),
            )
            if not match:
                continue
            extension = "jpg" if match.group(1) == "jpeg" else "png"
            image_path = f"{directory}/images/frame-{index:03d}.{extension}"
            files[image_path] = {"content": match.group(2), "encoding": "base64"}
            screenshot_paths.append((f"images/frame-{index:03d}.{extension}", int(screenshot.get("timestamp", 0))))
        document, diagram = _render_html(
            title,
            transcript,
            generated_content,
            complete_metadata,
            visual_analysis or {},
            screenshot_paths,
        )
        files[output_path] = document
        if diagram:
            files[f"{directory}/diagram.svg"] = diagram
        manifest_path = f"{directory}/manifest.json"
    else:
        output_path = f"records/audio/{now:%Y/%m}/{stem}_{timestamp}.md"
        metadata_block = "\n".join(f"- {line}" for line in _metadata_lines(complete_metadata))
        files[output_path] = (
            f"# {title}\n\n{metadata_block}\n\n## Generated content\n\n{generated_content}"
            f"\n\n## Transcript\n\n{_transcript_text(transcript)}\n"
        )
        manifest_path = output_path.removesuffix(".md") + ".manifest.json"
    manifest = {
        "title": title,
        "output_path": output_path,
        "metadata": complete_metadata,
        "files": {},
        "publication_commit_sha": None,
    }
    for path, content in files.items():
        raw = base64.b64decode(content["content"]) if isinstance(content, dict) else content.encode("utf-8")
        manifest["files"][path] = hashlib.sha256(raw).hexdigest()
    files[manifest_path] = json.dumps(manifest, ensure_ascii=True, indent=2)
    return {"title": title, "output_path": output_path, "files": files, "manifest": manifest}