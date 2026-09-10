/** Pantalla 1a: login y registro del constructor, en dos paneles. */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Boton, Campo } from "../../components/ui";
import Logo from "../../components/Logo";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type Pestana = "entrar" | "registrarme";

export default function Login() {
  const { entrar, registrar } = useAuth();
  const navegar = useNavigate();

  const [pestana, setPestana] = useState<Pestana>("entrar");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function manejar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;
    setEnviando(true);
    setError(null);
    try {
      if (pestana === "entrar") {
        await entrar(datos.identificador, datos.password);
      } else {
        await registrar(datos);
      }
      navegar("/portal", { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No pudimos conectar con el servidor.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <aside className="flex flex-col justify-between gap-12 bg-tinta px-10 py-14 text-hueso lg:px-14">
        <Logo tamano="grande" sobreFondoOscuro />

        <div className="flex flex-col gap-5">
          <h1 className="font-heading text-5xl leading-[1.02] text-hueso">
            Portal de
            <br />
            afiliados
          </h1>
          <p className="max-w-sm text-[0.98rem] leading-relaxed text-hueso/70">
            Consulta el estado de tu afiliación, sube tus documentos y descarga tus proformas de
            pago.
          </p>
        </div>

        <div className="flex flex-col gap-1.5 font-mono text-[0.65rem] tracking-[0.05em] text-hueso/50">
          <span>ASOCIACIÓN DE DESARROLLADORES</span>
          <span>Y CONSTRUCTORES DE LA ALTAGRACIA</span>
        </div>
      </aside>

      <main className="flex items-center justify-center px-6 py-14 lg:px-14">
        <form onSubmit={manejar} className="flex w-full max-w-md flex-col gap-6">
          <div className="flex w-fit gap-1 rounded-[9px] border border-borde bg-hueso p-1">
            {(["entrar", "registrarme"] as Pestana[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => {
                  setPestana(p);
                  setError(null);
                }}
                className={`rounded-md px-4 py-1.5 text-sm transition-colors ${
                  pestana === p
                    ? "bg-superficie font-semibold text-tinta shadow-sm"
                    : "text-tinta-suave"
                }`}
              >
                {p === "entrar" ? "Iniciar sesión" : "Registrarme"}
              </button>
            ))}
          </div>

          {pestana === "entrar" ? (
            <>
              <Campo
                etiqueta="Correo, usuario o RNC"
                name="identificador"
                autoComplete="username"
                placeholder="tu@empresa.do"
                ayuda="También sirve tu nombre de usuario o el RNC de la empresa."
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
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-tinta-suave">
                  <input type="checkbox" name="recordarme" className="accent-teal-boton" />
                  Recordarme
                </label>
                <Link to="/recuperar" className="text-teal-boton hover:underline">
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>
            </>
          ) : (
            <>
              <Campo etiqueta="Razón social" name="nombre_empresa" placeholder="Constructora Bávaro SRL" required />
              <Campo etiqueta="RNC / Cédula" name="rnc_cedula" placeholder="1-31-45678-9" required />
              <Campo etiqueta="Representante" name="representante" placeholder="Julio Morales" required />
              <Campo etiqueta="Correo" name="email" type="email" autoComplete="email" required />
              <Campo
                etiqueta="Nombre de usuario"
                name="usuario"
                placeholder="constructora-bavaro"
                pattern="[a-zA-Z0-9._-]+"
                minLength={3}
                ayuda="Opcional. Te sirve para entrar sin escribir el correo."
              />
              <Campo etiqueta="Teléfono" name="telefono" placeholder="809-552-0114" />
              <Campo
                etiqueta="Contraseña"
                name="password"
                type="password"
                autoComplete="new-password"
                ayuda="Mínimo 8 caracteres."
                minLength={8}
                required
              />
            </>
          )}

          {error ? (
            <p className="rounded-[10px] bg-vencido-suave px-4 py-3 text-sm text-vencido" role="alert">
              {error}
            </p>
          ) : null}

          <Boton type="submit" cargando={enviando} className="w-full py-3.5">
            {pestana === "entrar" ? "Entrar" : "Crear mi cuenta"}
          </Boton>

          <p className="text-xs leading-relaxed text-tinta-tenue">
            ¿Primera vez? El registro requiere RNC, cédula del representante y soporte de pago de la
            cuota anual. Tu afiliación queda pendiente hasta que el equipo revise los documentos.
          </p>

          <Link to="/admin/login" className="text-xs text-tinta-tenue hover:text-tinta">
            ¿Eres del staff de ADECLA? Entra al panel administrativo →
          </Link>
        </form>
      </main>
    </div>
  );
}
