/**
 * Emisión de la proforma de cobro.
 *
 * Antes era un botón suelto: pulsarlo dos veces creaba dos documentos válidos
 * para la misma cuota, cada uno con su número. Ahora hay que decir qué se está
 * cobrando —período, monto y concepto— y el backend rechaza una segunda
 * proforma sin pagar del mismo período.
 */

import { useState, type FormEvent } from "react";

import { Aviso, Boton, Campo, Tarjeta } from "./ui";
import { ApiError, api } from "../lib/api";
import { money } from "../lib/format";
import type { Afiliado, Proforma } from "../lib/types";

export default function EmitirProforma({
  afiliado,
  pendientes,
  onEmitida,
  onCancelar,
}: {
  afiliado: Afiliado;
  pendientes: Proforma[];
  onEmitida: (proforma: Proforma) => void;
  onCancelar: () => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const anio = new Date().getFullYear();

  async function emitir(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;

    setEnviando(true);
    setError(null);
    try {
      const proforma = await api.post<Proforma>(
        `/proformas?enviar=${datos.avisar === "on"}`,
        {
          afiliado_id: afiliado.id,
          periodo: Number(datos.periodo),
          monto: datos.monto,
          concepto: datos.concepto.trim() || null,
        },
      );
      onEmitida(proforma);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo emitir la proforma.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Tarjeta className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <h2 className="font-heading text-xl">Emitir proforma</h2>
        <p className="text-sm text-tinta-suave">
          Es el cobro que recibe el afiliado: le llega por correo con el PDF adjunto y habilita la
          subida del soporte de pago en su portal.
        </p>
      </div>

      {pendientes.length > 0 ? (
        <Aviso>
          Ya hay {pendientes.length === 1 ? "una proforma sin pagar" : `${pendientes.length} proformas sin pagar`}:{" "}
          {pendientes.map((p) => `${p.numero} (${p.periodo ?? "sin período"})`).join(", ")}. Emitir
          otra del mismo período va a dar error.
        </Aviso>
      ) : null}

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      <form onSubmit={emitir} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Campo
            etiqueta="Período"
            name="periodo"
            type="number"
            min="2000"
            max="2100"
            defaultValue={anio}
            ayuda="El año que cubre la cuota."
            required
          />
          <Campo
            etiqueta="Monto"
            name="monto"
            type="number"
            step="0.01"
            min="0"
            defaultValue={afiliado.cuota_anual ?? ""}
            ayuda={afiliado.cuota_anual ? `Cuota de la ficha: ${money(afiliado.cuota_anual)}` : "Sin cuota en la ficha."}
            required
          />
          <Campo
            etiqueta="Concepto"
            name="concepto"
            placeholder={`Cuota anual ${anio}`}
            ayuda="Aparece en la línea del documento."
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-tinta-suave">
          <input type="checkbox" name="avisar" defaultChecked className="accent-teal-boton" />
          Enviarla por correo al afiliado con el PDF adjunto
          {afiliado.email ? "" : " — esta empresa no tiene correo en la ficha"}
        </label>

        <div className="flex justify-end gap-2">
          <Boton type="button" variante="contorno" onClick={onCancelar}>
            Cancelar
          </Boton>
          <Boton type="submit" cargando={enviando}>
            Emitir
          </Boton>
        </div>
      </form>
    </Tarjeta>
  );
}
