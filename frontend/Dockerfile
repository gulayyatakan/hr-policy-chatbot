FROM node:22-alpine
WORKDIR /app

# For better SWC compatibility on Alpine
RUN apk add --no-cache libc6-compat

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_DISABLE_TURBOPACK=1 \
    HOSTNAME=0.0.0.0 \
    CHOKIDAR_USEPOLLING=1

EXPOSE 3000

# No backslash-newlines in the JSON string
CMD ["sh","-lc","test -f package.json || { echo 'ERROR: /app/package.json not found. Mount ./frontend -> /app in docker-compose.'; exit 1; }; if [ -f package-lock.json ]; then [ -x node_modules/.bin/next ] || npm ci; else [ -x node_modules/.bin/next ] || npm install; fi; exec npm run dev"]
