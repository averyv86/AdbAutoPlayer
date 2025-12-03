# Nextra Documentation Site - Deployment Guide

## Quick Start

### Local Development

```bash
cd /Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude/skills/macos-resource-optimizer/.data/docs

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:3000
```

### Production Build

```bash
# Build static site
npm run build

# Test production build locally
npm start

# Site will be at http://localhost:3000
```

## Directory Structure

```
.claude/skills/macos-resource-optimizer/.data/docs/
├── package.json                  # Dependencies and scripts
├── next.config.js               # Next.js configuration
├── theme.config.tsx             # Nextra theme config
├── tsconfig.json                # TypeScript config
├── .gitignore                   # Git ignore rules
│
├── pages/                       # Documentation content
│   ├── index.mdx               # Homepage
│   ├── _meta.json              # Main navigation
│   │
│   ├── getting-started/        # Installation & setup
│   ├── architecture/           # System design
│   ├── commands/               # Command reference
│   ├── agents/                 # MoAI-ADK integration
│   ├── api/                    # API documentation
│   ├── guides/                 # Help guides
│   └── migration/              # Upgrade guide
│
├── public/                      # Static assets
│   └── images/                 # Images and diagrams
│
└── Documentation files
    ├── DOCUMENTATION_SUMMARY.md # Content summary
    ├── DEPLOYMENT_GUIDE.md     # This file
    └── README.md               # Setup instructions
```

## Content Overview

### Pages Created: 30+

#### Core Documentation (23 pages)
- 1 Homepage
- 4 Getting Started pages
- 3 Architecture pages
- 7 Command pages
- 4 API reference pages
- 3 Guide pages
- 1 Migration guide

#### Navigation Files (8 _meta.json)
- Root navigation
- Section navigations
- Page ordering

## Deployment Options

### Option 1: Vercel (Recommended)

Fastest deployment with zero configuration.

```bash
# 1. Push to GitHub
git push origin main

# 2. Connect to Vercel
# - Go to vercel.com
# - Import repository
# - Select framework: Next.js
# - Build settings auto-detected
# - Deploy

# Auto-deploys on every push
```

**Advantages**:
- Zero configuration
- Automatic builds on push
- Global CDN
- SSL included
- Free tier available
- Domain management

### Option 2: GitHub Pages

Free static hosting from GitHub.

```bash
# 1. Build static export
npm run build
npm run export  # If available, or use: next export

# 2. Upload ./out directory to gh-pages branch
# Option A: Use gh-pages package
npm install gh-pages --save-dev

# Option B: Manual upload
git checkout gh-pages
cp -r .next/static/* ./
git add .
git commit -m "Update docs"
git push

# 3. Enable Pages in repo settings
# Settings → Pages → Source: gh-pages branch
```

**Advantages**:
- Free
- Integrated with GitHub
- No external services needed

### Option 3: Netlify

Easy drag-and-drop deployment.

```bash
# 1. Connect GitHub to Netlify
# - Go to netlify.com
# - Click "New site from Git"
# - Select repository
# - Configure build settings:
#   - Build command: npm run build
#   - Publish directory: .next

# 2. Deploy
# Auto-deploys on push

# Optional: Connect custom domain
```

**Advantages**:
- Simple setup
- Good performance
- Form handling
- Analytics included

### Option 4: Self-Hosted

Deploy to your own server.

```bash
# 1. Build for production
npm run build

# 2. Start server
npm start

# 3. Use PM2 to keep running
npm install -g pm2
pm2 start npm --name "macos-docs" -- start
pm2 save

# 4. Use Nginx as reverse proxy
# Configure /etc/nginx/sites-available/docs
# upstream docs {
#   server localhost:3000;
# }
# server {
#   server_name docs.example.com;
#   location / {
#     proxy_pass http://docs;
#   }
# }

# 5. Enable SSL with Let's Encrypt
# sudo certbot --nginx -d docs.example.com
```

**Advantages**:
- Full control
- Custom configuration
- Integration with existing infrastructure

## Configuration

### Update Domain

Edit `theme.config.tsx`:

```typescript
export default {
  logo: <span>macOS Resource Optimizer v7.0</span>,

  // Update GitHub link
  project: {
    link: 'https://github.com/your-org/macos-resource-optimizer'
  },

  // Update repository link
  docsRepositoryBase: 'https://github.com/your-org/macos-resource-optimizer/tree/main/.claude/skills/macos-resource-optimizer/.data/docs',

  // Update footer
  footer: {
    text: 'macOS Resource Optimizer v7.0 - MoAI-ADK'
  }
}
```

### Update Search

Search is enabled by default via FlexSearch. No configuration needed.

### Custom Styling

Edit `styles/globals.css` (create if needed):

```css
:root {
  --primary-color: #0070f3;
  --background: #ffffff;
  --text: #000000;
}

html[data-theme='dark'] {
  --primary-color: #3291ff;
  --background: #111111;
  --text: #ffffff;
}
```

## Content Management

