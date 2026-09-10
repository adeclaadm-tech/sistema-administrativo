/** Todos los pagos de la asociación, con filtro por período. */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Boton, Cargando, Tabla, Tarjeta, Vacio } from "../../components/ui";
import { api } from "../../lib/api";
import { fecha, money } from "../../lib/format";
import type { Pagina, Pago } from "../../lib/types";

export default function PagosAdmin() {
  const [pagina, setPagina] = useState<Pagina<Pago> | null>(null);
  const [periodo, setPeriodo] = useState<number | "">("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    api
      .get<Pagina<Pago>>("/pagos", { periodo: periodo || undefined, page, per_page: 20 })
      .then(setPagina)
      .catch(() => setPagina(null));
  }, [periodo, page]);

  const anioActual = new Date().getFullYear();
  const anios = [anioActual, anioActual - 1, anioActual - 2, anioActual - 3];
  const paginas = pagina ? Math.max(1, Math.ceil(pagina.total / pagina.per_page)) : 1;
  const totalPagina = pagina?.items.reduce((suma, p) => suma + Number(p.monto), 0) ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">{pagina?.total ?? 0} pagos registrados</span>
          <h1 className="font-heading text-3xl">Pagos</h1>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="rounded-[8px] border border-borde bg-superficie px-3 py-2 text-sm"
            value={periodo}
            onChange={(e) => {
              setPeriodo(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
          >
            <option value="">Todos los períodos</option>
            {anios.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          <Boton
            variante="contorno"
            onClick={() => void api.descargar("/reportes/export", { formato: "xlsx", tipo: "recaudacion" })}
          >
            Exportar
          </Boton>
        </div>
      </header>

      {!pagina ? (
        <Cargando />
      ) : pagina.items.length === 0 ? (
        <Tarjeta>
          <Vacio titulo="Sin pagos en este período" detalle="Cambia el filtro o registra uno desde la ficha del afiliado." />
        </Tarjeta>
      ) : (
        <>
          <Tabla encabezados={["Fecha", "Concepto", "Método", "Referencia", "Monto", ""]}>
            {pagina.items.map((pago) => (
              <tr key={pago.id} className="border-b border-borde last:border-0 hover:bg-hueso">
                <td className="cifra px-4 py-3 font-mono text-xs">{fecha(pago.fecha)}</td>
                <td className="px-4 py-3">{pago.concepto ?? `Cuota ${pago.periodo ?? ""}`}</td>
                <td className="px-4 py-3 text-tinta-suave capitalize">{pago.metodo}</td>
                <td className="cifra px-4 py-3 font-mono text-xs text-tinta-tenue">
                  {pago.referencia ?? "—"}
                </td>
                <td className="cifra px-4 py-3 font-mono">{money(pago.monto)}</td>
                <td className="px-4 py-3 text-right">
                  <Link
                    to={`/admin/afiliados/${pago.afiliado_id}`}
                    className="text-sm text-teal-boton hover:underline"
                  >
                    Ver ficha
                  </Link>
                </td>
              </tr>
            ))}
          </Tabla>

          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-tinta-suave">
            <span className="cifra font-mono tracking-wide uppercase">
              Subtotal de esta página · {money(totalPagina)}
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
