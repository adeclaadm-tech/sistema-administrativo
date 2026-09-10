/** Pantalla 1f: métricas de la base y cola de revisión. */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Aviso, Boton, Cargando, Metrica, Tarjeta, Vacio } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { TIPO_DOCUMENTO, moneyCorto } from "../../lib/format";
import { useAuth } from "../../lib/auth";
import type {
  CandidatoRecordatorio,
  DocumentoEnCola,
  Metricas,
  ResumenEnvio,
} from "../../lib/types";

export default function DashboardAdmin() {
  const { puedeEscribir } = useAuth();
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [cola, setCola] = useState<DocumentoEnCola[]>([]);
  const [revisando, setRevisando] = useState<string | null>(null);
  const [tanda, setTanda] = useState<CandidatoRecordatorio[]>([]);
  const [enviandoTanda, setEnviandoTanda] = useState(false);
  const [avisoTanda, setAvisoTanda] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api.get<Metricas>("/reportes/dashboard").then(setMetricas).catch(() => setMetricas(null));
    api
      .get<DocumentoEnCola[]>("/documentos/cola", { limite: 6 })
      .then(setCola)
      .catch(() => setCola([]));
    api
      .get<CandidatoRecordatorio[]>("/afiliados/recordatorios/pendientes")
      .then(setTanda)
      .catch(() => setTanda([]));
  }, []);



  useEffect(cargar, [cargar]);

  async function revisar(id: string, aprobado: boolean) {
    setRevisando(id);
    try {
      await api.post(`/documentos/${id}/revision`, {
        aprobado,
        motivo_rechazo: aprobado ? null : "El documento no se lee o no corresponde al período.",
      });
      cargar();
    } finally {
      setRevisando(null);
    }
  }

  async function enviarTanda() {
    setEnviandoTanda(true);
    setAvisoTanda(null);
    try {
      const r = await api.post<ResumenEnvio>("/afiliados/recordatorios/enviar");
      const partes = [`${r.enviados} enviados`];
      if (r.sin_correo) partes.push(`${r.sin_correo} sin correo`);
      if (r.fallidos) partes.push(`${r.fallidos} fallaron`);
      setAvisoTanda(partes.join(" · "));
      cargar();
    } catch (e) {
      setAvisoTanda(e instanceof ApiError ? e.message : "No se pudo enviar la tanda.");
    } finally {
      setEnviandoTanda(false);
    }
  }

  if (!metricas) return <Cargando />;

  const porcentajeActivos = metricas.total_afiliados
    ? Math.round((metricas.activos / metricas.total_afiliados) * 100)
    : 0;

  const composicion = [
    { texto: "Activos", valor: metricas.activos, clase: "bg-activo" },
    { texto: "Pendientes", valor: metricas.pendientes, clase: "bg-pendiente" },
    { texto: "Vencidos", valor: metricas.vencidos, clase: "bg-vencido" },
  ];

  return (
    <div className="flex flex-col gap-7">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">Periodo {new Date().getFullYear()}</span>
          <h1 className="font-heading text-3xl">Dashboard general</h1>
        </div>
        {puedeEscribir ? (
          <Link to="/admin/afiliados">
            <Boton>Nuevo afiliado</Boton>
          </Link>
        ) : null}
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metrica
          etiqueta="Total afiliados"
          valor={metricas.total_afiliados}
          pie={`+${metricas.nuevos_en_el_ano} este año`}
        />
        <Metrica
          etiqueta="Activos"
          valor={metricas.activos}
          pie={`${porcentajeActivos}% de la base`}
        />
        <Link to="/admin/afiliados?vence=30" className="contents">
          <Metrica
            etiqueta="Próximos a vencer"
            valor={metricas.proximos_a_vencer}
            pie="vencen en 30 días · ver listado"
            acento="pendiente"
            interactiva
          />
        </Link>
        <Metrica
          etiqueta="Pendientes de revisión"
          valor={metricas.documentos_por_revisar}
          pie="documentos en cola"
          acento={metricas.documentos_por_revisar > 0 ? "vencido" : undefined}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
        <Tarjeta className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl">Cola de revisión</h2>
            <Link to="/admin/documentos" className="text-sm text-teal-boton hover:underline">
              Ver todos ({metricas.documentos_por_revisar})
            </Link>
          </div>

          {cola.length === 0 ? (
            <Vacio titulo="Nada por revisar" detalle="Toda la documentación está al día." />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-borde">
                  <th className="etiqueta py-2 text-left">Afiliado</th>
                  <th className="etiqueta py-2 text-left">Documento</th>
                  <th className="etiqueta py-2 text-left">Espera</th>
                  <th className="etiqueta py-2 text-right">Acción</th>
                </tr>
              </thead>
              <tbody>
                {cola.map((fila) => (
                  <tr key={fila.id} className="border-b border-borde last:border-0">
                    <td className="py-3 pr-3">
                      <Link
                        to={`/admin/afiliados/${fila.afiliado_id}`}
                        className="hover:text-teal-boton"
                      >
                        {fila.afiliado_nombre}
                      </Link>
                    </td>
                    <td className="py-3 pr-3 text-tinta-suave">{TIPO_DOCUMENTO[fila.tipo]}</td>
                    <td
                      className={`cifra py-3 pr-3 font-mono text-xs ${
                        fila.dias_en_espera >= 3 ? "text-vencido" : "text-tinta-suave"
                      }`}
                    >
                      {fila.dias_en_espera === 0
                        ? "HOY"
                        : `${fila.dias_en_espera} ${fila.dias_en_espera === 1 ? "DÍA" : "DÍAS"}`}
                    </td>
                    <td className="py-3 text-right">
                      {puedeEscribir ? (
                        <span className="inline-flex gap-1">
                          <Boton
                            variante="fantasma"
                            cargando={revisando === fila.id}
                            onClick={() => void revisar(fila.id, true)}
                          >
                            Aprobar
                          </Boton>
                          <Boton
                            variante="fantasma"
                            className="text-vencido"
                            onClick={() => void revisar(fila.id, false)}
                          >
                            Rechazar
                          </Boton>
                        </span>
                      ) : (
                        <span className="text-xs text-tinta-tenue">Solo lectura</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Tarjeta>

        <div className="flex flex-col gap-5">
          <Tarjeta className="flex flex-col gap-4">
            <h2 className="font-heading text-xl">Composición de la base</h2>
            <ul className="flex flex-col gap-3">
              {composicion.map((fila) => (
                <li key={fila.texto} className="flex flex-col gap-1.5">
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="text-tinta-suave">{fila.texto}</span>
                    <span className="cifra font-semibold">{fila.valor}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-borde">
                    <div
                      className={`h-full rounded-full ${fila.clase}`}
                      style={{
                        width: `${
                          metricas.total_afiliados
                            ? Math.round((fila.valor / metricas.total_afiliados) * 100)
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Tarjeta>

          <Tarjeta className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="font-heading text-xl">Recordatorios de hoy</h2>
              <span className="cifra font-mono text-xs text-tinta-suave">{tanda.length}</span>
            </div>

            {tanda.length === 0 ? (
              <p className="text-sm text-tinta-tenue">
                Hoy no le toca aviso a nadie. Se manda 30 días antes del vencimiento, y a los 7, 30
                y 60 días después.
              </p>
            ) : (
              <>
                <ul className="flex flex-col gap-2">
                  {tanda.slice(0, 4).map((c) => (
                    <li key={c.afiliado_id} className="flex flex-col gap-0.5">
                      <Link
                        to={`/admin/afiliados/${c.afiliado_id}`}
                        className="text-sm hover:text-teal-boton"
                      >
                        {c.afiliado_nombre}
                      </Link>
                      <span className="text-xs text-tinta-tenue">
                        {c.motivo}
                        {c.email ? "" : " · sin correo"}
                        {c.proforma ? ` · ${c.proforma}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
                {tanda.length > 4 ? (
                  <span className="text-xs text-tinta-tenue">y {tanda.length - 4} más</span>
                ) : null}
                {puedeEscribir ? (
                  <Boton variante="contorno" cargando={enviandoTanda} onClick={() => void enviarTanda()}>
                    {tanda.length === 1 ? "Enviar el recordatorio" : `Enviar los ${tanda.length}`}
                  </Boton>
                ) : null}
              </>
            )}

            {avisoTanda ? <Aviso tono="teal">{avisoTanda}</Aviso> : null}
          </Tarjeta>

          <Tarjeta className="flex flex-col gap-2">
            <span className="etiqueta">Recaudación {new Date().getFullYear()}</span>
            <p className="cifra font-heading text-3xl font-semibold">
              {moneyCorto(metricas.recaudado_periodo)}
            </p>
            {metricas.variacion_recaudacion !== null ? (
              <span
                className={`text-xs ${
                  metricas.variacion_recaudacion >= 0 ? "text-activo" : "text-vencido"
                }`}
              >
                {metricas.variacion_recaudacion >= 0 ? "+" : ""}
                {metricas.variacion_recaudacion}% contra el año pasado
              </span>
            ) : null}
          </Tarjeta>
        </div>
      </div>
    </div>
  );
}
