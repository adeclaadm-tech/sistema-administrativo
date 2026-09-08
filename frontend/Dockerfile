# Frontend en dos etapas: se compila con Node y se sirve como estático con nginx.
#
# Vercel no usa este archivo (compila desde el repo con `npm run build`); está
# para el día que todo se mude a un droplet con docker compose.
FROM node:22-alpine AS build

WORKDIR /app

# La URL del backend se hornea en el bundle: Vite resuelve import.meta.env en
# tiempo de build, así que tiene que llegar como argumento.
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
