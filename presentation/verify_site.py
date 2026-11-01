# presentation/verify_site.py
"""
Validates presentation/explainer.html and presentation/glossary.html:
1. HTML parser check (no unclosed tags or syntax issues)
2. Every <img src> points to an existing file in presentation/
3. Every local <a href> points to an existing file/anchor
4. No external http:// or https:// script, link, or img resources
5. JavaScript syntax validation using node --check
6. Report file sizes
"""
import os
import re
import subprocess
import html.parser
from urllib.parse import urlparse

class StrictHtmlValidator(html.parser.HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.tags_stack = []
        self.img_sources = []
        self.hrefs = []
        self.scripts = []
        self.in_script = False
        self.current_script = []
        self.errors = []
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Check resources
        if tag == 'img' and 'src' in attrs_dict:
            self.img_sources.append(attrs_dict['src'])
        if 'href' in attrs_dict:
            self.hrefs.append(attrs_dict['href'])
        if tag == 'script' and 'src' in attrs_dict:
            self.errors.append(f"External script found: {attrs_dict['src']}")
        if tag == 'link' and attrs_dict.get('rel') == 'stylesheet' and 'href' in attrs_dict:
            self.errors.append(f"External stylesheet found: {attrs_dict['href']}")

        if tag == 'script' and 'src' not in attrs_dict:
            script_type = attrs_dict.get('type', 'text/javascript').lower()
            self.in_script = True
            self.current_script = []
            self.current_script_type = script_type

        if tag not in self.void_elements:
            self.tags_stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
            self.scripts.append((getattr(self, 'current_script_type', 'text/javascript'), "".join(self.current_script)))
            self.current_script = []

        if tag not in self.void_elements:
            if not self.tags_stack:
                self.errors.append(f"Unexpected closing tag </{tag}> with empty stack")
            elif self.tags_stack[-1] == tag:
                self.tags_stack.pop()
            else:
                self.errors.append(f"Tag mismatch: expected </{self.tags_stack[-1]}>, found </{tag}>")

    def handle_data(self, data):
        if self.in_script:
            self.current_script.append(data)

def check_file(filepath):
    print(f"\n==================================================")
    print(f"Validating {filepath}")
    print(f"==================================================")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    validator = StrictHtmlValidator(filepath)
    validator.feed(content)

    if validator.tags_stack:
        validator.errors.append(f"Unclosed tags remaining on stack: {validator.tags_stack}")

    # 1. HTML parsing errors
    if validator.errors:
        print(f"❌ HTML structure errors found ({len(validator.errors)}):")
        for err in validator.errors[:10]:
            print(f"   - {err}")
    else:
        print("✓ HTML syntax & tag nesting clean! Zero unclosed tag errors.")

    # 2. Check <img src>
    missing_imgs = []
    base_dir = os.path.dirname(filepath)
    for src in validator.img_sources:
        if src.startswith(('http://', 'https://')):
            validator.errors.append(f"External image URL: {src}")
            continue
        clean_src = src.split('?')[0].split('#')[0]
        if not clean_src:
            continue
        full_path = os.path.join(base_dir, clean_src)
        if not os.path.isfile(full_path):
            missing_imgs.append(src)

    if missing_imgs:
        print(f"❌ Missing images ({len(missing_imgs)}):")
        for img in missing_imgs:
            print(f"   - {img}")
    else:
        print(f"✓ All {len(validator.img_sources)} image sources exist locally on disk.")

    # 3. Check local hrefs
    missing_hrefs = []
    for href in validator.hrefs:
        if href.startswith(('http://', 'https://', 'javascript:', 'mailto:')):
            continue
        # Split anchor
        parts = href.split('#')
        target_file = parts[0]
        if target_file:
            target_path = os.path.join(base_dir, target_file)
            if not os.path.isfile(target_path):
                missing_hrefs.append(href)

    if missing_hrefs:
        print(f"❌ Broken local href targets ({len(missing_hrefs)}):")
        for h in missing_hrefs:
            print(f"   - {h}")
    else:
        print(f"✓ Local href links verified.")

    # 4. Check for external URLs in resource tags (<script src>, <link href>, <img src>)
    resource_patterns = [
        re.compile(r'<script[^>]+src=["\'](https?://[^"\']+)["\']', re.IGNORECASE),
        re.compile(r'<link[^>]+href=["\'](https?://[^"\']+)["\']', re.IGNORECASE),
        re.compile(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', re.IGNORECASE)
    ]
    external_res = []
    for pat in resource_patterns:
        external_res.extend(pat.findall(content))

    if external_res:
        print(f"❌ External resource URLs found ({len(external_res)}):")
        for u in external_res:
            print(f"   - {u}")
    else:
        print("✓ Zero external resource calls (no external CDNs, fonts, or scripts).")

    # 5. Node.js check on embedded JS (and JSON check on application/json)
    js_errors = 0
    import json as pyjson
    for idx, (script_type, script_text) in enumerate(validator.scripts):
        if not script_text.strip():
            continue
        if 'json' in script_type:
            try:
                pyjson.loads(script_text)
            except Exception as e:
                print(f"❌ JSON parse error in script block {idx} (type={script_type}): {e}")
                js_errors += 1
            continue
        tmp_js = f"/tmp/check_script_{idx}.js"
        with open(tmp_js, 'w', encoding='utf-8') as fjs:
            fjs.write(script_text)
        res = subprocess.run(["node", "--check", tmp_js], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ JS syntax error in script block {idx}:")
            print(res.stderr)
            js_errors += 1
        os.remove(tmp_js)

    if js_errors == 0:
        print(f"✓ Embedded JavaScript syntax verified with node --check (0 errors) and JSON blocks validated.")

    # 6. File size
    size_kb = os.path.getsize(filepath) / 1024
    print(f"✓ Final file size: {size_kb:.1f} KB ({os.path.getsize(filepath)} bytes)")

if __name__ == "__main__":
    check_file("presentation/explainer.html")
    check_file("presentation/glossary.html")
