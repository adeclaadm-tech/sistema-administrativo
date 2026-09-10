/**
 * Panel para mandar el recordatorio de vencimiento.
 *
 * Antes el botón enviaba en el acto, sin decir a quién ni con qué. Aquí se ve
 * la dirección exacta antes de pulsar, se puede desviar a otro contacto y se
 * puede agregar una nota para ese envío concreto —un acuerdo de pago, una
 * aclaración— que va dentro del correo.
 */

import { useEffect, useState, type FormEvent } from "react";

import { Aviso, Boton, Campo, Tarjeta } from "./ui";
import { ApiError, api } from "../lib/api";
import { fecha } from "../lib/format";
import type { Afiliado, DestinatarioPosible, Proforma } from "../lib/types";

export default function RecordatorioPanel({
  afiliado,
  proformaPendiente,
  onEnviado,
  onCancelar,
}: {
  afiliado: Afiliado;
  proformaPendiente: Proforma | null;
  onEnviado: (mensaje: string) => void;
  onCancelar: () => void;
}) {
  const [opciones, setOpciones] = useState<DestinatarioPosible[] | null>(null);
  const [destino, setDestino] = useState("automatico");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<DestinatarioPosible[]>(`/afiliados/${afiliado.id}/recordatorio`)
      .then(setOpciones)
      .catch(() => setOpciones([]));
  }, [afiliado.id]);

  const dias =
    afiliado.fecha_vencimiento === null
      ? null
      : Math.round(
          (new Date(afiliado.fecha_vencimiento + "T00:00:00").getTime() - Date.now()) / 86400000,
        );

  const situacion =
    dias === null
      ? "Esta empresa no tiene fecha de vencimiento en su ficha, así que el correo va sin plazo."
      : dias < 0
        ? `Venció hace ${Math.abs(dias)} días, el ${fecha(afiliado.fecha_vencimiento)}.`
        : `Vence en ${dias} días, el ${fecha(afiliado.fecha_vencimiento)}.`;

  // Con "automático" se usa la primera de la lista, que viene ordenada con
  // contabilidad delante por ser quien paga.
  const elegido =
    destino === "automatico"
      ? (opciones?.[0]?.email ?? null)
      : destino === "otro"
        ? null
        : (opciones?.find((o) => o.destino === destino)?.email ?? null);

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;

    setEnviando(true);
    setError(null);
    try {
      const r = await api.post<{ detail: string }>(`/afiliados/${afiliado.id}/recordatorio`, {
        destino: datos.destino,
        email: datos.destino === "otro" ? datos.email : null,
        nota: datos.nota.trim() || null,
        adjuntar_proforma: datos.adjuntar === "on",
      });
      onEnviado(r.detail);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo enviar el recordatorio.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Tarjeta className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <h2 className="font-heading text-xl">Enviar recordatorio</h2>
        <p className="text-sm text-tinta-suave">{situacion}</p>
      </div>

      {opciones !== null && opciones.length === 0 ? (
        <Aviso tono="vencido">
          Esta empresa no tiene ningún correo cargado. Agrégalo en la ficha o en sus contactos por
          área antes de mandarle nada.
        </Aviso>
      ) : null}

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      <form onSubmit={enviar} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Destinatario</span>
          <select
            name="destino"
            className="campo"
            value={destino}
            onChange={(e) => setDestino(e.target.value)}
          >
            <option value="automatico">
              Automático — contabilidad, o el primero disponible
            </option>
            {(opciones ?? []).map((o) => (
              <option key={o.destino} value={o.destino}>
                {o.etiqueta}
              </option>
            ))}
            <option value="otro">Otra dirección…</option>
          </select>
          {destino !== "otro" ? (
            <span className="cifra font-mono text-xs text-tinta-suave">
              {elegido ?? "sin correo disponible"}
            </span>
          ) : null}
        </label>

        {destino === "otro" ? (
          <Campo
            etiqueta="Correo"
            name="email"
            type="email"
            placeholder="contabilidad@empresa.do"
            required
          />
        ) : null}

        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Nota para este envío</span>
          <textarea
            name="nota"
            className="campo min-h-20"
            maxLength={600}
            placeholder="Opcional. Va dentro del correo, destacada. Por ejemplo: quedamos en que pagan en dos partes antes del 30."
          />
        </label>

        <label className="flex items-center gap-2 text-sm text-tinta-suave">
          <input
            type="checkbox"
            name="adjuntar"
            defaultChecked
            disabled={!proformaPendiente}
            className="accent-teal-boton"
          />
          {proformaPendiente
            ? `Adjuntar la proforma ${proformaPendiente.numero}`
            : "No hay proforma sin pagar que adjuntar"}
        </label>

        <div className="flex justify-end gap-2">
          <Boton type="button" variante="contorno" onClick={onCancelar}>
            Cancelar
          </Boton>
          <Boton type="submit" cargando={enviando} disabled={opciones?.length === 0}>
            Enviar
          </Boton>
        </div>
      </form>
    </Tarjeta>
  );
}
