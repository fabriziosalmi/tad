# TAD Documentation

This directory contains the documentation for TAD.

## Local Development

```bash
# Install dependencies
cd docs
npm install

# Start dev server
npm run docs:dev

# Build for production
npm run docs:build

# Preview production build
npm run docs:preview
```

## Documentation Structure

```
docs/
├── .vitepress/
│   └── config.js          # VitePress configuration
├── guide/
│   ├── getting-started.md
│   ├── installation.md
│   ├── user-guide.md
│   ├── deployment.md
│   └── ...
├── reference/
│   ├── architecture.md
│   ├── api-*.md
│   └── ...
└── index.md               # Homepage
```

## Deployment

Documentation is automatically deployed to GitHub Pages via GitHub Actions:

- **Workflow:** `.github/workflows/docs.yml`
- **Trigger:** Push to `main` branch with changes in `docs/`
- **URL:** https://fabriziosalmi.github.io/tad/

## Contributing

To add or update documentation:

1. Edit markdown files in `docs/`
2. Test locally with `npm run docs:dev`
3. Commit and push to `main`
4. GitHub Actions will auto-deploy

## Links

- **Live Docs:** https://fabriziosalmi.github.io/tad/
- **VitePress:** https://vitepress.dev/
- **GitHub:** https://github.com/fabriziosalmi/tad
