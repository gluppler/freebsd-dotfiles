#!/usr/bin/env python3
"""Maintainer tool, not run by the installer: refresh docs/secret-knowledge.

Reads a local checkout of trimstray/the-book-of-secret-knowledge as data and
writes its systems, networking, distributed-systems and design chapters as
Markdown. The HTML link lists become Markdown lists; prose and code stay as
written.

    python3 -I .install/scripts/import-secret-knowledge.py /path/to/the-book-of-secret-knowledge
"""
import html.parser
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/secret-knowledge"
NBSP = chr(0xA0)

# Output file, title, then (chapter, sections) pairs; None keeps every section.
CHAPTERS = [
    ("tools.md", "Command-line and network tools", [
        ("CLI Tools", ["Files and directories", "Network", "Network (DNS)", "Network (HTTP)", "SSL",
                       "System Diagnostics/Debuggers", "Log Analyzers", "Databases"]),
        ("Networks", None),
    ]),
    ("services.md", "Systems, services and containers", [
        ("Systems/Services", ["Operating Systems", "HTTP(s) Services", "DNS Services", "Other Services"]),
        ("Containers/Orchestration", None),
    ]),
    ("howtos.md", "Manuals, howtos and tutorials", [
        ("Manuals/Howtos/Tutorials", ["Shell/Command line", "Text Editors", "Python", "Sed & Awk & Other",
                                      r"\*nix & Network", "Large-scale systems", "System hardening",
                                      "All-in-one", "Ebooks", "Other"]),
    ]),
    ("lists.md", "Reading lists", [("Inspiring Lists", ["SysOps/DevOps", "Developers"])]),
    ("one-liners.md", "Shell one-liners", [("Shell One-liners", None)]),
    ("shell-tricks.md", "Shell tricks and functions", [("Shell Tricks", None), ("Shell functions", None)]),
]
FENCE = re.compile(r"^\s*```")


def chapters(lines):
    """Map each chapter name to its section names -> lines; "" holds the chapter's own text."""
    book, chapter, section, fence = {}, None, None, False
    for line in lines:
        if FENCE.match(line):
            fence = not fence
        if not fence:
            match = re.match(r"#### (.+?) &nbsp;\[<sup>\[TOC\]</sup>\]", line)
            if match:
                chapter, section = match.group(1), ""
                book[chapter] = {"": []}
                continue
            match = re.match(r"##### :black_small_square: (.+)", line)
            if chapter and match:
                section = match.group(1).strip()
                book[chapter][section] = []
                continue
        if chapter:
            book[chapter][section].append(line)
    if fence:
        sys.exit("Unclosed code block in the book.")
    return book


def text(data):
    """Book text as literal Markdown text."""
    data = data.replace(NBSP, " ")
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", data)


def target(href):
    if not re.fullmatch(r"https?://[^\s<>\"]+", href):
        sys.exit(f"Unexpected link: {href}")
    return href.replace("(", "%28").replace(")", "%29")


class LinkList(html.parser.HTMLParser):
    """A <p> block of '<a href=URL><b>name</b></a> - description<br>' entries."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries, self.entry, self.link, self.bold = [], [], None, False

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.close_entry()
        elif tag == "a" and self.link is None:
            self.link = (target(dict(attrs).get("href") or ""), [])
        elif tag == "b" and not self.bold:
            self.bold = True
            if self.link is None:
                self.entry.append("**")
        elif tag != "p":
            sys.exit(f"Unexpected <{tag}> in a link list.")

    def handle_endtag(self, tag):
        if tag == "a" and self.link is not None:
            href, label = self.link
            self.entry.append(f"[{''.join(label).strip()}]({href})")
            self.link = None
        elif tag == "b" and self.bold:
            self.bold = False
            if self.link is None:
                self.entry.append("**")
        elif tag not in ("p", "br"):
            sys.exit(f"Unexpected </{tag}> in a link list.")

    def handle_data(self, data):
        (self.link[1] if self.link is not None else self.entry).append(text(data))

    def close_entry(self):
        if self.link is not None or self.bold:
            sys.exit("Unclosed tag in a link list.")
        entry = " ".join("".join(self.entry).split())
        if entry:
            self.entries.append("- " + entry)
        self.entry = []


def links(block):
    parser = LinkList()
    parser.feed(" ".join(block))
    parser.close()
    parser.close_entry()
    return parser.entries


def prose(lines, level):
    """One-liner chapters: headings move to this file's levels; text and code stay."""
    out, fence, contents = [], False, False
    # Entries nest under a tool's heading when the chapter has them.
    entry = level
    for line in lines:
        if FENCE.match(line):
            fence = not fence
        elif not fence:
            if line.startswith("##### Table of Contents"):
                contents = True
                continue
            match = re.match(r"##### Tool: \[([^\]]+)\]\((.+)\)\s*$", line)
            if match:
                contents, entry = False, level + 1
                out += [f"{'#' * level} {match.group(1)}", "", f"<{match.group(2)}>"]
                continue
            match = re.match(r"###### (.+)", line)
            if match:
                contents = False
                out.append(f"{'#' * entry} {match.group(1)}")
                continue
            if line.startswith("#"):
                sys.exit(f"Unexpected heading: {line}")
        if not contents:
            out.append(line.rstrip())
    return out


def outside_code(lines):
    fence = False
    for line in lines:
        if FENCE.match(line):
            fence = not fence
        yield fence, line


def body(lines, level):
    """A section's lines: <p> link lists become Markdown lists, everything else is prose."""
    if not any(not fence and line.strip().startswith("<p>") for fence, line in outside_code(lines)):
        return prose(lines, level)
    out, block = [], None
    for fence, line in outside_code(lines):
        stripped = line.strip()
        if block is None and not fence and stripped.startswith("<p>"):
            block = []
        if block is None:
            out.append(line.rstrip())
            continue
        block.append(stripped)
        if stripped.endswith("</p>"):
            out += links(block)
            block = None
    if block is not None:
        sys.exit("Unclosed link list.")
    return out


def main():
    source = Path(sys.argv[1]).resolve()
    commit = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    book = chapters((source / "README.md").read_text(encoding="utf-8").splitlines())
    header = ("Selected from [The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) "
              f"by trimstray, commit `{commit[:12]}`, under the MIT license in [LICENSE.md](LICENSE.md).")
    OUTPUT.mkdir(exist_ok=True)
    for name, title, parts in CHAPTERS:
        out = [f"# {title}", "", header, ""]
        # A file with several chapters gives each its own heading.
        level = 2 if len(parts) == 1 else 3
        for chapter, sections in parts:
            if chapter not in book:
                sys.exit(f"Missing chapter: {chapter}")
            content = book[chapter]
            if len(parts) > 1:
                out += [f"## {chapter}", ""]
            out += body(content[""], level) + [""]
            for section in [s for s in content if s] if sections is None else sections:
                if section not in content:
                    sys.exit(f"Missing section: {chapter} / {section}")
                entries = body(content[section], level + 1)
                if not any(line.strip() for line in entries):
                    sys.exit(f"Empty section: {chapter} / {section}")
                out += [f"{'#' * level} {section}", ""] + entries + [""]
        document = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip() + "\n"
        (OUTPUT / name).write_text(document, encoding="utf-8")
    (OUTPUT / "LICENSE.md").write_text((source / "LICENSE.md").read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
