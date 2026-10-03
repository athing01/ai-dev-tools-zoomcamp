# Multi-stage build for frontend
FROM oven/bun:1-alpine AS builder

WORKDIR /app

# Copy package.json and lockfile
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen ./

# Copy source code
COPY . ./

# Build environment-neutral frontend artifact
RUN bun run build

# Runtime stage
FROM oven/bun:1-alpine AS runtime

WORKDIR /app

# Copy built assets from builder
COPY --from=builder --chown=appuser:appuser /app/.output ./.output

# Set non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Run the Nitro server entry
CMD ["node", ".output/server/index.mjs"]
