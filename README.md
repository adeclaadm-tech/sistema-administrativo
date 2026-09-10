# ADECLA · Sistema de afiliados

Sistema administrativo de la Asociación de Constructores de Punta Cana. Son dos
portales sobre un mismo backend:

- **Portal de afiliados** — el constructor consulta el estado de su afiliación,
  sube documentos, revisa pagos y descarga proformas.
- **Panel administrativo** — el staff gestiona la base de afiliados, revisa
  documentación, registra pagos y exporta reportes.

```
.
├── backend/          FastAPI + SQLAlchemy + Alembic
├── frontend/         React + Vite + Tailwind
└── docker-compose.yml
```

## Stack

| Pieza     | Tecnología                                              |
| --------- | ------------------------------------------------------- |
| API       | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic           |
| Base      | PostgreSQL — Neon, Supabase, Railway o un droplet propio |
| Storage   | Cualquier S3 vía boto3; Cloudflare R2 por defecto        |
| Auth      | JWT con dos roles y dos sub-roles de staff               |
| Frontend  | React 18, Vite 6, Tailwind CSS 4, React Router           |
| Contenedores | Dockerfile por servicio + compose para local          |

Nada de infraestructura está escrito en el código: base, storage, secretos y
CORS entran por variable de entorno. Mover el backend de Railway a un droplet de
DigitalOcean es copiar el `.env` y levantar el compose.

---

## Modelo de datos

```
Usuario ──1:1── Afiliado ──1:N── ContactoAfiliado   (contabilidad, marketing, comercial)
                    ├──1:N── Documento              (rnc_nid, cedula, soporte_pago, doc_representante)
                    ├──1:N── Pago ──1:1── Proforma
                    └──1:N── Proforma
```

- **Usuario** — `rol` es `afiliado` o `admin`. Dentro de admin, `sub_rol` separa
  al **administrador** (gestiona todo) del **consultor** (consulta y exporta,
  pero no aprueba documentos ni registra pagos).
- **Afiliado** — RNC único, categoría (clase A/B/C), estado (activo, pendiente,
  vencido), fechas de afiliación y vencimiento, cuota anual.
- **ContactoAfiliado** — una persona por área con nombre, cargo, teléfono y
  correo. Tabla aparte en lugar de doce columnas en la ficha: sumar un área
  nueva no obliga a migrar `afiliados`, y "todos los contactos de contabilidad"
  sale con un solo filtro.
- **Documento** — `archivo_url` guarda la llave del objeto en el bucket, nunca
  una ruta del disco del servidor.
- **Pago / Proforma** — la proforma se numera `PRF-<año>-<consecutivo>` dentro de
  la transacción del pago, para que dos cobros simultáneos no repitan número.

---

## Endpoints

Todo cuelga de `/api/v1`. La documentación viva queda en `/docs`.

### Auth

| Método | Ruta                    | Quién             |
| ------ | ----------------------- | ----------------- |
| POST   | `/auth/login`           | público — acepta RNC o correo |
| POST   | `/auth/token`           | público — variante OAuth2 para Swagger |
| POST   | `/auth/register`        | público — **solo afiliados**  |
| POST   | `/auth/refresh`         | con refresh token |
| GET    | `/auth/me`              | autenticado       |
| POST   | `/auth/cambiar-password`| autenticado       |

Las cuentas del panel no salen del registro abierto: las crea un administrador
desde `/usuarios`.

### Afiliados

| Método | Ruta                                     | Quién         |
| ------ | ---------------------------------------- | ------------- |
| GET    | `/afiliados/me`                          | afiliado      |
| PATCH  | `/afiliados/me`                          | afiliado      |
| GET    | `/afiliados`                             | staff — filtros por estado, categoría, búsqueda y vencimiento |
| POST   | `/afiliados`                             | administrador |
| GET    | `/afiliados/{id}`                        | staff         |
| PATCH  | `/afiliados/{id}`                        | administrador |
| DELETE | `/afiliados/{id}`                        | administrador |
| GET    | `/afiliados/{id}/contactos`              | staff         |
| PUT    | `/afiliados/{id}/contactos/{area}`       | administrador |
| DELETE | `/afiliados/{id}/contactos/{area}`       | administrador |

### Documentos

| Método | Ruta                            | Quién         |
| ------ | ------------------------------- | ------------- |
| GET    | `/documentos/me`                | afiliado      |
| POST   | `/documentos/me`                | afiliado — multipart, PDF/JPG/PNG hasta 10 MB |
| GET    | `/documentos/cola`              | staff         |
| GET    | `/documentos`                   | staff         |
| GET    | `/documentos/{id}`              | dueño o staff |
| POST   | `/documentos/{id}/revision`     | administrador — un rechazo exige motivo |
| DELETE | `/documentos/{id}`              | administrador |

