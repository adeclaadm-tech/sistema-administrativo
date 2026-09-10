/**
 * Todas las proformas emitidas, de todos los afiliados.
 *
 * El staff necesita ver el cobro completo en un solo sitio: qué se emitió,
 * qué sigue sin pagar y desde cuándo. Por afiliado ya se veía en su ficha,
 * pero eso obliga a entrar empresa por empresa.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Aviso, Boton, Cargando, Tabla, Tarjeta, Vacio } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { fecha, money } from "../../lib/format";
import { useAuth } from "../../lib/auth";
import type { Proforma } from "../../lib/types";

type Filtro = "todas" | "pendientes" | "pagadas";

export default function Proformas() {
  const { puedeEscribir } = useAuth();
  const [proformas, setProformas] = useState<Proforma[] | null>(null);
  const [anulando, setAnulando] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("todas");
  const [periodo, setPeriodo] = useState<number | "">("");
  const [busqueda, setBusqueda] = useState("");

  useEffect(() => {
    api
      .get<Proforma[]>("/proformas", {
        pagadas: filtro === "todas" ? undefined : filtro === "pagadas",
        periodo: periodo || undefined,
      })
      .then(setProformas)
      .catch(() => setProformas(null));
  }, [filtro, periodo]);

  const visibles = useMemo(() => {
    if (!proformas) return [];
    const q = busqueda.trim().toLowerCase();
    if (!q) return proformas;
    return proformas.filter(
      (p) =>
        p.numero.toLowerCase().includes(q) ||
        (p.afiliado_nombre ?? "").toLowerCase().includes(q),
    );
  }, [proformas, busqueda]);

  async function anular(p: Proforma) {
    if (!window.confirm(`¿Anular la proforma ${p.numero}? No se puede deshacer.`)) return;
    setAnulando(p.id);
    setAviso(null);
    try {
      const r = await api.delete<{ detail: string }>(`/proformas/${p.id}`);
      setAviso(r.detail);
      setProformas((previas) => (previas ?? []).filter((x) => x.id !== p.id));
    } catch (e) {
      setAviso(e instanceof ApiError ? e.message : "No se pudo anular.");
    } finally {
      setAnulando(null);
    }
  }

  const anio = new Date().getFullYear();
  const anios = [anio + 1, anio, anio - 1, anio - 2];

  const pendiente = visibles.filter((p) => !p.pago_id);
  const totalPendiente = pendiente.reduce((suma, p) => suma + Number(p.monto ?? 0), 0);

  const pestanas: { clave: Filtro; texto: string }[] = [
    { clave: "todas", texto: "Todas" },
    { clave: "pendientes", texto: "Sin pagar" },
    { clave: "pagadas", texto: "Saldadas" },
  ];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">{visibles.length} emitidas</span>
          <h1 className="font-heading text-3xl">Proformas</h1>
        </div>
        {pendiente.length > 0 ? (
          <Tarjeta className="px-5 py-3">
            <span className="etiqueta">Por cobrar</span>
            <p className="cifra font-heading text-2xl">{money(totalPendiente)}</p>
            <span className="text-xs text-tinta-tenue">
              {pendiente.length} {pendiente.length === 1 ? "proforma" : "proformas"} sin pagar
            </span>
          </Tarjeta>
        ) : null}
      </header>

      {aviso ? <Aviso tono="teal">{aviso}</Aviso> : null}

      <Tarjeta className="flex flex-col gap-4 p-5">
        <input
          className="campo"
          placeholder="Buscar por número o razón social…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <div className="flex flex-wrap items-center gap-2">
          {pestanas.map((p) => (
            <button
              key={p.clave}
              onClick={() => setFiltro(p.clave)}
              className={`rounded-full px-3.5 py-1.5 text-xs font-semibold tracking-[0.06em] uppercase transition-colors ${
                filtro === p.clave
                  ? "bg-tinta text-hueso"
                  : "border border-borde text-tinta-suave hover:border-borde-fuerte"
              }`}
            >
              {p.texto}
            </button>
          ))}
          <select
            className="ml-auto rounded-[8px] border border-borde bg-superficie px-3 py-1.5 text-xs tracking-[0.06em] text-tinta-suave uppercase"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Período · todos</option>
            {anios.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
      </Tarjeta>

      {!proformas ? (
        <Cargando />
      ) : visibles.length === 0 ? (
        <Tarjeta>
          <Vacio
            titulo="Ninguna proforma coincide"
            detalle="Las proformas se emiten desde la ficha de cada afiliado."
          />
        </Tarjeta>
      ) : (
        <Tabla encabezados={["Número", "Afiliado", "Concepto", "Período", "Emitida", "Monto", "Estado", ""]}>
          {visibles.map((p) => (
            <tr key={p.id} className="border-b border-borde last:border-0 hover:bg-hueso">
              <td className="cifra px-4 py-3 font-mono text-xs">{p.numero}</td>
              <td className="px-4 py-3">
                <Link to={`/admin/afiliados/${p.afiliado_id}`} className="hover:text-teal-boton">
                  {p.afiliado_nombre ?? "—"}
                </Link>
              </td>
              <td className="px-4 py-3 text-tinta-suave">{p.concepto ?? "—"}</td>
              <td className="cifra px-4 py-3 text-tinta-suave">{p.periodo ?? "—"}</td>
              <td className="px-4 py-3 whitespace-nowrap text-tinta-suave">
                {fecha(p.fecha_generacion)}
              </td>
              <td className="cifra px-4 py-3 font-mono whitespace-nowrap">{money(p.monto)}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-3 py-1 text-[0.68rem] font-semibold tracking-[0.07em] uppercase ${
                    p.pago_id ? "bg-activo-suave text-activo" : "bg-pendiente-suave text-pendiente"
                  }`}
                >
                  {p.pago_id ? "Saldada" : "Sin pagar"}
                </span>
              </td>
              <td className="px-4 py-3 text-right whitespace-nowrap">
                <Boton
                  variante="fantasma"
                  onClick={() => void api.descargar(`/proformas/${p.id}/pdf`)}
                >
                  PDF
                </Boton>
                {puedeEscribir && !p.pago_id ? (
                  <Boton
                    variante="fantasma"
                    className="text-vencido"
                    cargando={anulando === p.id}
                    onClick={() => void anular(p)}
                  >
                    Anular
                  </Boton>
                ) : null}
              </td>
            </tr>
          ))}
        </Tabla>
      )}
    </div>
  );
}
