import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Navigate, useLocation } from "react-router-dom";

import { api, token } from "./api";
import type { Sesion, Usuario } from "./types";

interface EstadoAuth {
  usuario: Usuario | null;
  afiliadoId: string | null;
  cargando: boolean;
  entrar: (identificador: string, password: string) => Promise<Usuario>;
  registrar: (datos: Record<string, unknown>) => Promise<Usuario>;
  salir: () => void;
  esAdmin: boolean;
  puedeEscribir: boolean;
}

const AuthContext = createContext<EstadoAuth | null>(null);
const LLAVE_AFILIADO = "adecla.afiliado_id";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [afiliadoId, setAfiliadoId] = useState<string | null>(
    localStorage.getItem(LLAVE_AFILIADO),
  );
  const [cargando, setCargando] = useState(true);

  // Al recargar la página el token sigue en localStorage: se revalida contra
  // /auth/me antes de dar por buena la sesión.
  useEffect(() => {
    if (!token.get()) {
      setCargando(false);
      return;
    }
    api
      .get<Usuario>("/auth/me")
      .then(setUsuario)
      .catch(() => {
        token.clear();
        setUsuario(null);
      })
      .finally(() => setCargando(false));
  }, []);

  const guardar = useCallback((sesion: Sesion) => {
    token.set(sesion.access_token, sesion.refresh_token);
    setUsuario(sesion.usuario);
    setAfiliadoId(sesion.afiliado_id);
    if (sesion.afiliado_id) localStorage.setItem(LLAVE_AFILIADO, sesion.afiliado_id);
    return sesion.usuario;
  }, []);

  const entrar = useCallback(
    async (identificador: string, password: string) =>
      guardar(await api.post<Sesion>("/auth/login", { identificador, password })),
    [guardar],
  );

  const registrar = useCallback(
    async (datos: Record<string, unknown>) =>
      guardar(await api.post<Sesion>("/auth/register", datos)),
    [guardar],
  );

  const salir = useCallback(() => {
    token.clear();
    localStorage.removeItem(LLAVE_AFILIADO);
    setUsuario(null);
    setAfiliadoId(null);
  }, []);

  const valor = useMemo<EstadoAuth>(
    () => ({
      usuario,
      afiliadoId,
      cargando,
      entrar,
      registrar,
      salir,
      esAdmin: usuario?.rol === "admin",
      puedeEscribir: usuario?.rol === "admin" && usuario.sub_rol === "administrador",
    }),
    [usuario, afiliadoId, cargando, entrar, registrar, salir],
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth(): EstadoAuth {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth necesita estar dentro de <AuthProvider>.");
  return ctx;
}

/** Guard de rutas: manda al login del portal que corresponda. */
export function Protegida({ rol, children }: { rol: "afiliado" | "admin"; children: ReactNode }) {
  const { usuario, cargando } = useAuth();
  const location = useLocation();

  if (cargando) {
    return (
      <div className="flex min-h-screen items-center justify-center text-tinta-tenue">
        Cargando…
      </div>
    );
  }
  if (!usuario) {
    return <Navigate to={rol === "admin" ? "/admin/login" : "/login"} state={{ from: location }} replace />;
  }
  if (usuario.rol !== rol) {
    return <Navigate to={usuario.rol === "admin" ? "/admin" : "/portal"} replace />;
  }
  return <>{children}</>;
}
