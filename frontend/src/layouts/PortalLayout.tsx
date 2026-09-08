/** Portal del afiliado: navegación horizontal, espaciosa, poco técnica. */

import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Logo } from "../components/ui";
import { useAuth } from "../lib/auth";

const RUTAS = [
  { a: "/portal", texto: "Inicio", exacta: true },
  { a: "/portal/documentos", texto: "Documentos" },
  { a: "/portal/pagos", texto: "Pagos" },
  { a: "/portal/perfil", texto: "Mi perfil" },
];

export default function PortalLayout() {
  const { usuario, salir } = useAuth();
  const navegar = useNavigate();

  const iniciales = (usuario?.nombre ?? "??")
    .split(" ")
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen bg-hueso">
      <header className="border-b border-borde bg-superficie">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-6">
          <div className="flex items-center gap-10">
            <Logo compacto />
            <nav className="hidden gap-7 text-sm md:flex">
              {RUTAS.map((ruta) => (
                <NavLink
                  key={ruta.a}
                  to={ruta.a}
                  end={ruta.exacta}
                  className={({ isActive }) =>
                    isActive
                      ? "border-b-2 border-teal pb-1 font-semibold text-tinta"
                      : "pb-1 text-tinta-suave transition-colors hover:text-tinta"
                  }
                >
                  {ruta.texto}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-tinta-suave sm:inline">{usuario?.nombre}</span>
            <span className="grid h-8 w-8 place-items-center rounded-full bg-teal-suave font-mono text-xs text-teal-boton">
              {iniciales}
            </span>
            <button
              onClick={() => {
                salir();
                navegar("/login");
              }}
              className="text-sm text-tinta-suave transition-colors hover:text-tinta"
            >
              Salir
            </button>
          </div>
        </div>

        <nav className="flex gap-5 overflow-x-auto border-t border-borde px-6 py-2 text-sm md:hidden">
          {RUTAS.map((ruta) => (
            <NavLink
              key={ruta.a}
              to={ruta.a}
              end={ruta.exacta}
              className={({ isActive }) =>
                isActive ? "font-semibold whitespace-nowrap text-teal-boton" : "whitespace-nowrap text-tinta-suave"
              }
            >
              {ruta.texto}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        <Outlet />
      </main>

      <footer className="mx-auto max-w-6xl px-6 pb-10 text-xs text-tinta-tenue">
        Asociación de Constructores · Punta Cana, República Dominicana
      </footer>
    </div>
  );
}