### Pagos y proformas

| Método | Ruta                          | Quién         |
| ------ | ----------------------------- | ------------- |
| GET    | `/pagos/me`                   | afiliado      |
| GET    | `/pagos`                      | staff         |
| POST   | `/pagos/afiliado/{id}`        | administrador — emite proforma y opcionalmente renueva |
| PATCH  | `/pagos/{id}`                 | administrador |
| DELETE | `/pagos/{id}`                 | administrador |
| GET    | `/proformas/me`               | afiliado      |
| GET    | `/proformas`                  | staff         |
| POST   | `/proformas`                  | administrador |
| GET    | `/proformas/{id}/pdf`         | dueño o staff |

### Reportes

| Método | Ruta                   | Quién |
| ------ | ---------------------- | ----- |
| GET    | `/reportes/dashboard`  | staff |
| GET    | `/reportes/resumen`    | staff |
| GET    | `/reportes/export`     | staff — `formato=xlsx\|pdf`, filtros por tipo, rango, estado y categoría |

El Excel trae dos hojas: el padrón completo (con los tres contactos por área) y
un resumen por categoría. El PDF sale apaisado con la paleta institucional.

### Usuarios del staff

`GET`, `POST`, `PATCH` y `DELETE` sobre `/usuarios` — todo restringido al
administrador. La baja es lógica: los pagos y las revisiones guardan quién los
hizo.

---

## Desarrollo local

Requisitos: Docker y Docker Compose.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

Eso levanta cuatro servicios:

| Servicio  | URL                     | Para qué                          |
| --------- | ----------------------- | --------------------------------- |
| backend   | http://localhost:8000   | API + `/docs`                     |
| frontend  | http://localhost:5173   | los dos portales                  |
| db        | localhost:5432          | Postgres 16                       |
| storage   | http://localhost:9001   | MinIO — sustituye a R2 en local   |

Las migraciones corren solas al arrancar el backend. Para datos de prueba:

```bash
docker compose exec backend python -m app.scripts.seed
```

Deja ocho constructoras con documentos, pagos y contactos por área, y estas
cuentas:

| Cuenta | Clave | Entra a |
| --- | --- | --- |
| `gestion@adecla.do` | `adecla2026` | panel, como administrador |
| `consulta@adecla.do` | `adecla2026` | panel, como consultor (solo lectura) |
| `admin@constructora-bavaro.do` | `afiliado2026` | portal de afiliados |

El correo de cada constructora sale de su razón social; también se puede entrar
al portal con el RNC (`1-31-45678-9`).

### Sin Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

### Migraciones

```bash
# después de tocar un modelo
docker compose exec backend alembic revision --autogenerate -m "descripción corta"
docker compose exec backend alembic upgrade head

# volver atrás una revisión
docker compose exec backend alembic downgrade -1
```

---

## Despliegue

### Backend en Railway

1. **New Project → Deploy from GitHub repo**, y en Settings pon `backend` como
   *Root Directory*. Railway detecta el `Dockerfile` y el `railway.json`.
2. Agrega un **Postgres** al proyecto. También sirve una base de Neon: es la
   misma URL y el código no distingue. El Postgres de Railway ahorra un
   proveedor y viaja por la red privada del proyecto; Neon conviene si quieres
   la base fuera de Railway desde el día uno.
3. Variables del servicio:

   | Variable | Valor |
   | --- | --- |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` si usas el Postgres de Railway; si no, pega la de Neon |
   | `JWT_SECRET` | `openssl rand -hex 32` — uno nuevo, no el de desarrollo |
   | `CORS_ORIGINS` | el dominio de Vercel, y después el propio: `https://adecla-afiliados.vercel.app,https://afiliados.adecla.do` |
   | `APP_ENV` | `production` |
   | `DEBUG` | `false` |
   | `S3_*` | ver **Storage**; se pueden dejar vacías al principio |

   `PORT` la inyecta Railway; no la definas a mano.

4. El start command ya corre `alembic upgrade head` antes de servir, así que
   cada deploy migra la base. El health check apunta a `/health`.
5. **Settings → Networking → Generate Domain** para tener la URL pública.
6. Crea el primer administrador, una sola vez, desde la consola del servicio:

   ```bash
   python -m app.scripts.crear_admin --email gestion@adecla.do --password "<clave larga>" --nombre "Laura Méndez"
   ```

   Hace falta porque el registro abierto solo da de alta afiliados y `/usuarios`
   exige una sesión de administrador: en una base recién migrada, sin esto no
   hay manera de entrar al panel. El comando no pisa una cuenta existente, así
   que correrlo dos veces es inofensivo. Agrega `--consultor` para crear una
   cuenta de solo lectura.

   **No corras el seed en producción**: crea ocho constructoras de mentira.
