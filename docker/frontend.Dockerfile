# ==============================================================================
# DEVELOPMENT STAGE
# ==============================================================================
FROM node:20-alpine AS development
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Set environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Expose port
EXPOSE 3000

# Start development server with hot-reload
CMD ["sh", "-c", "pnpm install && pnpm dev"]

# ==============================================================================
# PRODUCTION STAGES
# ==============================================================================

# Stage 1: Dependencies
# Same base as the development and production stages: building on the image we
# actually run on keeps native modules on the same libc, and avoids depending on
# a moving nixos/nix channel.
FROM node:20-alpine AS deps
WORKDIR /app

RUN npm install -g pnpm

# Copy package files
COPY front/package.json front/pnpm-lock.yaml front/pnpm-workspace.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app

RUN npm install -g pnpm

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json
COPY --from=deps /app/pnpm-lock.yaml ./pnpm-lock.yaml

# Copy frontend source code
COPY front/ ./

# Build Next.js application for production
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# Stage 3: Production
FROM node:20-alpine AS production
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Switch to non-root user
USER nextjs

EXPOSE 3000

# Start Next.js production server
CMD ["node", "server.js"]
