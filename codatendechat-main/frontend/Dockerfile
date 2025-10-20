FROM node:20-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

COPY frontend/package*.json ./
COPY frontend/yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

COPY frontend/ .

RUN rm -f .env 

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

ARG REACT_APP_HOURS_CLOSE_TICKETS_AUTO
ENV REACT_APP_HOURS_CLOSE_TICKETS_AUTO=$REACT_APP_HOURS_CLOSE_TICKETS_AUTO

ARG STACK_NAME
ENV STACK_NAME=$STACK_NAME

ARG REACT_APP_COLOR
ENV REACT_APP_COLOR=$REACT_APP_COLOR

ARG REACT_APP_TAB_NAME
ENV REACT_APP_TAB_NAME=$REACT_APP_TAB_NAME

# Run brand assets script if exists (usando sh ao invés de bash)
RUN if [ -f copy_brand_assets.sh ]; then chmod +x copy_brand_assets.sh && sh copy_brand_assets.sh; else echo "No brands script"; fi

# Executa scripts de customização se existirem (usando sh ao invés de bash)
RUN if [ -f update_tab_name.sh ]; then chmod +x update_tab_name.sh && sh update_tab_name.sh; else echo "No tab name script"; fi
RUN if [ -f update_app_color.sh ]; then chmod +x update_app_color.sh && sh update_app_color.sh; else echo "No color script"; fi

# Build the application
RUN yarn build

EXPOSE 3001

ENV HOST=0.0.0.0
ENV PORT=3001

# Serve the built application
CMD ["serve", "-s", "build", "-l", "3001"] 