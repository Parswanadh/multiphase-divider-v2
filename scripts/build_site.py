#!/usr/bin/python3
"""Generate the presentation and copy only its referenced assets to site/."""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'site'

def main():
    for builder in ('explainer_builder.py', 'glossary_builder.py'):
        subprocess.run(['/usr/bin/python3', str(ROOT / 'presentation' / builder)], cwd=ROOT, check=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    pages = {name: (ROOT / 'presentation' / source).read_text(encoding='utf-8') for name, source in [('index.html', 'explainer.html'), ('glossary.html', 'glossary.html')]}
    refs = set(re.findall(r'assets/([\w.-]+\.webp)', '\n'.join(pages.values())))
    for name in sorted(refs):
        data = (ROOT / 'presentation' / 'assets' / name).read_bytes()
        path = Path(name)
        hashed = f'{path.stem}.{hashlib.sha256(data).hexdigest()[:12]}{path.suffix}'
        (OUT / 'assets' / hashed).write_bytes(data)
        pages = {key: val.replace('assets/' + name, 'assets/' + hashed) for key, val in pages.items()}
    for name, content in pages.items():
        (OUT / name).write_text(content.replace('explainer.html', 'index.html').replace('</head>', '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n</head>', 1), encoding='utf-8')
    (OUT / '404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Page not found</title><h1>Page not found</h1><p><a href="/">Return to the explainer</a></p></html>\n')
    (OUT / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#c96442"/><path d="M12 32h40M32 12v40" stroke="white" stroke-width="5"/><circle cx="32" cy="32" r="9" fill="#c96442" stroke="white" stroke-width="4"/></svg>\n')
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n')
    (OUT / '_headers').write_text('''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
/
  Cache-Control: public, max-age=300
/index.html
  Cache-Control: public, max-age=300
/glossary*
  Cache-Control: public, max-age=300
/404.html
  Cache-Control: public, max-age=300
/assets/*
  Cache-Control: public, max-age=31536000, immutable
''')
    print(f'Built {OUT} with {len(refs)} referenced images')

if __name__ == '__main__':
    main()
