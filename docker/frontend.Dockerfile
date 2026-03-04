# Stage 1: Dependencies
FROM nixos/nix:latest AS deps
WORKDIR /app

# Enable flakes and configure Nix
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Install Node.js 20, pnpm, and required tools via Nix
RUN nix-env -iA nixpkgs.nodejs_20 nixpkgs.pnpm nixpkgs.gnused nixpkgs.coreutils

# Copy package files
COPY front/package.json front/pnpm-lock.yaml front/pnpm-workspace.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Stage 2: Build
FROM nixos/nix:latest AS builder
WORKDIR /app

# Enable flakes and configure Nix
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Install Node.js 20, pnpm, and required tools via Nix
RUN nix-env -iA nixpkgs.nodejs_20 nixpkgs.pnpm nixpkgs.gnused nixpkgs.coreutils

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
FROM node:20-alpine AS runner
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
