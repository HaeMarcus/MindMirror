FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm with npm China mirror
RUN npm config set registry https://registry.npmmirror.com \
    && corepack enable && corepack prepare pnpm@10.14.0 --activate

# Install dependencies using China mirror
COPY package.json pnpm-lock.yaml ./
RUN pnpm config set registry https://registry.npmmirror.com \
    && echo 'ignore-build-scripts=false' > .npmrc \
    && pnpm install --frozen-lockfile

# Copy source and build
COPY . .

ENV BACKEND_URL=http://backend:8000
RUN pnpm build

# --- Production stage ---
FROM node:22-alpine AS runner

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.14.0 --activate

# Copy built output and dependencies
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000/').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"

CMD ["node", "server.js"]
