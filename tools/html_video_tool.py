#!/usr/bin/env python3
"""
html-video tool — wrap the html-video CLI for video generation.

Wraps `D:\VIdeo_ AI\html-video\packages\cli\dist\bin.js` to expose
project management and rendering as Hermes tools.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)

HTML_VIDEO_CLI = r"D:\VIdeo_ AI\html-video\packages\cli\dist\bin.js"
HTML_VIDEO_ROOT = "D:/VIeo_ AI/html-video"


def _check_html_video() -> bool:
    """Check if html-video CLI is available."""
    try:
        result = subprocess.run(
            ["node", HTML_VIDEO_CLI, "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        data = json.loads(result.stdout)
        return data.get("status") == "ok"
    except Exception:
        return False


def _run_cli(args: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Dict[str, Any]:
    """Run html-video CLI and return parsed JSON result."""
    cmd = ["node", HTML_VIDEO_CLI] + args
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or HTML_VIDEO_ROOT,
        )
        output = proc.stdout.strip()
        if not output:
            return {"error": f"CLI exited with code {proc.returncode}, no output"}
        # Parse JSON output
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"raw_output": output, "exit_code": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"error": f"CLI timed out after {timeout}s"}
    except FileNotFoundError:
        return {"error": f"Node.js not found, tried: {HTML_VIDEO_CLI}"}
    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------------------------------
# Tool schemas
# -------------------------------------------------------------------------

HTML_VIDEO_DOCTOR_SCHEMA: Dict[str, Any] = {
    "name": "html_video_doctor",
    "description": "Diagnose html-video installation and environment.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

HTML_VIDEO_LIST_ENGINES_SCHEMA: Dict[str, Any] = {
    "name": "html_video_list_engines",
    "description": "List installed html-video engine adapters (remotion, hyperframes).",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

HTML_VIDEO_SEARCH_TEMPLATES_SCHEMA: Dict[str, Any] = {
    "name": "html_video_search_templates",
    "description": (
        "Search html-video templates by intent. "
        "Returns matching templates with IDs usable in project-set-template."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "Free-text description of desired video style.",
            },
            "aspect": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "description": "Aspect ratio filter.",
            },
            "top": {
                "type": "integer",
                "description": "Number of results to return.",
                "default": 5,
            },
        },
    },
}

HTML_VIDEO_INSPECT_TEMPLATE_SCHEMA: Dict[str, Any] = {
    "name": "html_video_inspect_template",
    "description": "Show full metadata for a template by ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "Template ID (e.g. 'frame-vignelli').",
            },
        },
        "required": ["template_id"],
    },
}

HTML_VIDEO_PROJECT_CREATE_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_create",
    "description": (
        "Create a new html-video project. Returns project_id usable in subsequent commands."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Project name.",
            },
            "intent": {
                "type": "string",
                "description": "One-sentence description of the video.",
            },
            "aspect": {
                "type": "string",
                "enum": ["16:9", "9:16", "1:1"],
                "description": "Aspect ratio (default 16:9).",
            },
        },
        "required": ["name"],
    },
}

HTML_VIDEO_PROJECT_LIST_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_list",
    "description": "List all html-video projects.",
    "parameters": {"type": "object", "properties": {}},
}

HTML_VIDEO_PROJECT_SHOW_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_show",
    "description": "Show details of a project by ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Project ID (e.g. 'proj_xxx').",
            },
        },
        "required": ["project_id"],
    },
}

HTML_VIDEO_PROJECT_DELETE_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_delete",
    "description": "Delete a project by ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Project ID to delete.",
            },
        },
        "required": ["project_id"],
    },
}

HTML_VIDEO_PROJECT_SET_TEMPLATE_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_set_template",
    "description": "Assign a template to a project.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Project ID.",
            },
            "template_id": {
                "type": "string",
                "description": "Template ID (e.g. 'frame-vignelli').",
            },
        },
        "required": ["project_id", "template_id"],
    },
}

HTML_VIDEO_PROJECT_ADD_ASSET_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_add_asset",
    "description": (
        "Add an asset (image/video/audio file) to a project. "
        "Paths are relative to the html-video project root."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Project ID.",
            },
            "file": {
                "type": "string",
                "description": "Path to file (image/video/audio/data).",
            },
            "inline_text": {
                "type": "string",
                "description": "Inline text content instead of a file.",
            },
            "caption": {
                "type": "string",
                "description": "Optional caption for the asset.",
            },
        },
        "required": ["project_id"],
    },
}

HTML_VIDEO_PROJECT_RENDER_SCHEMA: Dict[str, Any] = {
    "name": "html_video_project_render",
    "description": (
        "Render a project to MP4. Runs foreground — returns when complete. "
        "Output path defaults to html-video root/output/<project_id>.mp4."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Project ID to render.",
            },
            "output": {
                "type": "string",
                "description": "Output MP4 path (optional).",
            },
        },
        "required": ["project_id"],
    },
}


# -------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------

def html_video_doctor(task_id: str = None) -> str:
    result = _run_cli(["doctor", "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_list_engines(task_id: str = None) -> str:
    result = _run_cli(["list-engines", "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_search_templates(intent: str = "", aspect: str = "16:9", top: int = 5, task_id: str = None) -> str:
    args = ["search-templates", "--aspect", aspect, "--top", str(top), "--json"]
    if intent:
        args += ["--intent", intent]
    result = _run_cli(args)
    return json.dumps(result, ensure_ascii=False)


def html_video_inspect_template(template_id: str, task_id: str = None) -> str:
    result = _run_cli(["inspect-template", template_id, "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_project_create(name: str, intent: str = "", aspect: str = "16:9", task_id: str = None) -> str:
    args = ["project-create", "--name", name, "--aspect", aspect, "--json"]
    if intent:
        args += ["--intent", intent]
    result = _run_cli(args)
    return json.dumps(result, ensure_ascii=False)


def html_video_project_list(task_id: str = None) -> str:
    result = _run_cli(["project-list", "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_project_show(project_id: str, task_id: str = None) -> str:
    result = _run_cli(["project-show", project_id, "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_project_delete(project_id: str, task_id: str = None) -> str:
    result = _run_cli(["project-delete", project_id, "--json"])
    return json.dumps(result, ensure_ascii=False)


def html_video_project_set_template(project_id: str, template_id: str, task_id: str = None) -> str:
    result = _run_cli([
        "project-set-template", project_id,
        "--template", template_id,
        "--json",
    ])
    return json.dumps(result, ensure_ascii=False)


def html_video_project_add_asset(
    project_id: str,
    file: str = "",
    inline_text: str = "",
    caption: str = "",
    task_id: str = None,
) -> str:
    args = ["project-add-asset", project_id, "--json"]
    if file:
        args += ["--file", file]
    if inline_text:
        args += ["--inline-text", inline_text]
    if caption:
        args += ["--caption", caption]
    result = _run_cli(args)
    return json.dumps(result, ensure_ascii=False)


def html_video_project_render(project_id: str, output: str = "", task_id: str = None) -> str:
    args = ["project-render", project_id, "--json"]
    if output:
        args += ["--output", output]
    # Run foreground with longer timeout for rendering
    result = _run_cli(args, timeout=600)
    return json.dumps(result, ensure_ascii=False)


# -------------------------------------------------------------------------
# Registry
# -------------------------------------------------------------------------

registry.register(
    name="html_video_doctor",
    toolset="video",
    schema=HTML_VIDEO_DOCTOR_SCHEMA,
    handler=lambda args, **kw: html_video_doctor(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_list_engines",
    toolset="video",
    schema=HTML_VIDEO_LIST_ENGINES_SCHEMA,
    handler=lambda args, **kw: html_video_list_engines(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_search_templates",
    toolset="video",
    schema=HTML_VIDEO_SEARCH_TEMPLATES_SCHEMA,
    handler=lambda args, **kw: html_video_search_templates(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_inspect_template",
    toolset="video",
    schema=HTML_VIDEO_INSPECT_TEMPLATE_SCHEMA,
    handler=lambda args, **kw: html_video_inspect_template(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_create",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_CREATE_SCHEMA,
    handler=lambda args, **kw: html_video_project_create(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_list",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_LIST_SCHEMA,
    handler=lambda args, **kw: html_video_project_list(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_show",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_SHOW_SCHEMA,
    handler=lambda args, **kw: html_video_project_show(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_delete",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_DELETE_SCHEMA,
    handler=lambda args, **kw: html_video_project_delete(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_set_template",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_SET_TEMPLATE_SCHEMA,
    handler=lambda args, **kw: html_video_project_set_template(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_add_asset",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_ADD_ASSET_SCHEMA,
    handler=lambda args, **kw: html_video_project_add_asset(**args),
    check_fn=_check_html_video,
    requires_env=[],
)

registry.register(
    name="html_video_project_render",
    toolset="video",
    schema=HTML_VIDEO_PROJECT_RENDER_SCHEMA,
    handler=lambda args, **kw: html_video_project_render(**args),
    check_fn=_check_html_video,
    requires_env=[],
)
