FROM node:18-alpine

WORKDIR /app

# Install dependencies for building
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package.json ./

# Copy lockfile if exists
COPY package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source code
COPY . .

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Set build-time environment variable
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the application
RUN npm run build

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
RUN chown -R nextjs:nodejs /app/.next

USER nextjs

# Expose port
EXPOSE 3000

# Set port environment variable
ENV PORT 3000

# Start the application
CMD ["npm", "start"]