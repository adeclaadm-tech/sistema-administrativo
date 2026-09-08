/** Pantalla 1g: tabla densa con búsqueda y filtros por estado. */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Boton, Cargando, EstadoBadge, Tabla, Tarjeta, Vacio } from "../../components/ui";
import { api } from "../../lib/api";
import { CATEGORIA, fechaCorta } from "../../lib/format";
import { useAuth } from "../../lib/auth";
import type { AfiliadoFila, Categoria, EstadoAfiliado, Metricas, Pagina } from "../../lib/types";

type Filtro = EstadoAfiliado | "todos";

export default function Afiliados() {
  const { puedeEscribir } = useAuth();
  const [pagina, setPagina] = useState<Pagina<AfiliadoFila> | null>(null);
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtro, setFiltro] = useState<Filtro>("todos");
  const [categoria, setCategoria] = useState<Categoria | "">("");
  const [page, setPage] = useState(1);

  const cargar = useCallback(() => {
    api
      .get<Pagina<AfiliadoFila>>("/afiliados", {
        q: busqueda || undefined,
        estado: filtro === "todos" ? undefined : filtro,
        categoria: categoria || undefined,
        page,
        per_page: 10,
      })
      .then(setPagina)
      .catch(() => setPagina(null));
  }, [busqueda, filtro, categoria, page]);

  useEffect(() => {
    const id = setTimeout(cargar, busqueda ? 250 : 0);
    return () => clearTimeout(id);
  }, [cargar, busqueda]);

  useEffect(() => {
    api.get<Metricas>("/reportes/dashboard").then(setMetricas).catch(() => setMetricas(null));
  }, []);

  const pestanas: { clave: Filtro; texto: string; total?: number }[] = [
    { clave: "todos", texto: "Todos", total: metricas?.total_afiliados },
    { clave: "activo", texto: "Activos", total: metricas?.activos },
    { clave: "pendiente", texto: "Pendientes", total: metricas?.pendientes },
    { clave: "vencido", texto: "Vencidos", total: metricas?.vencidos },
  ];

  const paginas = pagina ? Math.max(1, Math.ceil(pagina.total / pagina.per_page)) : 1;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">{pagina?.total ?? 0} registros</span>
          <h1 className="font-heading text-3xl font-semibold">Afiliados</h1>
        </div>
        <div className="flex gap-2">
          <Boton
            variante="contorno"
            onClick={() =>
              void api.descargar("/reportes/export", {
                formato: "xlsx",
                estado: filtro === "todos" ? undefined : filtro,
                categoria: categoria || undefined,
              })
            }
          >
            Exportar
          </Boton>
          {puedeEscribir ? <Boton>Nuevo afiliado</Boton> : null}
        </div>
      </header>

      <Tarjeta className="flex flex-col gap-4 p-5">
        <input
          className="campo"
          placeholder="Buscar por nombre, RNC o representante…"
          value={busqueda}
          onChange={(e) => {
            setBusqueda(e.target.value);
            setPage(1);
          }}
        />

        <div className="flex flex-wrap items-center gap-2">
          {pestanas.map((p) => (
            <button
              key={p.clave}
              onClick={() => {
                setFiltro(p.clave);
                setPage(1);
              }}
              className={`rounded-full px-3.5 py-1.5 text-xs font-semibold tracking-[0.06em] uppercase transition-colors ${
                filtro === p.clave
                  ? "bg-tinta text-hueso"
                  : "border border-borde text-tinta-suave hover:border-borde-fuerte"
              }`}
            >
              {p.texto}
              {p.total !== undefined ? ` · ${p.total}` : ""}
            </button>
          ))}

          <select
            className="ml-auto rounded-[8px] border border-borde bg-superficie px-3 py-1.5 text-xs tracking-[0.06em] text-tinta-suave uppercase"
            value={categoria}
            onChange={(e) => {
              setCategoria(e.target.value as Categoria | "");
              setPage(1);
            }}
          >
            <option value="">Categoría · todas</option>
            {(Object.keys(CATEGORIA) as Categoria[]).map((c) => (
              <option key={c} value={c}>
                {CATEGORIA[c]}
              </option>
            ))}
          </select>
        </div>
      </Tarjeta>

      {!pagina ? (
        <Cargando />
      ) : pagina.items.length === 0 ? (
        <Tarjeta>
          <Vacio titulo="Ningún afiliado coincide" detalle="Prueba con otro RNC o quita los filtros." />
        </Tarjeta>
      ) : (
        <>
          <Tabla encabezados={["Razón social", "RNC", "Representante", "Categoría", "Vence", "Estado", ""]}>
            {pagina.items.map((fila) => (
              <tr key={fila.id} className="border-b border-borde last:border-0 hover:bg-hueso">
                <td className="px-4 py-3 font-medium">{fila.nombre}</td>
                <td className="cifra px-4 py-3 font-mono text-xs text-tinta-suave">{fila.rnc_cedula}</td>
                <td className="px-4 py-3 text-tinta-suave">{fila.representante ?? "—"}</td>
                <td className="px-4 py-3 text-tinta-suave">{CATEGORIA[fila.categoria]}</td>
                <td className="cifra px-4 py-3 font-mono text-xs">{fechaCorta(fila.fecha_vencimiento)}</td>
                <td className="px-4 py-3">
                  <EstadoBadge estado={fila.estado} />
                </td>
                <td className="px-4 py-3 text-right">
                  <Link to={`/admin/afiliados/${fila.id}`} className="text-sm text-teal-boton hover:underline">
                    Ver ficha
                  </Link>
                </td>
              </tr>
            ))}
          </Tabla>

          <div className="flex items-center justify-between text-xs text-tinta-suave">
            <span className="cifra font-mono tracking-wide uppercase">
              {(pagina.page - 1) * pagina.per_page + 1}–
              {Math.min(pagina.page * pagina.per_page, pagina.total)} de {pagina.total}
            </span>
            <div className="flex items-center gap-2">
              <Boton variante="contorno" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Anterior
              </Boton>
              <span className="cifra font-mono">
                {pagina.page} / {paginas}
              </span>
              <Boton
                variante="contorno"
                disabled={page >= paginas}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Boton>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