### Adding New Pages

1. Create `.mdx` file in `pages/[section]/`:

```mdx
# Page Title

Content here...

## Section

More content...
```

2. Add to `_meta.json`:

```json
{
  "index": "Overview",
  "new-page": "New Page Title"
}
```

3. Reference from other pages:

```mdx
[Learn more →](/section/new-page)
```

### Updating Existing Pages

1. Edit `.mdx` file
2. Changes auto-reload in dev mode
3. Test locally: `npm run dev`
4. Commit and push

### Adding Images

1. Save image in `public/images/`
2. Reference in markdown:

```mdx
![Alt text](/images/filename.png)
```

## Building & Testing

### Development

```bash
npm run dev
# Site at http://localhost:3000
# Hot reload enabled
# Changes auto-update
```

### Production Build

```bash
npm run build
# Creates optimized build
# Ready for deployment
```

### Test Production Build Locally

```bash
npm run build
npm start
# Test at http://localhost:3000
```

### Check Build Size

```bash
npm run build
# Shows bundle size and optimization info
```

## Performance Optimization

### Image Optimization

Place images in `public/images/` for automatic optimization:

```mdx
![Description](/images/diagram.png)
```

### Code Splitting

Automatic for each page, no configuration needed.

### Static Generation

All pages pre-rendered at build time for fastest performance.

## SEO

Automatically optimized:
- Meta tags from filenames
- Open Graph support
- Sitemap generation
- Structured data

Add custom meta in `.mdx`:

```mdx
---
title: Page Title
description: Page description for SEO
---

# Page Title
```

## Analytics

### Google Analytics

Add to `theme.config.tsx`:

```typescript
export default {
  // ... other config
  useNextSeoProps() {
    return {
      titleTemplate: '%s – macOS Resource Optimizer'
    }
  }
}
```

Then add GA script to `_app.tsx`.

### Vercel Analytics

Automatic if deployed on Vercel.

## Monitoring & Maintenance

### Check Site Health

```bash
# Check links
npm run lint

# Check performance
npm run build
# Review output for warnings
```

### Monitor Uptime

- Vercel: Built-in monitoring
- GitHub Pages: Check status page
- Netlify: Built-in status page
- Self-hosted: Use external monitoring

### View Analytics

- Vercel: vercel.com dashboard
- Netlify: netlify.com dashboard
- Google Analytics: analytics.google.com

## Troubleshooting

### Build Fails

```bash
# Clear cache
rm -rf .next
rm -rf node_modules

# Reinstall
npm install

# Rebuild
npm run build
```

### Pages Not Showing

Check `_meta.json` in each section:

```json
{
  "index": "Overview",
  "new-page": "New Page Title"
}
```

### Search Not Working

Search is automatic in Nextra. Check:
- Pages are MDX files
- Files in `pages/` directory
- Build completed successfully

### Styling Issues

Clear Next.js cache:

```bash
rm -rf .next
npm run dev
```

### Deployment Fails

Check:
- Node.js version ≥ 16
- All dependencies installed
- No TypeScript errors
- Build succeeds locally

## Commands Reference

### Development

```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Check code quality
```

### Deployment

```bash
# Vercel
vercel deploy

# GitHub Pages
git push origin main

# Netlify
# Auto-deploys from dashboard

# Self-hosted
npm run build && npm start
```

## File Locations

All documentation files located at:

```
/Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude/skills/macos-resource-optimizer/.data/docs/
```

Key files:
- **Homepage**: `pages/index.mdx`
- **Theme**: `theme.config.tsx`
- **Config**: `next.config.js`, `package.json`, `tsconfig.json`
- **Content**: `pages/*/` directories

## Security

### No Secrets in Docs

Never commit:
- API keys
- Passwords
- Credentials
- Personal data

### SSL/HTTPS

- Vercel: Automatic
- GitHub Pages: Automatic
- Netlify: Automatic
- Self-hosted: Use Let's Encrypt

## Backup & Recovery

### Backup Documentation

```bash
# Backup entire docs directory
tar -czf docs-backup.tar.gz .claude/skills/macos-resource-optimizer/.data/docs/

# Store safely
# Restore with: tar -xzf docs-backup.tar.gz
```

## Next Steps

1. **Install dependencies**: `npm install`
2. **Test locally**: `npm run dev`
3. **Choose platform**: Vercel recommended
4. **Deploy**: Follow platform instructions
5. **Monitor**: Check analytics and performance
6. **Maintain**: Update content as needed

## Support

### Documentation Issues

- Fix broken links
- Update outdated info
- Add missing content
- Improve examples

### Performance Issues

- Optimize images
- Check build size
- Review bundle analysis
- Check server performance

### Deployment Issues

Check platform documentation:
- [Vercel Docs](https://vercel.com/docs)
- [Netlify Docs](https://docs.netlify.com)
- [GitHub Pages Docs](https://pages.github.com)

---

Documentation Version: 1.0.0
Last Updated: 2024-01-15
Ready for Deployment: Yes