7. Carga el padrón real de afiliados, también una sola vez:

   ```bash
   python -m app.scripts.importar_padron
   ```

   Son las 51 empresas del listado que mantiene ADECLA, las mismas que usa el
   sistema de inscripciones al torneo. Trae nombre, tipo de afiliación,
   persona de contacto, teléfono y correo.

   Lo que **no** trae, porque no está en el origen: RNC, fechas de afiliación
   y vencimiento, y montos de cuota. Quedan vacíos a propósito; se completan
   desde `Editar ficha` en cada afiliado. Rellenarlos con valores inventados
   haría imposible distinguir después un dato real de uno de relleno.

   Es idempotente: reconoce las empresas por nombre y actualiza en vez de
   duplicar, así que se puede volver a correr cuando el listado cambie. Con
   `--vence 2026-12-31` les pone a todas la misma fecha de vencimiento.

### Frontend en Vercel

1. **Add New → Project**, importa el repositorio y pon `frontend` como *Root
   Directory*. El `vercel.json` de esa carpeta ya trae el framework, el build y
   el rewrite que necesita React Router para que `/admin/afiliados/<id>` no
   devuelva 404 al recargar.
2. Variable de entorno: `VITE_API_URL = https://<backend>.up.railway.app/api/v1`,
   con `/api/v1` al final.
3. Deploy, y copia el dominio que te asigna.
4. Vuelve al servicio del backend en Railway y pon ese dominio en
   `CORS_ORIGINS`. Sin este paso el login parece "no hacer nada": el error solo
   aparece en la consola del navegador.

**`VITE_API_URL` se hornea en el bundle.** Vite resuelve `import.meta.env` al
compilar, no al ejecutar: si la cambias, hay que volver a desplegar en Vercel;
guardarla no basta. Es el motivo por el que el orden es backend primero,
frontend después.

El `Dockerfile` de `frontend/` no lo usa Vercel. Está para el día que todo se
mude a un droplet: sirve el build con nginx, escucha en `${PORT}` y aborta el
build si el bundle quedó apuntando a `localhost`.

### Storage de documentos

Cloudflare R2 pide una tarjeta aunque uses la capa gratis. Mientras tanto el
sistema despliega y funciona sin storage: afiliados, pagos, proformas y reportes
no lo tocan. Lo único que queda fuera de servicio es subir y ver documentos, que
responde 503 hasta que existan las llaves.

Cuando tengas la cuenta, crea el bucket `adecla-documentos` y un API token con
lectura y escritura, y llena `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`,
`S3_SECRET_ACCESS_KEY` y `S3_BUCKET`. Deja `S3_PUBLIC_BASE_URL` vacío para que
el bucket siga privado: el backend firma URLs de una hora cuando hay que mostrar
un archivo. No hace falta redesplegar el backend, solo reiniciarlo.

Cualquier proveedor S3 sirve sin tocar código, únicamente cambiando el endpoint:
Backblaze B2, Spaces de DigitalOcean o el storage de Supabase, que expone llaves
compatibles con S3 y no pide tarjeta.

### Migración futura a un droplet de DigitalOcean

Es la razón por la que todo está containerizado. En el droplet:

```bash
git clone <repo> && cd "Sistema administrativo ADECLA"
cp backend/.env.example backend/.env   # DATABASE_URL apuntando al Postgres del droplet
docker compose -f docker-compose.yml up -d --build
```

Lo único que cambia son las variables de entorno: `DATABASE_URL`, las llaves de
S3 (R2 sigue funcionando desde ahí, o se cambia a Spaces con otro endpoint) y
`CORS_ORIGINS`. El código no se toca.

---

## Sistema visual

La colorimetría viene del MVP de inscripciones al torneo, que a su vez sale del
brand book de ADECLA:

| Rol | Color |
| --- | --- |
| Acento de marca | Teal oficial `#00a99d` |
| Botones y CTA | Teal profundo `#00776d` (el oficial no da contraste AA con texto blanco) |
| Fondo | Blanco hueso `#fcfcf7` |
| Texto | Tinta `#233738`, nunca negro plano |
| Bordes | Gris claro `#e9e9e9` |
| Errores y vencidos | Terracota `#c4432a` |
| Acento cálido | Oro `#b0832f` — nombra el ciclo, nunca acciona |

Tipografía: **Fraunces** en titulares, **Public Sans** en formularios y tablas,
**IBM Plex Mono** para RNC, montos y números de proforma. Los tokens viven en
`frontend/src/styles/globals.css`.

Cuatro reglas que sostienen el sistema:

- El teal es acento, no fondo: no pasa del 10% de la pantalla.
- Todo texto oscuro pasa por la Tinta; nada de negro puro.
- Las tarjetas son planas en reposo; la sombra se gana con hover o foco.
- Montos y RNC siempre en cifra tabular, para que las columnas alineen.
