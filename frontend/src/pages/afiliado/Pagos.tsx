/**
 * Pantalla 1d del portal: proformas por pagar e historial de pagos.
 *
 * Las proformas van primero y como sección propia. Antes la tabla recorría los
 * pagos y buscaba la proforma por `pago_id`, así que una proforma recién
 * emitida —sin pago todavía, que es el caso para el que existe— no aparecía en
 * ninguna parte: el afiliado recibía el cobro por correo y al entrar al portal
 * no encontraba nada.
 */

import { useEffect, useState } from "react";

import { Aviso, Boton, Cargando, Tabla, Tarjeta, Vacio } from "../../components/ui";
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
  const porPagar = proformas.filter((p) => !p.pago_id);
  const totalPagado = pagos.reduce((suma, p) => suma + Number(p.monto), 0);
  const totalPorPagar = porPagar.reduce((suma, p) => suma + Number(p.monto ?? 0), 0);

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="etiqueta">Cobros</span>
          <h1 className="font-heading text-3xl">Proformas y pagos</h1>
        </div>
        <div className="flex gap-3">
          {porPagar.length > 0 ? (
            <Tarjeta className="px-5 py-3">
              <span className="etiqueta">Por pagar</span>
              <p className="cifra font-heading text-2xl text-pendiente">{money(totalPorPagar)}</p>
            </Tarjeta>
          ) : null}
          <Tarjeta className="px-5 py-3">
            <span className="etiqueta">Total pagado</span>
            <p className="cifra font-heading text-2xl">{money(totalPagado)}</p>
          </Tarjeta>
        </div>
      </header>

      {porPagar.length > 0 ? (
        <Aviso>
          {porPagar.length === 1
            ? "Tienes una proforma pendiente de pago."
            : `Tienes ${porPagar.length} proformas pendientes de pago.`}{" "}
          Descarga el PDF —trae los datos de la cuenta— y cuando pagues sube el comprobante desde
          Documentos.
        </Aviso>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-xl">Mis proformas</h2>

        {proformas.length === 0 ? (
          <Tarjeta>
            <Vacio
              titulo="Todavía no hay proformas"
              detalle="ADECLA emite la proforma cuando toca renovar. Te llega por correo y aparece aquí."
            />
          </Tarjeta>
        ) : (
          <Tabla encabezados={["Número", "Concepto", "Período", "Emitida", "Monto", "Estado", ""]}>
            {proformas.map((p) => (
              <tr key={p.id} className="border-b border-borde last:border-0">
                <td className="cifra px-4 py-3.5 font-mono text-xs">{p.numero}</td>
                <td className="px-4 py-3.5">{p.concepto ?? "—"}</td>
                <td className="cifra px-4 py-3.5 text-tinta-suave">{p.periodo ?? "—"}</td>
                <td className="px-4 py-3.5 whitespace-nowrap text-tinta-suave">
                  {fecha(p.fecha_generacion)}
                </td>
                <td className="cifra px-4 py-3.5 font-mono whitespace-nowrap">{money(p.monto)}</td>
                <td className="px-4 py-3.5">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-[0.68rem] font-semibold tracking-[0.07em] uppercase ${
                      p.pago_id
                        ? "bg-activo-suave text-activo"
                        : "bg-pendiente-suave text-pendiente"
                    }`}
                  >
                    {p.pago_id ? "Pagada" : "Por pagar"}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-right">
                  <Boton
                    variante={p.pago_id ? "fantasma" : "primario"}
                    onClick={() => void api.descargar(`/proformas/${p.id}/pdf`)}
                  >
                    Descargar PDF
                  </Boton>
                </td>
              </tr>
            ))}
          </Tabla>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-xl">Pagos registrados</h2>

        {pagos.length === 0 ? (
          <Tarjeta>
            <Vacio
              titulo="Sin pagos registrados"
              detalle="Cuando ADECLA registre tu pago, aparece aquí con su proforma."
            />
          </Tarjeta>
        ) : (
          <Tabla encabezados={["Concepto", "Proforma", "Fecha", "Método", "Monto"]}>
            {pagos.map((pago) => (
              <tr key={pago.id} className="border-b border-borde last:border-0">
                <td className="px-4 py-3.5">{pago.concepto ?? `Cuota ${pago.periodo ?? ""}`}</td>
                <td className="cifra px-4 py-3.5 font-mono text-xs text-tinta-suave">
                  {proformaDe.get(pago.id)?.numero ?? "—"}
                </td>
                <td className="px-4 py-3.5 whitespace-nowrap text-tinta-suave">
                  {fecha(pago.fecha)}
                </td>
                <td className="px-4 py-3.5 text-tinta-suave capitalize">{pago.metodo}</td>
                <td className="cifra px-4 py-3.5 font-mono whitespace-nowrap">
                  {money(pago.monto)}
                </td>
              </tr>
            ))}
          </Tabla>
        )}
      </section>
    </div>
  );
}
