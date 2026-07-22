FROM node:22-bookworm AS build

WORKDIR /app

ARG VITE_APP_NAME
ARG VITE_APP_SHORT_NAME
ARG VITE_APP_TAGLINE
ARG VITE_APP_DESCRIPTION
ARG VITE_APP_CONTACT_EMAIL
ARG VITE_APP_LOGO_PATH
ARG VITE_DEFAULT_LOCALE
ARG VITE_NAVIGATION_TITLE
ARG VITE_TAB_OVERVIEW
ARG VITE_TAB_DONORS
ARG VITE_TAB_DONATIONS
ARG VITE_TAB_DONATION_TYPES
ARG VITE_TAB_WAREHOUSE
ARG VITE_TAB_CASES
ARG VITE_TAB_CUSTODY
ARG VITE_TAB_APPROVALS
ARG VITE_TAB_REPORTS
ARG VITE_TAB_SCHEDULED_REPORTS
ARG VITE_TAB_USERS
ARG VITE_TAB_SETTINGS
ARG VITE_COLOR_PRIMARY
ARG VITE_COLOR_PRIMARY_DARK
ARG VITE_COLOR_ACCENT
ARG VITE_COLOR_SIDEBAR
ARG VITE_COLOR_BACKGROUND
ARG VITE_COLOR_SURFACE
ARG VITE_COLOR_TEXT
ARG VITE_COLOR_MUTED_TEXT
ARG VITE_COLOR_SUCCESS
ARG VITE_COLOR_WARNING
ARG VITE_COLOR_DANGER

ENV VITE_APP_NAME=$VITE_APP_NAME \
    VITE_APP_SHORT_NAME=$VITE_APP_SHORT_NAME \
    VITE_APP_TAGLINE=$VITE_APP_TAGLINE \
    VITE_APP_DESCRIPTION=$VITE_APP_DESCRIPTION \
    VITE_APP_CONTACT_EMAIL=$VITE_APP_CONTACT_EMAIL \
    VITE_APP_LOGO_PATH=$VITE_APP_LOGO_PATH \
    VITE_DEFAULT_LOCALE=$VITE_DEFAULT_LOCALE \
    VITE_NAVIGATION_TITLE=$VITE_NAVIGATION_TITLE \
    VITE_TAB_OVERVIEW=$VITE_TAB_OVERVIEW \
    VITE_TAB_DONORS=$VITE_TAB_DONORS \
    VITE_TAB_DONATIONS=$VITE_TAB_DONATIONS \
    VITE_TAB_DONATION_TYPES=$VITE_TAB_DONATION_TYPES \
    VITE_TAB_WAREHOUSE=$VITE_TAB_WAREHOUSE \
    VITE_TAB_CASES=$VITE_TAB_CASES \
    VITE_TAB_CUSTODY=$VITE_TAB_CUSTODY \
    VITE_TAB_APPROVALS=$VITE_TAB_APPROVALS \
    VITE_TAB_REPORTS=$VITE_TAB_REPORTS \
    VITE_TAB_SCHEDULED_REPORTS=$VITE_TAB_SCHEDULED_REPORTS \
    VITE_TAB_USERS=$VITE_TAB_USERS \
    VITE_TAB_SETTINGS=$VITE_TAB_SETTINGS \
    VITE_COLOR_PRIMARY=$VITE_COLOR_PRIMARY \
    VITE_COLOR_PRIMARY_DARK=$VITE_COLOR_PRIMARY_DARK \
    VITE_COLOR_ACCENT=$VITE_COLOR_ACCENT \
    VITE_COLOR_SIDEBAR=$VITE_COLOR_SIDEBAR \
    VITE_COLOR_BACKGROUND=$VITE_COLOR_BACKGROUND \
    VITE_COLOR_SURFACE=$VITE_COLOR_SURFACE \
    VITE_COLOR_TEXT=$VITE_COLOR_TEXT \
    VITE_COLOR_MUTED_TEXT=$VITE_COLOR_MUTED_TEXT \
    VITE_COLOR_SUCCESS=$VITE_COLOR_SUCCESS \
    VITE_COLOR_WARNING=$VITE_COLOR_WARNING \
    VITE_COLOR_DANGER=$VITE_COLOR_DANGER

# 🔥 FIX: Install network tools
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 🔥 FIX: Configure npm
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-timeout 180000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set strict-ssl true && \
    npm config set cache /tmp/npm-cache

# 🔥 FIX: Network diagnostics
RUN echo "=== Network Diagnostics ===" && \
    echo "Testing DNS resolution..." && \
    nslookup registry.npmjs.org || echo "DNS lookup failed" && \
    echo "Testing connectivity..." && \
    curl -I --max-time 10 https://registry.npmjs.org/ || echo "Connection check failed" && \
    echo "=== End Diagnostics ==="

COPY package*.json ./

# 🔥 FIX: Install with retry logic
RUN set -ex; \
    for attempt in 1 2 3 4 5; do \
        echo "=== Attempt $attempt to install dependencies ==="; \
        if npm ci --network-timeout=180000 --cache /tmp/npm-cache; then \
            echo "✅ Installation succeeded on attempt $attempt!"; \
            break; \
        else \
            echo "❌ Attempt $attempt failed"; \
            if [ $attempt -eq 5 ]; then \
                echo "⚠️ All ci attempts failed. Trying with npm install..."; \
                npm install --network-timeout=180000 --cache /tmp/npm-cache; \
                if [ $? -eq 0 ]; then \
                    echo "✅ npm install succeeded!"; \
                else \
                    echo "❌ npm install also failed. Build will fail."; \
                    exit 1; \
                fi; \
            else \
                echo "Retrying in 10 seconds..."; \
                sleep 10; \
            fi; \
        fi; \
    done

COPY . .

RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]