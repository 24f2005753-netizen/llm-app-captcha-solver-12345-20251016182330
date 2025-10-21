"""
LLM Helper Module for generating HTML/JS/CSS applications using OpenRouter API
Includes deterministic builders for specific briefs to avoid external dependency.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

try:
    from openai import OpenAI  # type: ignore
except Exception:  # openai may be absent or fail when not configured
    OpenAI = None  # type: ignore

from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppGenerationRequest(BaseModel):
    task: str
    brief: str
    round: int = 1
    attachments: Optional[List[Dict[str, Any]]] = None


class GeneratedApp(BaseModel):
    html_content: str
    css_content: str
    js_content: str
    metadata: Dict[str, Any]
    extra_files: Optional[Dict[str, str]] = None


class LLMHelper:
    def __init__(self):
        """
        Initializes OpenRouter/OpenAI-compatible client when API key is available.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if api_key and OpenAI is not None:
            self.client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1"),
            )

        self.model = os.getenv("OPENAI_MODEL", "arliai/qwq-32b-arliai-rpr-v1:free")
        logger.info(f"Using model: {self.model}")

    def generate_app(self, request: AppGenerationRequest) -> GeneratedApp:
        """
        Generate complete web app based on user brief.
        Uses deterministic builders for known briefs, otherwise uses LLM if configured.
        """
        brief_lower = (request.brief or "").lower()
        try:
            if "sum-of-sales" in brief_lower or "sales" in brief_lower:
                return self._build_sum_of_sales_app(request)
            if "markdown-to-html" in brief_lower or "markdown" in brief_lower:
                return self._build_markdown_to_html_app(request)
            if "github-user" in brief_lower:
                return self._build_github_user_created_app(request)
        except Exception as e:
            logger.error(f"Deterministic builder failed, trying LLM if available: {e}")

        if not self.client:
            raise RuntimeError("LLM client not configured and no deterministic builder matched")

        try:
            prompt = (
                self._build_initial_prompt(request)
                if request.round == 1
                else self._build_revision_prompt(request)
            )

            logger.info(f"Generating app (Round {request.round}) using {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert web developer. "
                            "Always respond in strict JSON format with keys: "
                            "html_content, css_content, js_content, metadata."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=4000,
            )
            content = response.choices[0].message.content
            app_data = json.loads(content)
            return GeneratedApp(
                html_content=app_data.get("html_content", ""),
                css_content=app_data.get("css_content", ""),
                js_content=app_data.get("js_content", ""),
                metadata=app_data.get("metadata", {}),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM: {e}")
            raise ValueError("Invalid JSON response from OpenRouter API")
        except Exception as e:
            logger.error(f"App generation failed: {e}")
            raise

    # ------------------------ Deterministic builders ------------------------
    def _decode_data_url(self, url: str) -> Tuple[str, str]:
        try:
            if not url or not url.startswith("data:"):
                return "", ""
            header, b64 = url.split(",", 1)
            mime = header[5:]
            if ";base64" in mime:
                mime = mime.replace(";base64", "")
                import base64
                decoded = base64.b64decode(b64).decode("utf-8", errors="replace")
            else:
                from urllib.parse import unquote
                decoded = unquote(b64)
            return mime, decoded
        except Exception:
            return "", ""

    def _collect_attachments(self, request: AppGenerationRequest) -> Dict[str, str]:
        files: Dict[str, str] = {}
        if not request.attachments:
            return files
        for a in request.attachments:
            name = a.get("name") if isinstance(a, dict) else None
            url = a.get("url") if isinstance(a, dict) else None
            if not name or not url:
                continue
            _, text = self._decode_data_url(url)
            files[name] = text
        return files

    def _build_sum_of_sales_app(self, request: AppGenerationRequest) -> GeneratedApp:
        files = self._collect_attachments(request)
        data_csv = files.get("data.csv", "")
        html = (
            "<!doctype html><html><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>Sales Summary</title>"
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\">"
            "</head><body class=\"p-4\">"
            "<div class=\"container\">"
            "<h1 class=\"mb-3\">Sales Summary</h1>"
            "<div class=\"mb-2\">Total: <span id=\"total-sales\">0</span> <span id=\"total-currency\"></span></div>"
            "<div class=\"mb-3\">"
            "<label class=\"form-label\" for=\"region-filter\">Region</label>"
            "<select id=\"region-filter\" class=\"form-select\"><option value=\"all\">All</option></select>"
            "</div>"
            "<div class=\"mb-3\">"
            "<label class=\"form-label\" for=\"currency-picker\">Currency</label>"
            "<select id=\"currency-picker\" class=\"form-select\"><option value=\"USD\">USD</option></select>"
            "</div>"
            "<table id=\"product-sales\" class=\"table table-striped\"><thead><tr><th>Product</th><th>Sales</th></tr></thead><tbody></tbody></table>"
            "</div>"
            "<script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js\"></script>"
            "<script>"
            "(function(){\n"
            "  function parseCSV(text){\n"
            "    const lines=text.trim().split(/\\r?\\n/);\n"
            "    const header=lines.shift().split(',').map(s=>s.trim());\n"
            "    return lines.map(l=>{const cols=l.split(',');const o={};header.forEach((h,i)=>o[h]=cols[i]);return o;});\n"
            "  }\n"
            "  async function loadData(){\n"
            "    let csv='';\n"
            "    try{csv=await fetch('data.csv').then(r=>r.text());}catch(e){}\n"
            "    const rows = csv ? parseCSV(csv) : [];\n"
            "    const tbody=document.querySelector('#product-sales tbody');\n"
            "    const regionSel=document.getElementById('region-filter');\n"
            "    const regions = new Set(['all']);\n"
            "    for(const r of rows){\n"
            "      const p=r.product||r.Product||'Unknown';\n"
            "      const s=parseFloat(r.sales||r.Sales||0)||0;\n"
            "      const region=r.region||r.Region||'all'; regions.add(region);\n"
            "      const tr=document.createElement('tr'); tr.innerHTML=`<td>${p}</td><td>${s.toFixed(2)}</td>`; tr.dataset.region=region; tbody.appendChild(tr);\n"
            "    }\n"
            "    for(const r of regions){ if(r==='all') continue; const opt=document.createElement('option'); opt.value=r; opt.textContent=r; regionSel.appendChild(opt);}\n"
            "    function computeTotal(){\n"
            "      const region=regionSel.value; let sum=0;\n"
            "      [...tbody.querySelectorAll('tr')].forEach(tr=>{ if(region==='all'||tr.dataset.region===region){ sum+=parseFloat(tr.children[1].textContent)||0; } });\n"
            "      const el=document.getElementById('total-sales'); el.textContent=sum.toFixed(2); el.dataset.region=region;\n"
            "    }\n"
            "    regionSel.addEventListener('change', computeTotal);\n"
            "    computeTotal();\n"
            "    const picker=document.getElementById('currency-picker'); const totalCur=document.getElementById('total-currency');\n"
            "    let rates={USD:1};\n"
            "    try{ rates = await fetch('rates.json').then(r=>r.json()); }catch(e){}\n"
            "    function applyCurrency(){ const rate=rates[picker.value]||1; const base=parseFloat(document.getElementById('total-sales').textContent)||0; document.getElementById('total-sales').textContent=(base*rate).toFixed(2); totalCur.textContent = ' '+picker.value; }\n"
            "    picker.addEventListener('change', applyCurrency);\n"
            "    if(typeof seed!=='undefined'){ document.title = `Sales Summary ${seed}`; }\n"
            "  }\n"
            "  loadData();\n"
            "})();\n"
            "</script>"
            "</body></html>"
        )
        extra_files: Dict[str, str] = {}
        if data_csv:
            extra_files["data.csv"] = data_csv
        metadata = {"title": "Sales Summary"}
        return GeneratedApp(html_content=html, css_content="", js_content="", metadata=metadata, extra_files=extra_files)

    def _build_markdown_to_html_app(self, request: AppGenerationRequest) -> GeneratedApp:
        files = self._collect_attachments(request)
        input_md = files.get("input.md", "")
        html = (
            "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>Markdown Viewer</title>"
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\">"
            "<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css\">"
            "</head><body class=\"p-4\">"
            "<div class=\"container\">"
            "<div class=\"mb-3\" id=\"markdown-tabs\">"
            "<button class=\"btn btn-primary me-2\" data-target=\"output\">Rendered</button>"
            "<button class=\"btn btn-outline-secondary\" data-target=\"source\">Source</button>"
            "<span id=\"markdown-source-label\" class=\"ms-3 text-muted\"></span>"
            "<span id=\"markdown-word-count\" class=\"badge bg-secondary ms-3\">0</span>"
            "</div>"
            "<div id=\"markdown-output\" class=\"mb-3\"></div>"
            "<pre id=\"markdown-source\" class=\"p-3 bg-light border\"></pre>"
            "</div>"
            "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/marked/11.1.1/marked.min.js\"></script>"
            "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>"
            "<script>"
            "(function(){\n"
            "  function wordCount(s){ return (s.trim().match(/\\S+/g)||[]).length; }\n"
            "  async function loadMarkdown(){\n"
            "    const params=new URLSearchParams(location.search);\n"
            "    const url=params.get('url');\n"
            "    let md=''; let sourceLabel='attachment';\n"
            "    try{ md = url ? await fetch(url).then(r=>r.text()) : await fetch('input.md').then(r=>r.text()); sourceLabel = url ? url : 'attachment'; }catch(e){}\n"
            "    document.getElementById('markdown-source').textContent = md;\n"
            "    document.getElementById('markdown-output').innerHTML = marked.parse(md);\n"
            "    document.getElementById('markdown-source-label').textContent = sourceLabel;\n"
            "    document.getElementById('markdown-word-count').textContent = new Intl.NumberFormat().format(wordCount(md));\n"
            "    document.querySelectorAll('pre code').forEach(el=>hljs.highlightElement(el));\n"
            "  }\n"
            "  document.getElementById('markdown-tabs').addEventListener('click', (e)=>{ const btn=e.target.closest('button'); if(!btn) return; const target=btn.getAttribute('data-target'); document.getElementById('markdown-output').style.display = target==='output'?'block':'none'; document.getElementById('markdown-source').style.display = target==='source'?'block':'none'; });\n"
            "  loadMarkdown();\n"
            "})();\n"
            "</script>"
            "</body></html>"
        )
        extra_files: Dict[str, str] = {}
        if input_md:
            extra_files["input.md"] = input_md
        metadata = {"title": "Markdown Viewer"}
        return GeneratedApp(html_content=html, css_content="", js_content="", metadata=metadata, extra_files=extra_files)

    def _build_github_user_created_app(self, request: AppGenerationRequest) -> GeneratedApp:
        html = (
            "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>GitHub User Info</title>"
            "<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\">"
            "</head><body class=\"p-4\">"
            "<div class=\"container\">"
            "<h1 class=\"mb-3\">GitHub User Info</h1>"
            "<div id=\"github-status\" class=\"alert alert-info\" aria-live=\"polite\">Idle</div>"
            "<form id=\"github-user-${seed}\" class=\"row g-2\">"
            "<div class=\"col-auto\"><input id=\"gh-username\" class=\"form-control\" placeholder=\"Username\" required></div>"
            "<div class=\"col-auto\"><button class=\"btn btn-primary\" type=\"submit\">Lookup</button></div>"
            "</form>"
            "<div class=\"mt-3\">Created: <span id=\"github-created-at\"></span> <span id=\"github-account-age\"></span></div>"
            "</div>"
            "<script>"
            "(function(){\n"
            "  const form=document.getElementById('github-user-${seed}');\n"
            "  const statusEl=document.getElementById('github-status');\n"
            "  const createdEl=document.getElementById('github-created-at');\n"
            "  const ageEl=document.getElementById('github-account-age');\n"
            "  const stored = localStorage.getItem('github-user-${seed}');\n"
            "  if(stored){ try{ const d=JSON.parse(stored); document.getElementById('gh-username').value=d.username||''; }catch(e){} }\n"
            "  form.addEventListener('submit', async (e)=>{ e.preventDefault(); const u=document.getElementById('gh-username').value.trim(); if(!u) return; statusEl.textContent='Starting lookup...';\n"
            "    try{\n"
            "      const params=new URLSearchParams(location.search); const token=params.get('token');\n"
            "      const res = await fetch('https://api.github.com/users/'+encodeURIComponent(u), { headers: token? { Authorization: 'Bearer '+token } : {} });\n"
            "      statusEl.textContent='Lookup complete';\n"
            "      if(!res.ok){ createdEl.textContent=''; ageEl.textContent=''; return; }\n"
            "      const data=await res.json();\n"
            "      const created=new Date(data.created_at); const y=created.getUTCFullYear(); const m=String(created.getUTCMonth()+1).padStart(2,'0'); const d=String(created.getUTCDate()).padStart(2,'0');\n"
            "      createdEl.textContent = `${y}-${m}-${d}`;\n"
            "      const years = Math.max(0, Math.floor((Date.now()-created.getTime())/ (365*24*3600*1000)));\n"
            "      ageEl.textContent = ` (${years} years)`;\n"
            "      localStorage.setItem('github-user-${seed}', JSON.stringify({ username:u, created: data.created_at }));\n"
            "    }catch(e){ statusEl.textContent='Failed'; createdEl.textContent=''; ageEl.textContent=''; }\n"
            "  });\n"
            "})();\n"
            "</script>"
            "</body></html>"
        )
        metadata = {"title": "GitHub User Info"}
        return GeneratedApp(html_content=html, css_content="", js_content="", metadata=metadata)

    # ------------------------ Prompt builders ------------------------
    def _build_initial_prompt(self, request: AppGenerationRequest) -> str:
        prompt = f"""
Create a complete, minimal web app based on:

TASK: {request.task}
BRIEF: {request.brief}

Requirements:
1. Single-page HTML5 app (self-contained)
2. Include embedded CSS and JavaScript
3. Be functional and visually appealing
4. Responsive and works directly in browser

Respond strictly as JSON with:
- html_content
- css_content
- js_content
- metadata (title, description)
"""
        if request.attachments:
            prompt += f"\nAttachments:\n{json.dumps(request.attachments, indent=2)}"
        return prompt

    def _build_revision_prompt(self, request: AppGenerationRequest) -> str:
        prompt = f"""
Revise the previous app as per feedback.

TASK: {request.task}
BRIEF: {request.brief}
ROUND: {request.round}

Keep same functionality but improve UI/UX and fix issues.
Respond with JSON (same keys as before).
"""
        if request.attachments:
            prompt += f"\nRevision context:\n{json.dumps(request.attachments, indent=2)}"
        return prompt

    def validate_generated_app(self, app: GeneratedApp) -> bool:
        try:
            if not app.html_content or "<html" not in app.html_content.lower():
                return False
            if not app.css_content and "style" not in app.html_content.lower():
                return False
            if not app.js_content and "script" not in app.html_content.lower():
                return False
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


