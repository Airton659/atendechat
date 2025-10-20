FROM node:20-alpine

WORKDIR /app

# Install git, ssh and other dependencies
RUN apk add --no-cache git openssh-client netcat-openbsd tzdata

# Set timezone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Remove package-lock.json to avoid conflicts with yarn
RUN rm -f package-lock.json

COPY backend/package*.json ./
COPY backend/yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

COPY backend/ .

# Configure git to use HTTPS instead of SSH
RUN git config --global url."https://".insteadOf ssh://

RUN yarn add fluent-ffmpeg @ffmpeg-installer/ffmpeg

# Create certs-temp directory
RUN mkdir -p ./certs-temp

# Copy certificates if exists (won't fail if doesn't exist due to context)
COPY backend/copy_cert_assets.sh ./
RUN chmod +x copy_cert_assets.sh

ARG STACK_NAME
ENV STACK_NAME=$STACK_NAME

# Run script (will skip if no certs)
RUN ./copy_cert_assets.sh || echo "No certificates to copy"

RUN rm -rf ./certs-temp

RUN yarn build

EXPOSE 3000

ENV HOST=0.0.0.0
ENV PORT=3000

# Make the entrypoint script executable
COPY backend/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"] 