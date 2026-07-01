FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_API_FALLBACK_URL=
ARG VITE_SENTINELA_LOGIN_URL=/app
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_FALLBACK_URL=$VITE_API_FALLBACK_URL
ENV VITE_SENTINELA_LOGIN_URL=$VITE_SENTINELA_LOGIN_URL
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
