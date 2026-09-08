/** Pantalla 1i: resumen del período, barras por mes y exportación. */

import { useEffect, useMemo, useState } from "react";

import { Boton, Cargando, Metrica, Tabla, Tarjeta } from "../../components/ui";
import { api } from "../../lib/api";
import { CATEGORIA, money, moneyCorto } from "../../lib/format";
import type { Categoria, EstadoAfiliado, ReporteResumen } from "../../lib/types";

const TIPOS = [
  { clave: "afiliaciones", texto: "Afiliaciones" },
  { clave: "recaudacion", texto: "Recaudación" },
  { clave: "vencimientos", texto: "Vencimientos" },
  { clave: "documentos", texto: "Documentos" },
] as const;

const SERIES = [
  { clave: "activos", texto: "Activos", clase: "bg-activo" },
  { clave: "pendientes", texto: "Pendientes", clase: "bg-pendiente" },
  { clave: "vencidos", texto: "Vencidos", clase: "bg-vencido" },
] as const;

export default function Reportes() {
  const anio = new Date().getFullYear();

  const [tipo, setTipo] = useState<(typeof TIPOS)[number]["clave"]>("afiliaciones");
  const [desde, setDesde] = useState(`${anio}-01-01`);
  const [hasta, setHasta] = useState(new Date().toISOString().slice(0, 10));
  const [categoria, setCategoria] = useState<Categoria | "">("");
  const [estado, setEstado] = useState<EstadoAfiliado | "">("");
  const [datos, setDatos] = useState<ReporteResumen | null>(null);

  useEffect(() => {
    api
      .get<ReporteResumen>("/reportes/resumen", {
        tipo,
        desde,
        hasta,
        categoria: categoria || undefined,
        estado: estado || undefined,
      })
      .then(setDatos)
      .catch(() => setDatos(null));
  }, [tipo, desde, hasta, categoria, estado]);

  const alturaMaxima = useMemo(() => {
    if (!datos) return 1;
    return Math.max(
      1,
      ...datos.por_mes.map((m) => m.activos + m.pendientes + m.vencidos),
    );
  }, [datos]);

  function exportar(formato: "xlsx" | "pdf") {
    void api.descargar("/reportes/export", {
      formato,
      tipo,
      desde,
      hasta,
      categoria: categoria || undefined,
      estado: estado || undefined,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">Gestión</span>
          <h1 className="font-heading text-3xl font-semibold">Reportes</h1>
        </div>
        <div className="flex gap-2">
          <Boton variante="contorno" onClick={() => exportar("xlsx")}>
            Exportar Excel
          </Boton>
          <Boton variante="contorno" onClick={() => exportar("pdf")}>
            Exportar PDF
          </Boton>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        {TIPOS.map((t) => (
          <button
            key={t.clave}
            onClick={() => setTipo(t.clave)}
            className={`rounded-full px-4 py-1.5 text-xs font-semibold tracking-[0.07em] uppercase transition-colors ${
              tipo === t.clave
                ? "bg-tinta text-hueso"
                : "border border-borde text-tinta-suave hover:border-borde-fuerte"
            }`}
          >
            {t.texto}
          </button>
        ))}
      </div>

      <Tarjeta className="flex flex-wrap items-end gap-4 p-5">
        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Desde</span>
          <input type="date" className="campo" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Hasta</span>
          <input type="date" className="campo" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Categoría</span>
          <select
            className="campo"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value as Categoria | "")}
          >
            <option value="">Todas</option>
            {(Object.keys(CATEGORIA) as Categoria[]).map((c) => (
              <option key={c} value={c}>
                {CATEGORIA[c]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Estado</span>
          <select
            className="campo"
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoAfiliado | "")}
          >
            <option value="">Todos</option>
            <option value="activo">Activos</option>
            <option value="pendiente">Pendientes</option>
            <option value="vencido">Vencidos</option>
          </select>
        </label>
      </Tarjeta>

      {!datos ? (
        <Cargando />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metrica etiqueta="Nuevas afiliaciones" valor={datos.nuevas_afiliaciones} />
            <Metrica etiqueta="Renovaciones" valor={datos.renovaciones} />
            <Metrica etiqueta="Bajas" valor={datos.bajas} acento="vencido" />
            <Metrica etiqueta="Recaudado" valor={moneyCorto(datos.recaudado)} />
          </div>

          <Tarjeta className="flex flex-col gap-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-heading text-xl font-semibold">Afiliaciones por mes y estado</h2>
              <div className="flex gap-4 text-xs text-tinta-suave">
                {SERIES.map((s) => (
                  <span key={s.clave} className="flex items-center gap-1.5">
                    <span className={`h-2.5 w-2.5 rounded-sm ${s.clase}`} />
                    {s.texto}
                  </span>
                ))}
              </div>
            </div>

            {datos.por_mes.length === 0 ? (
              <p className="py-10 text-center text-sm text-tinta-tenue">
                No hay afiliaciones en este rango de fechas.
              </p>
            ) : (
              <div className="flex h-48 items-end gap-3 overflow-x-auto">
                {datos.por_mes.map((mes) => (
                  <div key={`${mes.anio}-${mes.mes}`} className="flex min-w-10 flex-1 flex-col items-center gap-2">
                    <div className="flex h-full w-full flex-col justify-end gap-0.5">
                      {SERIES.map((s) => {
                        const valor = mes[s.clave];
                        return valor ? (
                          <div
                            key={s.clave}
                            className={`w-full rounded-sm ${s.clase}`}
                            style={{ height: `${(valor / alturaMaxima) * 100}%` }}
                            title={`${s.texto}: ${valor}`}
                          />
                        ) : null;
                      })}
                    </div>
                    <span className="cifra font-mono text-[0.62rem] tracking-wide text-tinta-tenue">
                      {mes.mes}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Tarjeta>

          <Tabla encabezados={["Categoría", "Afiliados", "Activos", "Pendientes", "Vencidos", "Recaudado"]}>
            {datos.por_categoria.map((fila) => (
              <tr key={fila.categoria} className="border-b border-borde last:border-0">
                <td className="px-4 py-3 font-medium">{CATEGORIA[fila.categoria]}</td>
                <td className="cifra px-4 py-3">{fila.total}</td>
                <td className="cifra px-4 py-3 text-activo">{fila.activos}</td>
                <td className="cifra px-4 py-3 text-pendiente">{fila.pendientes}</td>
                <td className="cifra px-4 py-3 text-vencido">{fila.vencidos}</td>
                <td className="cifra px-4 py-3 font-mono">{money(fila.recaudado)}</td>
              </tr>
            ))}
            <tr className="bg-hueso">
              <td className="px-4 py-3 font-semibold">Total</td>
              <td className="cifra px-4 py-3 font-semibold">{datos.total_afiliados}</td>
              <td colSpan={3} />
              <td className="cifra px-4 py-3 font-mono font-semibold">{money(datos.recaudado)}</td>
            </tr>
          </Tabla>
        </>
      )}
    </div>
  );
}
