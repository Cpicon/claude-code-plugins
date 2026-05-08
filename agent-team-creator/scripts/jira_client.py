#!/usr/bin/env python3
"""Jira REST API client for Claude Code plugin fallback.

Zero external dependencies — uses only Python 3 stdlib.
Credentials read from config file (never CLI args).
Output: JSON on stdout. Errors: human-readable on stderr.
Exit codes: 0=success, 1=auth, 2=validation, 3=network, 4=jira-api.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# --- Config ---

def read_config(path):
    """Read and validate credential config file."""
    try:
        with open(path) as f:
            config = json.load(f)
    except FileNotFoundError:
        error_exit(f"Config file not found: {path}", 2)
    except json.JSONDecodeError as e:
        error_exit(f"Invalid JSON in config: {e}", 2)

    for field in ("baseUrl", "email", "apiToken"):
        if field not in config or not config[field]:
            error_exit(f"Missing required config field: {field}", 2)

    # Normalize baseUrl — strip trailing slash
    config["baseUrl"] = config["baseUrl"].rstrip("/")
    return config


# --- HTTP ---

def _build_authed_request(config, method, path, body):
    """Build an authenticated urllib.Request (no I/O)."""
    url = f"{config['baseUrl']}{path}"
    credentials = f"{config['email']}:{config['apiToken']}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    return urllib.request.Request(url, data=data, headers=headers, method=method)


def make_request(config, method, path, body=None, timeout=15):
    """Execute an authenticated HTTP request to Jira REST API.

    Returns parsed JSON response.
    Calls error_exit() on HTTP errors (auth, network, server, jira-api).
    """
    req = _build_authed_request(config, method, path, body)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        handle_http_error(e)
    except urllib.error.URLError as e:
        if "timed out" in str(e.reason):
            error_exit("Request timed out", 3)
        error_exit(f"Cannot reach {config['baseUrl']}: {e.reason}", 3)


def try_request(config, method, path, body=None, timeout=10):
    """Non-fatal variant of make_request: returns None on any failure.

    Use for optional/secondary calls where the action should still succeed
    if this call fails (e.g., approximate-count for duplicate detection).
    """
    req = _build_authed_request(config, method, path, body)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode())
    except Exception:
        return None


def make_request_with_retry(config, method, path, body=None, retries=1):
    """Wrapper with retry logic for transient errors."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return make_request(config, method, path, body)
        except SystemExit:
            raise
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(3)
    error_exit(f"Request failed after {retries + 1} attempts: {last_error}", 3)


def handle_http_error(e):
    """Map HTTP status codes to exit codes with clear messages."""
    status = e.code
    try:
        body = json.loads(e.read().decode())
        detail = body.get("errorMessages", [body.get("message", str(body))])
        if isinstance(detail, list):
            detail = "; ".join(detail)
    except Exception:
        detail = e.reason

    if status == 401:
        error_exit(f"Authentication failed (401). Check API token. {detail}", 1)
    elif status == 403:
        error_exit(f"Access denied (403). Check permissions. {detail}", 1)
    elif status == 404:
        error_exit(f"Resource not found (404). {detail}", 4)
    elif status == 409:
        error_exit(f"Conflict (409). {detail}", 4)
    elif status == 429:
        retry_after = e.headers.get("Retry-After", "5")
        try:
            wait = int(retry_after)
        except ValueError:
            wait = 5
        print(f"Rate limited. Waiting {wait}s...", file=sys.stderr)
        time.sleep(wait)
        # Caller handles retry
        raise
    elif 500 <= status < 600:
        error_exit(f"Server error ({status}). {detail}", 3)
    else:
        error_exit(f"HTTP {status}: {detail}", 4)


# --- Markdown to Wiki Markup ---

