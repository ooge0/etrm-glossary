"""Normalize text files: strip BOM, force LF, remove invisible unicode."""
import sys
from pathlib import Path

EXTS = {".py", ".rst", ".md", ".yaml", ".yml", ".txt", ".cfg", ".ini", ".toml", ".json"}
SKIP_DIRS = {".venv", "venv", "_build", ".git", "__pycache__", ".pytest_cache"}

# invisible / problematic unicode
INVISIBLE = {
    "\u00a0": " ",     # NBSP → space
    "\u200b": "",      # zero-width space
    "\u200c": "",      # zero-width non-joiner
    "\u200d": "",      # zero-width joiner
    "\ufeff": "",      # BOM anywhere
    "\u2028": "\n",    # line separator
    "\u2029": "\n",    # paragraph separator
}

def normalize(path: Path) -> bool:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        text = raw.decode("utf-16-le")
    elif raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16-be")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"SKIP (not utf-8): {path}")
            return False

    original = text
    for bad, good in INVISIBLE.items():
        text = text.replace(bad, good)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False

def main(targets):
    fixed = 0
    for target in targets:
        p = Path(target)
        candidates = [p] if p.is_file() else p.rglob("*")
        for f in candidates:
            if not f.is_file() or f.suffix not in EXTS:
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            if normalize(f):
                print(f"FIXED: {f}")
                fixed += 1
    print(f"done, {fixed} files normalized")

if __name__ == "__main__":
    args = sys.argv[1:] or ["."]
    main(args)