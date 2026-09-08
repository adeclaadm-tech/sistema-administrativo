/** Pantalla 1d: historial de pagos y descarga de proformas. */

import { useEffect, useState } from "react";

import { Boton, Cargando, Tabla, Tarjeta, Vacio } from "../../components/ui";
import { api } from "../../lib/api";
import { fecha, money } from "../../lib/format";
import type { Pago, Proforma } from "../../lib/types";

export default function Pagos() {
  const [pagos, setPagos] = useState<Pago[] | null>(null);
  const [proformas, setProformas] = useState<Proforma[]>([]);

  useEffect(() => {
    api.get<Pago[]>("/pagos/me").then(setPagos).catch(() => setPagos([]));
    api.get<Proforma[]>("/proformas/me").then(setProformas).catch(() => setProformas([]));
  }, []);

  if (!pagos) return <Cargando />;

  const proformaDe = new Map(proformas.filter((p) => p.pago_id).map((p) => [p.pago_id, p]));
  const total = pagos.reduce((suma, p) => suma + Number(p.monto), 0);

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="etiqueta">Historial</span>
          <h1 className="font-heading text-3xl font-semibold">Pagos y proformas</h1>
        </div>
        <Tarjeta className="px-5 py-3">
          <span className="etiqueta">Total pagado</span>
          <p className="cifra font-heading text-2xl font-semibold">{money(total)}</p>
        </Tarjeta>
      </header>

      {pagos.length === 0 ? (
        <Tarjeta>
          <Vacio
            titulo="Todavía no hay pagos registrados"
            detalle="Cuando el equipo de ADECLA registre tu cuota, el comprobante y la proforma aparecen aquí."
          />
        </Tarjeta>
      ) : (
        <Tabla encabezados={["Concepto", "Proforma", "Fecha", "Método", "Monto", ""]}>
          {pagos.map((pago) => {
            const proforma = proformaDe.get(pago.id);
            return (
              <tr key={pago.id} className="border-b border-borde last:border-0">
                <td className="px-4 py-3.5">{pago.concepto ?? `Cuota ${pago.periodo ?? ""}`}</td>
                <td className="cifra px-4 py-3.5 font-mono text-xs text-tinta-suave">
                  {proforma?.numero ?? "—"}
                </td>
                <td className="px-4 py-3.5 text-tinta-suave">{fecha(pago.fecha)}</td>
                <td className="px-4 py-3.5 text-tinta-suave capitalize">{pago.metodo}</td>
                <td className="cifra px-4 py-3.5 font-mono">{money(pago.monto)}</td>
                <td className="px-4 py-3.5 text-right">
                  {proforma ? (
                    <Boton
                      variante="fantasma"
                      onClick={() => void api.descargar(`/proformas/${proforma.id}/pdf`)}
                    >
                      Descargar PDF
                    </Boton>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </Tabla>
      )}
    </div>
  );
}
