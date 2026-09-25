# Multi-stage build for frontend
FROM oven/bun:1-alpine AS builder

WORKDIR /app

# Copy package.json and lockfile
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen ./

# Copy source code
COPY . ./

# Build with VITE_API_BASE_URL as build arg
ARG VITE_API_BASE_URL
RUN VITE_API_BASE_URL=$VITE_API_BASE_URL bun run build

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