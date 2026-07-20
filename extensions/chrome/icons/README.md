# Icons needed

Generate icon16.png, icon48.png, icon128.png

Brand: gradient cyan → purple → pink · 🧠 brain glyph or SellIA "S" lettermark.

Use Figma export or:
```bash
# Quick magick generation
convert -size 128x128 -background "#0a0e1a" -fill white -gravity center label:"S" icon128.png
convert icon128.png -resize 48x48 icon48.png
convert icon128.png -resize 16x16 icon16.png
```

Or use https://favicon.io to generate from emoji 🧠.
