/** Pantalla 1e: acceso restringido del staff. */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Boton, Campo, Logo } from "../../components/ui";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";

export default function LoginAdmin() {
  const { entrar } = useAuth();
  const navegar = useNavigate();
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function manejar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;
    setEnviando(true);
    setError(null);
    try {
      const usuario = await entrar(datos.identificador, datos.password);
      if (usuario.rol !== "admin") {
        setError("Esta cuenta es del portal de afiliados, no del panel.");
        return;
      }
      navegar("/admin", { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No pudimos conectar con el servidor.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-tinta px-6 py-14">
      <form onSubmit={manejar} className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex items-center gap-2">
          <Logo compacto invertido />
          <span className="rounded bg-hueso/15 px-1.5 py-0.5 font-mono text-[0.6rem] tracking-wider text-hueso">
            ADMIN
          </span>
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-mono text-[0.65rem] tracking-[0.1em] text-hueso/50 uppercase">
            Acceso restringido
          </span>
          <h1 className="font-heading text-3xl font-semibold text-hueso">Panel administrativo</h1>
        </div>

        <div className="flex flex-col gap-4 rounded-[14px] bg-superficie p-6">
          <Campo
            etiqueta="Correo institucional"
            name="identificador"
            type="email"
            autoComplete="username"
            placeholder="gestion@adecla.do"
            required
          />
          <Campo
            etiqueta="Contraseña"
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••••"
            required
          />

          {error ? (
            <p className="rounded-[10px] bg-vencido-suave px-4 py-3 text-sm text-vencido" role="alert">
              {error}
            </p>
          ) : null}

          <Boton type="submit" cargando={enviando} className="w-full py-3.5">
            Entrar
          </Boton>
        </div>

        <p className="text-center font-mono text-[0.62rem] tracking-[0.05em] text-hueso/40 uppercase">
          Sesión auditada · las cuentas del staff las crea un administrador
        </p>

        <Link to="/login" className="text-center text-xs text-hueso/50 hover:text-hueso">
          ← Volver al portal de afiliados
        </Link>
      </form>
    </div>
  );
}
