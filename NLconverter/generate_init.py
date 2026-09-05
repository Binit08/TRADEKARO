import os
import json
from pathlib import Path

# Config
SRC = Path("frontend/src")
OUT = Path(".superdesign/init")
OUT.mkdir(parents=True, exist_ok=True)

# Helper to read file
def read_file(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading: {e}"

# theme.md
theme_content = "# Theme\n\n## globals.css\n```css\n" + read_file(SRC / "app/globals.css") + "\n```\n"
theme_content += "\n## tailwind config\n```js\n" + read_file("frontend/tailwind.config.ts") + read_file("frontend/postcss.config.mjs") + "\n```\n"
with open(OUT / "theme.md", "w") as f:
    f.write(theme_content)

# layouts.md
layout_files = list(SRC.glob("components/layout/*.tsx")) + list(SRC.glob("app/layout.tsx"))
layouts_content = "# Layouts\n\n"
for lf in layout_files:
    layouts_content += f"## {lf}\n```tsx\n{read_file(lf)}\n```\n\n"
with open(OUT / "layouts.md", "w") as f:
    f.write(layouts_content)

# components.md
comp_files = list(SRC.glob("components/**/*.tsx"))
comp_files = [c for c in comp_files if "layout" not in str(c)]
comp_content = "# Components\n\n"
for cf in comp_files:
    comp_content += f"## {cf}\n```tsx\n{read_file(cf)}\n```\n\n"
with open(OUT / "components.md", "w") as f:
    f.write(comp_content)

# routes.md
routes_content = "# Routes\n\n"
route_files = list(SRC.glob("app/**/page.tsx"))
for rf in route_files:
    routes_content += f"- /{str(rf).replace('frontend/src/app/', '').replace('/page.tsx', '').replace('page.tsx', '')}\n"
with open(OUT / "routes.md", "w") as f:
    f.write(routes_content)

# pages.md
pages_content = "# Pages\n\n"
for rf in route_files:
    pages_content += f"## {rf}\nDependencies:\n- (See components.md and layouts.md)\n\n"
with open(OUT / "pages.md", "w") as f:
    f.write(pages_content)

# extractable-components.md
ext_content = "# Extractable Components\n\n"
for lf in layout_files:
    ext_content += f"## {lf.stem}\n- Source: `{lf}`\n- Category: layout\n- Description: A layout component\n- Extractable props: \n- Hardcoded: CSS classes\n\n"
with open(OUT / "extractable-components.md", "w") as f:
    f.write(ext_content)

print("Superdesign initialization complete.")
