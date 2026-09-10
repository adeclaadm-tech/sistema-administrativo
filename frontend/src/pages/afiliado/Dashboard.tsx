/** Pantalla 1b: estado de la afiliación, vencimiento, documentos y pagos. */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Aviso, Boton, Cargando, DocumentoBadge, EstadoBadge, Tarjeta } from "../../components/ui";
import { api } from "../../lib/api";
import { TIPO_DOCUMENTO, fecha, money, notaEstado } from "../../lib/format";
import type { Documento, Pago, Proforma, ResumenAfiliado } from "../../lib/types";

const COLOR_BARRA: Record<string, string> = {
  activo: "bg-activo",
  pendiente: "bg-pendiente",
  vencido: "bg-vencido",
};

export default function Dashboard() {
  const [resumen, setResumen] = useState<ResumenAfiliado | null>(null);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [pagos, setPagos] = useState<Pago[]>([]);
  const [proformas, setProformas] = useState<Proforma[]>([]);

  useEffect(() => {
    api.get<ResumenAfiliado>("/afiliados/me").then(setResumen).catch(() => setResumen(null));
    api.get<Documento[]>("/documentos/me").then(setDocumentos).catch(() => setDocumentos([]));
    api.get<Pago[]>("/pagos/me").then(setPagos).catch(() => setPagos([]));
    api.get<Proforma[]>("/proformas/me").then(setProformas).catch(() => setProformas([]));
  }, []);

  if (!resumen) return <Cargando />;

  const { afiliado } = resumen;
  const porPagar = proformas.filter((p) => !p.pago_id);
  const anioAfiliacion = afiliado.fecha_afiliacion
    ? new Date(afiliado.fecha_afiliacion).getFullYear()
    : null;

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-wrap items-end justify-between gap-5">
        <div className="flex flex-col gap-1.5">
          {anioAfiliacion ? <span className="etiqueta">Afiliado desde {anioAfiliacion}</span> : null}
          <h1 className="font-heading text-4xl leading-tight">{afiliado.nombre}</h1>
        </div>
        <EstadoBadge estado={afiliado.estado} />
      </header>

      {porPagar.length > 0 ? (
        <Aviso>
          <span className="flex flex-wrap items-center gap-x-2">
            <strong className="font-semibold">
              {porPagar.length === 1
                ? `Tienes la proforma ${porPagar[0].numero} por pagar`
                : `Tienes ${porPagar.length} proformas por pagar`}
            </strong>
            <span>· descarga el PDF con los datos de la cuenta y sube el comprobante.</span>
            <Link to="/portal/pagos" className="font-semibold text-teal-boton hover:underline">
              Ver proformas
            </Link>
          </span>
        </Aviso>
      ) : null}

      <Tarjeta className="grid gap-8 lg:grid-cols-[1.4fr_1px_1fr] lg:items-center">
        <div className="flex flex-col gap-3.5">
          <span className="etiqueta">Vencimiento de afiliación</span>
          <div className="flex items-baseline gap-3">
            <span className="cifra font-heading text-4xl leading-none font-semibold">
              {fecha(afiliado.fecha_vencimiento)}
            </span>
            {resumen.dias_para_vencer !== null ? (
              <span className="text-sm text-tinta-suave">
                {resumen.dias_para_vencer >= 0
                  ? `faltan ${resumen.dias_para_vencer} días`
                  : `venció hace ${Math.abs(resumen.dias_para_vencer)} días`}
              </span>
            ) : null}
          </div>

          <div
            className="h-1.5 max-w-md overflow-hidden rounded-full bg-borde"
            role="progressbar"
            aria-valuenow={Math.round(resumen.progreso_anual * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Avance del año de afiliación"
          >
            <div
              className={`h-full rounded-full ${COLOR_BARRA[afiliado.estado]}`}
              style={{ width: `${Math.round(resumen.progreso_anual * 100)}%` }}
            />
          </div>

          <p className="max-w-lg text-sm leading-relaxed text-tinta-suave">
            {notaEstado(afiliado.estado, resumen.dias_para_vencer)}
          </p>
        </div>

        <div className="hidden h-full w-px bg-borde lg:block" />

        <div className="flex flex-col gap-3">
          <Link to="/portal/documentos">
            <Boton className="w-full py-3.5">Subir documentos</Boton>
          </Link>
          <Link to="/portal/pagos">
            <Boton variante="contorno" className="w-full py-3.5">
              {porPagar.length > 0 ? "Pagar mi proforma" : "Ver mis proformas"}
            </Boton>
          </Link>
          <span className="text-center font-mono text-[0.68rem] tracking-wider text-tinta-tenue uppercase">
            Cuota anual · {money(afiliado.cuota_anual)}
          </span>
        </div>
      </Tarjeta>

      <div className="grid gap-5 lg:grid-cols-2">
        <Tarjeta className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl">Mis documentos</h2>
            <span className="font-mono text-[0.68rem] tracking-wider text-tinta-suave uppercase">
              {resumen.documentos_aprobados} / {resumen.documentos_totales || 4} aprobados
            </span>
          </div>

          <ul className="flex flex-col divide-y divide-borde">
            {documentos.length === 0 ? (
              <li className="py-4 text-sm text-tinta-tenue">
                Todavía no has subido documentos.{" "}
                <Link to="/portal/documentos" className="text-teal-boton hover:underline">
                  Empieza aquí
                </Link>
                .
              </li>
            ) : (
              documentos.map((doc) => (
                <li key={doc.id} className="flex items-center justify-between gap-3 py-3">
                  <span className="text-sm">{TIPO_DOCUMENTO[doc.tipo]}</span>
                  <DocumentoBadge estado={doc.estado} />
                </li>
              ))
            )}
          </ul>
        </Tarjeta>

        <Tarjeta className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl">Últimos pagos</h2>
            <Link to="/portal/pagos" className="text-sm text-teal-boton hover:underline">
              Ver historial
            </Link>
          </div>

          <ul className="flex flex-col divide-y divide-borde">
            {pagos.length === 0 ? (
              <li className="py-4 text-sm text-tinta-tenue">Sin pagos registrados todavía.</li>
            ) : (
              pagos.slice(0, 3).map((pago) => (
                <li key={pago.id} className="flex items-center justify-between gap-4 py-3">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm">{pago.concepto ?? `Cuota ${pago.periodo}`}</span>
                    <span className="cifra font-mono text-[0.68rem] tracking-wide text-tinta-tenue uppercase">
                      {fecha(pago.fecha)} · {pago.metodo}
                    </span>
                  </div>
                  <span className="cifra font-mono text-sm">{money(pago.monto)}</span>
                </li>
              ))
            )}
          </ul>
        </Tarjeta>
      </div>
    </div>
  );
}
