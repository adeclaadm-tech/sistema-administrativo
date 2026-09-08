/** Panel administrativo: barra lateral fija, densidad alta, orientado a datos. */

import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Logo } from "../components/ui";
import { useAuth } from "../lib/auth";

const GESTION = [
  { a: "/admin", texto: "Dashboard", exacta: true },
  { a: "/admin/afiliados", texto: "Afiliados" },
  { a: "/admin/documentos", texto: "Documentos por revisar" },
  { a: "/admin/pagos", texto: "Pagos" },
  { a: "/admin/reportes", texto: "Reportes" },
];

const CONFIGURACION = [{ a: "/admin/usuarios", texto: "Usuarios del staff" }];

function Grupo({ titulo, rutas }: { titulo: string; rutas: typeof GESTION }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="etiqueta px-3 pt-5 pb-2">{titulo}</span>
      {rutas.map((ruta) => (
        <NavLink
          key={ruta.a}
          to={ruta.a}
          end={ruta.exacta}
          className={({ isActive }) =>
            `rounded-[8px] px-3 py-2 text-sm transition-colors ${
              isActive
                ? "bg-teal-suave font-semibold text-teal-boton"
                : "text-tinta-suave hover:bg-borde/50 hover:text-tinta"
            }`
          }
        >
          {ruta.texto}
        </NavLink>
      ))}
    </div>
  );
}

export default function AdminLayout() {
  const { usuario, salir, puedeEscribir } = useAuth();
  const navegar = useNavigate();

  const iniciales = (usuario?.nombre ?? "??")
    .split(" ")
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen bg-hueso lg:grid lg:grid-cols-[248px_1fr]">
      <aside className="flex flex-col border-b border-borde bg-superficie px-4 py-5 lg:sticky lg:top-0 lg:h-screen lg:border-r lg:border-b-0">
        <div className="flex items-center gap-2 px-2">
          <Logo compacto />
          <span className="rounded bg-tinta px-1.5 py-0.5 font-mono text-[0.6rem] tracking-wider text-hueso">
            ADMIN
          </span>
        </div>

        <nav className="flex flex-1 flex-col">
          <Grupo titulo="Gestión" rutas={GESTION} />
          {puedeEscribir ? <Grupo titulo="Configuración" rutas={CONFIGURACION} /> : null}
        </nav>

        <div className="mt-6 flex items-center gap-3 border-t border-borde pt-4">
          <span className="grid h-8 w-8 place-items-center rounded-full bg-teal-suave font-mono text-xs text-teal-boton">
            {iniciales}
          </span>
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-sm font-semibold text-tinta">{usuario?.nombre}</span>
            <span className="text-xs text-tinta-tenue capitalize">{usuario?.sub_rol ?? "staff"}</span>
          </div>
          <button
            onClick={() => {
              salir();
              navegar("/admin/login");
            }}
            className="text-xs text-tinta-suave transition-colors hover:text-tinta"
          >
            Salir
          </button>
        </div>
      </aside>

      <main className="min-w-0 px-6 py-8 lg:px-10">
        <Outlet />
      </main>
    </div>
  );
}
