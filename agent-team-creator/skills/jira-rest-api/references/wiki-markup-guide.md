# Jira Wiki Markup Reference

This reference documents the Jira wiki markup syntax used by REST API v2.
The `jira_client.py` script converts markdown to wiki markup automatically,
but this guide is useful for understanding the output format and edge cases.

## Core Syntax Translation

| Markdown | Wiki Markup | Notes |
|----------|-------------|-------|
| `# Heading 1` | `h1. Heading 1` | Levels 1-6 |
| `## Heading 2` | `h2. Heading 2` | |
| `**bold**` | `*bold*` | Single asterisks |
| `*italic*` | `_italic_` | Underscores |
| `` `inline code` `` | `{{inline code}}` | Double braces |
| `[text](url)` | `[text\|url]` | Pipe separator |
| `- list item` | `* list item` | Asterisk prefix |
| `1. ordered` | `# ordered` | Hash prefix |
| `> blockquote` | `{quote}text{quote}` | Macro syntax |
| `---` | `----` | Four dashes |
| `- [x] done` | `(/) done` | Check mark |
| `- [ ] todo` | `(x) todo` | Cross mark |

## Code Blocks

Markdown:
~~~
```python
def hello():
    print("world")
```
~~~

Wiki markup:
```
{code:language=python}
def hello():
    print("world")
{code}
```

## Tables

Wiki markup tables use `||` for headers and `|` for cells:

```
||Header 1||Header 2||Header 3||
|Cell 1|Cell 2|Cell 3|
|Cell 4|Cell 5|Cell 6|
```

## Panels

```
{panel:title=Important Note}
Panel content here.
{panel}
```

## Mentions

```
[~accountId:5a09588d12345]
```

## Colors and Effects

```
{color:red}Red text{color}
+inserted text+
-deleted text-
^superscript^
~subscript~
```

## Images

```
!image.png|width=300!
!https://example.com/image.png!
```
