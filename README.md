# Docs Build

pip install -r requirements.txt
python scripts/generate_rst.py

# Build HTML docs with Sphinx
sphinx-build -W --keep-going -b html docs docs/_build/html

# Open generated HTML docs
open docs/_build/html/index.html

# Windows
start docs\_build\html\index.html

# If HTML render fails, run a local server (better for Sphinx)
python -m http.server 8000 --directory docs\_build\html

## Troubleshooting

### 1. Generated HTML files are broken due to wrong encoding
### 2. CRLF is not parsed by Windows PowerShell

# Check CRLF/LF
python -c "from pathlib import Path; raw = Path('docs/index.rst').read_bytes(); print('CRLF:', raw.count(b'\r\n'), 'LF:', raw.count(b'\n'), 'bare CR:', raw.count(b'\r') - raw.count(b'\r\n'))"

# If CRLF > 0, normalize docs/index.rst
python -c "
from pathlib import Path
p = Path('docs/index.rst')
raw = p.read_bytes()
text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
p.write_text(text, encoding='utf-8', newline='\n')
print('normalized')
"

# Or normalize all project files
python scripts\normalize_text.py

# Rebuild docs
sphinx-build -W --keep-going -b html docs docs\_build\html

# Final check
python scripts\normalize_text.py
python scripts\generate_rst.py
Remove-Item -Recurse -Force docs\_build -ErrorAction SilentlyContinue
sphinx-build -E -a -W --keep-going -b html docs docs\_build\html
python -m http.server 8000 --directory docs\_build\html