def markdown_to_wiki(text):
    """Convert markdown (from jira-writer agent) to Jira wiki markup.

    Handles the subset of markdown that jira-writer actually produces:
    headings, bold, italic, inline code, links, lists, code blocks, blockquotes, HRs.
    """
    if not text:
        return text

    lines = text.split("\n")
    result = []
    in_code_block = False
    code_lang = ""

    for line in lines:
        # Code block toggle
        if line.strip().startswith("```"):
            if not in_code_block:
                code_lang = line.strip()[3:].strip()
                lang_attr = f":language={code_lang}" if code_lang else ""
                result.append("{code" + lang_attr + "}")
                in_code_block = True
            else:
                result.append("{code}")
                in_code_block = False
            continue

        if in_code_block:
            result.append(line)
            continue

        # Headings: ### H3 → h3. H3
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            result.append(f"h{level}. {heading_match.group(2)}")
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", line.strip()):
            result.append("----")
            continue

        # Blockquote
        if line.startswith("> "):
            result.append("{quote}" + line[2:] + "{quote}")
            continue

        # Unordered list: - item → * item
        list_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if list_match:
            indent = len(list_match.group(1)) // 2
            prefix = "*" * (indent + 1)
            result.append(f"{prefix} {list_match.group(2)}")
            continue

        # Ordered list: 1. item → # item
        olist_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if olist_match:
            indent = len(olist_match.group(1)) // 2
            prefix = "#" * (indent + 1)
            result.append(f"{prefix} {olist_match.group(2)}")
            continue

        # Inline transformations on remaining lines
        converted = line

        # Bold: **text** → *text*
        converted = re.sub(r"\*\*(.+?)\*\*", r"*\1*", converted)

        # Italic: *text* → _text_ (but not already converted bold)
        # Only match single * not preceded/followed by *
        converted = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"_\1_", converted)

        # Inline code: `code` → {{code}}
        converted = re.sub(r"`([^`]+)`", r"{{\1}}", converted)

        # Links: [text](url) → [text|url]
        converted = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[\1|\2]", converted)

        # Checkbox: - [x] → (x) / (/)
        converted = converted.replace("- [x]", "(/)").replace("- [ ]", "(x)")

        result.append(converted)

    return "\n".join(result)


# --- Actions ---

def action_verify_auth(config, _args):
    """Verify credentials are valid."""
    data = make_request(config, "GET", "/rest/api/2/myself")
    return {
        "ok": True,
        "email": data.get("emailAddress", ""),
        "displayName": data.get("displayName", ""),
        "accountId": data.get("accountId", ""),
    }


def action_get_projects(config, args):
    """Search for Jira projects."""
    query = args.query or ""
    path = f"/rest/api/2/project/search?query={urllib.request.quote(query)}&maxResults=10"
    data = make_request(config, "GET", path)
    projects = [
        {"key": p["key"], "name": p["name"], "id": p["id"]}
        for p in data.get("values", [])
    ]
    return {"ok": True, "projects": projects}


def action_search_issues(config, args):
    """Search issues via JQL using /rest/api/3/search/jql.

    Atlassian removed /rest/api/2/search and /rest/api/3/search (HTTP 410)
    in favor of a token-paginated endpoint that no longer returns `total`.
    To preserve duplicate-detection UX ("Found ~47 similar issues"), we
    fetch an approximate count from /rest/api/3/search/approximate-count
    in a separate non-fatal call. Failures there degrade to the page size.

    See: https://developer.atlassian.com/changelog/#CHANGE-2046
    """
    payload = read_payload(args.payload_file)
    jql = payload.get("jql", "")
    body = {
        "jql": jql,
        "maxResults": payload.get("maxResults", 5),
        "fields": payload.get("fields", ["summary", "status", "created", "key"]),
    }
    if payload.get("nextPageToken"):
        body["nextPageToken"] = payload["nextPageToken"]

    data = make_request(config, "POST", "/rest/api/3/search/jql", body)
    issues = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        status = fields.get("status", {})
        issues.append({
            "key": issue["key"],
            "summary": fields.get("summary", ""),
            "status": status.get("name", "") if isinstance(status, dict) else str(status),
            "created": fields.get("created", ""),
        })

    count_data = try_request(
        config, "POST", "/rest/api/3/search/approximate-count", {"jql": jql}
    )
    total = count_data.get("count", len(issues)) if count_data else len(issues)

    result = {"ok": True, "issues": issues, "total": total}
    if data.get("nextPageToken"):
        result["nextPageToken"] = data["nextPageToken"]
    return result


def action_get_issue_types(config, args):
    """Get available issue types for a project."""
    if not args.project:
        error_exit("--project required for get-issue-types", 2)
    path = f"/rest/api/2/issue/createmeta?projectKeys={args.project}&expand=projects.issuetypes"
    data = make_request(config, "GET", path)
    issue_types = []
    for proj in data.get("projects", []):
        for it in proj.get("issuetypes", []):
            issue_types.append({"name": it["name"], "id": it["id"], "subtask": it.get("subtask", False)})
    return {"ok": True, "issueTypes": issue_types}


