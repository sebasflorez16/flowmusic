# Dockerfile de producción para un frontend estático (Vite + React).
#
# Construye la SPA con Vite (inyectando VITE_API_URL/VITE_WS_URL como build args)
# y sirve los estáticos con nginx con fallback SPA. Los build args se definen en
# el dashboard de Railway al crear el servicio.
#
#   VITE_API_URL  -> https://<backend>.up.railway.app/api/v1
#   VITE_WS_URL   -> wss://<backend>.up.railway.app/ws

FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_API_URL
ARG VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL \
    VITE_WS_URL=$VITE_WS_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
