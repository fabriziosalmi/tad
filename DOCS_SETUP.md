# TAZCOM Documentation Site - Setup Instructions

This repository uses VitePress for documentation hosted on GitHub Pages.

## 🚀 Quick Start

```bash
# Install VitePress dependencies
cd docs
npm install

# Start development server
npm run docs:dev
# Opens at http://localhost:5173

# Build for production
npm run docs:build

# Preview production build
npm run docs:preview
```

## 📁 Documentation Structure

```
docs/
├── .vitepress/
│   └── config.js              # Site configuration & navigation
├── guide/
│   ├── getting-started.md     # Installation & first run
│   ├── installation.md        # Detailed install instructions
│   ├── user-guide.md          # Complete command reference
│   └── deployment.md          # Production deployments
├── reference/
│   └── architecture.md        # Technical architecture
├── public/                    # Static assets (logo, images)
└── index.md                   # Homepage
```

## 🌐 GitHub Pages Deployment

Documentation is **automatically deployed** when you push to `main`:

1. Edit markdown files in `docs/`
2. Commit and push to GitHub
3. GitHub Actions builds and deploys to `gh-pages` branch
4. Live at: **https://fabriziosalmi.github.io/tad/**

### Manual Deployment

If you need to deploy manually:

```bash
# Build docs
cd docs
npm run docs:build

# Deploy to GitHub Pages (if you have gh-pages setup)
# The GitHub Action handles this automatically
```

## ✍️ Writing Documentation

### Adding a New Page

1. Create markdown file in `docs/guide/` or `docs/reference/`
2. Add to sidebar in `docs/.vitepress/config.js`:

```js
sidebar: {
  '/guide/': [
    {
      text: 'Introduction',
      items: [
        { text: 'Your New Page', link: '/guide/your-new-page' }
      ]
    }
  ]
}
```

### Markdown Features

VitePress supports:
- Standard Markdown
- Code blocks with syntax highlighting
- Custom containers (tip, warning, danger)
- Frontmatter for metadata
- Vue components in markdown

Example:

```markdown
# Page Title

::: tip
This is a helpful tip!
:::

\`\`\`python
def hello():
    print("Hello, TAZCOM!")
\`\`\`
```

## 🎨 Customization

### Site Config

Edit `docs/.vitepress/config.js` to customize:
- Site title and description
- Navigation menu
- Sidebar structure
- Theme colors
- Social links

### Logo & Assets

Place images in `docs/public/`:
- `logo.svg` - Site logo
- `favicon.ico` - Browser icon

Reference in markdown: `![Logo](/logo.svg)`

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run docs:dev -- --port 3000
```

### Build Errors

```bash
# Clear cache and rebuild
rm -rf docs/.vitepress/cache docs/.vitepress/dist
cd docs && npm run docs:build
```

### GitHub Pages Not Updating

1. Check GitHub Actions workflow status
2. Ensure `gh-pages` branch exists
3. Verify Pages is enabled in repo settings
4. Check `base` path in `config.js` matches repo name

## 📚 Resources

- **VitePress Docs:** https://vitepress.dev/
- **Markdown Guide:** https://www.markdownguide.org/
- **GitHub Pages:** https://pages.github.com/

## 🤝 Contributing

To contribute to documentation:

1. Fork the repository
2. Create feature branch (`git checkout -b docs/improve-guide`)
3. Edit documentation files
4. Test locally (`npm run docs:dev`)
5. Commit changes
6. Push and create Pull Request

---

**Need help?** Open an issue on [GitHub](https://github.com/fabriziosalmi/tad/issues).
