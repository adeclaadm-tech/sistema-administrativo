# Frontend en dos etapas: se compila con Node y se sirve como estático con nginx.
#
# Sirve igual en Railway (segundo servicio del proyecto, con Root Directory
# `frontend`) y en un droplet con docker compose.
FROM node:22-alpine AS build

WORKDIR /app

# Vite resuelve import.meta.env en tiempo de BUILD, no de ejecución: la URL del
# backend tiene que entrar como build arg. En Railway se define la variable del
# servicio y la pasa al build; si cambia, hay que redesplegar, no basta con
# guardarla.
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Falla temprano y con un mensaje claro si el bundle salió apuntando a
# localhost: si no, el error aparece en producción como un login que no hace
# nada y cuesta media hora encontrarlo.
RUN if grep -rq "localhost:8000" dist/assets/*.js; then \
      echo "ERROR: el bundle quedó apuntando a localhost. Define VITE_API_URL en el servicio antes de construir." >&2; \
      exit 1; \
    fi

FROM nginx:1.27-alpine AS runtime

# La imagen procesa las plantillas con envsubst al arrancar, así que el puerto
# se resuelve en tiempo de ejecución con el $PORT que inyecta Railway.
ENV PORT=80
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