def action_create_issue(config, args):
    """Create a new Jira issue."""
    payload = read_payload(args.payload_file)

    for field in ("project_key", "issue_type", "summary"):
        if field not in payload or not payload[field]:
            error_exit(f"Missing required payload field: {field}", 2)

    description = payload.get("description", "")
    wiki_description = markdown_to_wiki(description)

    body = {
        "fields": {
            "project": {"key": payload["project_key"]},
            "issuetype": {"name": payload["issue_type"]},
            "summary": payload["summary"][:255],
            "description": wiki_description,
        }
    }

    labels = payload.get("labels", [])
    if labels:
        body["fields"]["labels"] = labels

    data = make_request(config, "POST", "/rest/api/2/issue", body)
    issue_key = data.get("key", "")
    return {
        "ok": True,
        "key": issue_key,
        "url": f"{config['baseUrl']}/browse/{issue_key}",
    }


def action_get_issue(config, args):
    """Fetch a Jira issue with comments."""
    if not args.issue_key:
        error_exit("--issue-key required for get-issue", 2)
    path = f"/rest/api/2/issue/{args.issue_key}?fields=summary,description,status,comment"
    data = make_request(config, "GET", path)
    fields = data.get("fields", {})
    status = fields.get("status", {})
    comment_data = fields.get("comment", {})
    comments = []
    for c in comment_data.get("comments", []):
        author = c.get("author", {})
        comments.append({
            "author": author.get("displayName", author.get("name", "Unknown")),
            "created": c.get("created", ""),
            "body": c.get("body", ""),
        })
    return {
        "ok": True,
        "key": data.get("key", args.issue_key),
        "summary": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "status": status.get("name", "") if isinstance(status, dict) else str(status),
        "comments": comments,
    }


def action_add_comment(config, args):
    """Add a comment to a Jira issue."""
    if not args.issue_key:
        error_exit("--issue-key required for add-comment", 2)
    payload = read_payload(args.payload_file)
    raw_body = payload.get("body", "")
    if not raw_body:
        error_exit("Payload must contain non-empty 'body' field", 2)

    wiki_body = markdown_to_wiki(raw_body)
    data = make_request(
        config, "POST",
        f"/rest/api/2/issue/{args.issue_key}/comment",
        {"body": wiki_body},
    )
    return {"ok": True, "commentId": data.get("id", "")}


# --- Utilities ---

def read_payload(path):
    """Read a JSON payload file."""
    if not path:
        error_exit("--payload-file required for this action", 2)
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        error_exit(f"Payload file not found: {path}", 2)
    except json.JSONDecodeError as e:
        error_exit(f"Invalid JSON in payload: {e}", 2)


def success_output(data):
    """Print JSON success response to stdout and exit 0."""
    print(json.dumps(data, indent=2))
    sys.exit(0)


def error_exit(message, code):
    """Print error to stderr, JSON to stdout, and exit with code."""
    print(message, file=sys.stderr)
    print(json.dumps({"ok": False, "error": message, "errorType": {
        1: "auth", 2: "validation", 3: "network", 4: "jira_api"
    }.get(code, "unknown")}))
    sys.exit(code)


# --- Main ---

ACTIONS = {
    "verify-auth": action_verify_auth,
    "get-projects": action_get_projects,
    "search-issues": action_search_issues,
    "get-issue-types": action_get_issue_types,
    "create-issue": action_create_issue,
    "get-issue": action_get_issue,
    "add-comment": action_add_comment,
    "get-accessible-resources": action_verify_auth,  # alias — same endpoint
}


def main():
    parser = argparse.ArgumentParser(description="Jira REST API client")
    parser.add_argument("--action", required=True, choices=ACTIONS.keys())
    parser.add_argument("--config", required=True, help="Path to credential config JSON")
    parser.add_argument("--issue-key", dest="issue_key", help="Jira issue key (e.g., PROJ-123)")
    parser.add_argument("--project", help="Jira project key")
    parser.add_argument("--query", help="Search query string")
    parser.add_argument("--payload-file", dest="payload_file", help="Path to JSON payload file")
    args = parser.parse_args()

    config = read_config(args.config)
    action_fn = ACTIONS[args.action]
    result = action_fn(config, args)
    success_output(result)


if __name__ == "__main__":
    main()
