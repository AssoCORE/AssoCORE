# Docker Images and GitHub Container Registry (GHCR)

## Overview

This project uses GitHub Actions to automatically build and publish Docker images to GitHub Container Registry (GHCR). Images are built for three main services:

- **Backend**: FastAPI application with uvicorn
- **Frontend**: Next.js application
- **Mobile**: Flutter APK builder

## Image Naming Convention

Images are published to GHCR with the following pattern:
```
ghcr.io/assocore/assocore/{service}:{tag}
```

Where `{service}` is one of: `backend`, `frontend`, `mobile`

## Available Tags

The workflow automatically creates the following tags:

### Branch-based tags
- `main` - Latest commit from main branch (also tagged as `latest`)
- `develop` - Latest commit from develop branch
- `CI-abc123` - Commit SHA on specific branch

### Pull Request tags
- `pr-123` - Built from PR #123

### Release tags (when pushing version tags)
- `v1.2.3` - Specific version
- `v1.2` - Minor version (latest patch)
- `v1` - Major version (latest minor)

## Triggering Builds

### Automatic triggers

1. **Push to main or develop branches**
   ```bash
   git push origin main
   ```
   → Builds and pushes images with branch name + `latest` (for main)

2. **Push a version tag**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   → Builds and pushes images with semantic version tags
   → Extracts and uploads APK as artifact

3. **Open/update a Pull Request**
   ```bash
   # Create PR via GitHub UI or gh CLI
   gh pr create
   ```
   → Builds images (doesn't push to registry, just validates)

## Using Pre-built Images

### Development (building locally)
```bash
docker compose up --build
```

### Production (using GHCR images)
```bash
# Pull latest images from GHCR
docker compose -f docker-compose.prod.yml pull

# Run with pre-built images
docker compose -f docker-compose.prod.yml up -d
```

### Pulling specific versions
```bash
# Pull a specific version
docker pull ghcr.io/assocore/assocore/backend:v1.2.3
docker pull ghcr.io/assocore/assocore/frontend:v1.2.3

# Pull from a specific branch
docker pull ghcr.io/assocore/assocore/backend:develop

# Pull latest (main branch)
docker pull ghcr.io/assocore/assocore/backend:latest
```

## Authentication

### For developers (pulling public images)
If images are public, no authentication is needed:
```bash
docker pull ghcr.io/assocore/assocore/backend:latest
```

### For CI/CD or private images
1. Create a Personal Access Token (PAT) with `read:packages` scope
2. Login to GHCR:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

3. Pull images:
   ```bash
   docker compose -f docker-compose.prod.yml pull
   ```

## Making Images Public

By default, GHCR images are private. To make them public:

1. Go to https://github.com/orgs/AssoCORE/packages
2. Select the package (backend, frontend, or mobile)
3. Click "Package settings"
4. Scroll to "Change visibility"
5. Select "Public"

## Build Cache

The workflow uses GitHub Actions cache to speed up builds:
- Dependencies are cached between builds
- Only changed layers are rebuilt
- Typical build time: 2-5 minutes (first build: 10-15 minutes)

## Troubleshooting

### Build fails with "permission denied"
- Check that GITHUB_TOKEN has `packages: write` permission
- Verify the workflow file has `permissions: packages: write`

### Image not found when pulling
- Ensure the image was pushed (check GitHub Actions logs)
- Verify you're using the correct image name and tag
- Check if the package is private (requires authentication)

### Build is slow
- First builds are slower (no cache)
- Subsequent builds use layer caching
- Ensure `.dockerignore` files are optimized

## Manual Workflow Dispatch

To manually trigger a build:
1. Go to Actions tab in GitHub
2. Select "Build and Push Docker Images"
3. Click "Run workflow"
4. Select branch and run

## APK Artifacts

When a version tag is pushed (e.g., `v1.0.0`), the mobile APK is:
1. Built inside the Docker image
2. Extracted from the container
3. Uploaded as a GitHub Actions artifact
4. Available for download for 90 days

To download the APK:
1. Go to the workflow run in Actions tab
2. Scroll to "Artifacts" section
3. Download `mobile-apk.zip`
