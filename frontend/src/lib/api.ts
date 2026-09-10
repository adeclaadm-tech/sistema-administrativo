/**
 * Cliente HTTP.
 *
 * La URL del backend llega por variable de entorno, así que el mismo build
 * apunta a Railway hoy y a un droplet mañana sin tocar código.
 */

const BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");
const LLAVE_TOKEN = "adecla.access_token";
const LLAVE_REFRESH = "adecla.refresh_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public errores?: { campo: string; mensaje: string }[],
    public causa?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const token = {
  get: () => localStorage.getItem(LLAVE_TOKEN),
  getRefresh: () => localStorage.getItem(LLAVE_REFRESH),
  set: (acceso: string, refresh: string) => {
    localStorage.setItem(LLAVE_TOKEN, acceso);
    localStorage.setItem(LLAVE_REFRESH, refresh);
  },
  clear: () => {
    localStorage.removeItem(LLAVE_TOKEN);
    localStorage.removeItem(LLAVE_REFRESH);
  },
};

type Opciones = Omit<RequestInit, "body"> & { body?: unknown; query?: Record<string, unknown> };

/** Traduce el fallo de red al error de configuración que casi siempre es. */
function mensajeDeRed(destino: string): string {
  const apuntaALocal = /^https?:\/\/(localhost|127\.0\.0\.1)/.test(destino);
  const paginaSegura = window.location.protocol === "https:";

  if (apuntaALocal && paginaSegura) {
    return (
      "Esta versión quedó apuntando a localhost. Define VITE_API_URL con la URL " +
      "del backend y vuelve a desplegar: Vite la incrusta al compilar, no al cargar."
    );
  }
  return (
    `No pudimos conectar con ${new URL(destino).origin}. Puede estar caído, o el ` +
    "dominio de esta página no está en CORS_ORIGINS del backend."
  );
}

function construirUrl(ruta: string, query?: Record<string, unknown>): string {
  const url = new URL(BASE + ruta, window.location.origin);
  if (query) {
    for (const [clave, valor] of Object.entries(query)) {
      if (valor !== undefined && valor !== null && valor !== "") {
        url.searchParams.set(clave, String(valor));
      }
    }
  }
  return url.toString();
}

async function ejecutar<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const { body, query, headers, ...resto } = opciones;
  const esFormData = body instanceof FormData;

  const destino = construirUrl(ruta, query);

  let respuesta: Response;
  try {
    respuesta = await fetch(destino, {
      ...resto,
      headers: {
        ...(esFormData ? {} : body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token.get() ? { Authorization: `Bearer ${token.get()}` } : {}),
        ...headers,
      },
      body: esFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (causa) {
    // El navegador no le cuenta a JavaScript por qué falló: CORS, DNS y
    // servidor caído llegan aquí como el mismo TypeError. Lo único que
    // podemos hacer es decir a dónde se estaba llamando, que es justo el dato
    // que hace falta para distinguirlos.
    throw new ApiError(0, mensajeDeRed(destino), undefined, causa);
  }

  if (respuesta.status === 401) {
    token.clear();
    // El guard de rutas se encarga de mandar al login; aquí solo cortamos.
    throw new ApiError(401, "Tu sesión expiró. Vuelve a entrar.");
  }

  if (!respuesta.ok) {
    let mensaje = "Algo falló del lado del servidor.";
    let errores;
    try {
      const datos = await respuesta.json();
      mensaje = datos.detail ?? mensaje;
      errores = datos.errores;
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new ApiError(respuesta.status, mensaje, errores);
  }

  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

export const api = {
  get: <T>(ruta: string, query?: Record<string, unknown>) => ejecutar<T>(ruta, { query }),
  post: <T>(ruta: string, body?: unknown) => ejecutar<T>(ruta, { method: "POST", body }),
  patch: <T>(ruta: string, body?: unknown) => ejecutar<T>(ruta, { method: "PATCH", body }),
  put: <T>(ruta: string, body?: unknown) => ejecutar<T>(ruta, { method: "PUT", body }),
  delete: <T>(ruta: string) => ejecutar<T>(ruta, { method: "DELETE" }),

  /** Descarga un archivo respetando el nombre que manda el backend. */
  async descargar(ruta: string, query?: Record<string, unknown>): Promise<void> {
    const respuesta = await fetch(construirUrl(ruta, query), {
      headers: token.get() ? { Authorization: `Bearer ${token.get()}` } : {},
    });
    if (!respuesta.ok) throw new ApiError(respuesta.status, "No se pudo generar el archivo.");

    const disposicion = respuesta.headers.get("Content-Disposition") ?? "";
    const nombre = /filename="?([^"]+)"?/.exec(disposicion)?.[1] ?? "adecla-reporte";
    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombre;
    enlace.click();
    URL.revokeObjectURL(url);
  },
};
