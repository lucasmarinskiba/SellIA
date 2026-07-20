const fs = require('fs');
const path = require('path');
const MarkdownIt = require('markdown-it');
const puppeteer = require('puppeteer-core');

const baseDir = __dirname;
const mdPath = path.join(baseDir, 'HISTORIAL_DEL_PROYECTO.md');
const outPath = path.join(baseDir, 'HISTORIAL_DEL_PROYECTO.pdf');
const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

async function main() {
  const mdContent = fs.readFileSync(mdPath, 'utf-8');

  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
    breaks: false
  });

  const bodyHtml = md.render(mdContent);

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>HISTORIAL DEL PROYECTO - SellIA</title>
<style>
@page { size: A4; margin: 2cm; }
body {
  font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: #1a1a1a;
  max-width: 100%;
}
h1 { font-size: 22pt; color: #0f172a; border-bottom: 3px solid #3b82f6; padding-bottom: 8px; margin-top: 28px; page-break-after: avoid; }
h2 { font-size: 15pt; color: #1e293b; border-bottom: 1.5px solid #94a3b8; padding-bottom: 5px; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #334155; margin-top: 18px; page-break-after: avoid; }
h4 { font-size: 11pt; color: #475569; margin-top: 14px; page-break-after: avoid; }
p { margin: 8px 0; text-align: justify; }
ul, ol { margin: 8px 0; padding-left: 22px; }
li { margin: 3px 0; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 9.5pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; page-break-after: auto; }
th, td {
  border: 1px solid #cbd5e1;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
th {
  background: #f1f5f9;
  font-weight: 600;
  color: #0f172a;
}
tr:nth-child(even) { background: #f8fafc; }
code {
  background: #f1f5f9;
  padding: 2px 5px;
  border-radius: 4px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 9pt;
  color: #be123c;
}
pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 8.5pt;
  line-height: 1.45;
  page-break-inside: avoid;
}
pre code { background: transparent; color: inherit; padding: 0; font-size: inherit; }
blockquote {
  border-left: 4px solid #3b82f6;
  margin: 12px 0;
  padding: 8px 14px;
  background: #eff6ff;
  color: #1e3a8a;
  page-break-inside: avoid;
}
hr { border: none; border-top: 1px solid #cbd5e1; margin: 18px 0; }
strong { color: #0f172a; }
a { color: #2563eb; text-decoration: none; }
</style>
</head>
<body>
${bodyHtml}
</body>
</html>`;

  const browser = await puppeteer.launch({
    executablePath: edgePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: outPath,
    format: 'A4',
    printBackground: true,
    margin: { top: '2cm', right: '2cm', bottom: '2cm', left: '2cm' }
  });

  await browser.close();
  console.log('PDF generado exitosamente en:', outPath);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
