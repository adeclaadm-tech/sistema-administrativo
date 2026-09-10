/**
 * Edición de la ficha del afiliado.
 *
 * Existe sobre todo por las fechas: el padrón importado no trae vencimiento, y
 * sin él la métrica de "próximos a vencer" y el estado del portal no tienen de
 * dónde salir. Aquí también se completan el RNC y la cuota, que tampoco vienen
 * en el listado de origen.
 */

import { useState, type FormEvent } from "react";

import { Aviso, Boton, Campo, Tarjeta } from "./ui";
import { ApiError, api } from "../lib/api";
import { CATEGORIA } from "../lib/format";
import type { Afiliado, Categoria, EstadoAfiliado } from "../lib/types";

/** `<input type="date">` habla ISO; el backend manda null cuando no hay fecha. */
function paraInput(valor: string | null): string {
  return valor ? valor.slice(0, 10) : "";
}

export default function EditarAfiliado({
  afiliado,
  onGuardado,
  onCancelar,
}: {
  afiliado: Afiliado;
  onGuardado: (actualizado: Afiliado) => void;
  onCancelar: () => void;
}) {
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(
      new FormData(evento.currentTarget),
    ) as Record<string, string>;

    setGuardando(true);
    setError(null);
    try {
      const actualizado = await api.patch<Afiliado>(`/afiliados/${afiliado.id}`, {
        nombre: datos.nombre,
        rnc_cedula: datos.rnc_cedula.trim() || null,
        categoria: datos.categoria || null,
        estado: datos.estado,
        representante: datos.representante.trim() || null,
        email: datos.email.trim() || null,
        telefono: datos.telefono.trim() || null,
        direccion: datos.direccion.trim() || null,
        fecha_afiliacion: datos.fecha_afiliacion || null,
        fecha_vencimiento: datos.fecha_vencimiento || null,
        cuota_anual: datos.cuota_anual ? datos.cuota_anual : null,
        notas: datos.notas.trim() || null,
      });
      onGuardado(actualizado);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudieron guardar los cambios.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Tarjeta className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <h2 className="font-heading text-xl font-semibold">Editar ficha</h2>
        <p className="text-sm text-tinta-suave">
          El vencimiento alimenta el aviso de "próximos a vencer" y el estado que ve el afiliado en
          su portal.
        </p>
      </div>

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      <form onSubmit={guardar} className="flex flex-col gap-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Campo etiqueta="Razón social" name="nombre" defaultValue={afiliado.nombre} required />
          <Campo
            etiqueta="RNC / Cédula"
            name="rnc_cedula"
            defaultValue={afiliado.rnc_cedula ?? ""}
            placeholder="1-31-45678-9"
            ayuda={afiliado.rnc_cedula ? undefined : "No viene en el padrón."}
          />
          <Campo
            etiqueta="Representante"
            name="representante"
            defaultValue={afiliado.representante ?? ""}
          />

          <label className="flex flex-col gap-1.5">
            <span className="etiqueta">Tipo de afiliación</span>
            <select name="categoria" className="campo" defaultValue={afiliado.categoria ?? ""}>
              <option value="">Sin tipo</option>
              {(Object.keys(CATEGORIA) as Categoria[]).map((c) => (
                <option key={c} value={c}>
                  {CATEGORIA[c]}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="etiqueta">Estado</span>
            <select name="estado" className="campo" defaultValue={afiliado.estado}>
              {(["activo", "pendiente", "vencido"] as EstadoAfiliado[]).map((e) => (
                <option key={e} value={e}>
                  {e[0].toUpperCase() + e.slice(1)}
                </option>
              ))}
            </select>
          </label>

          <Campo
            etiqueta="Cuota anual"
            name="cuota_anual"
            type="number"
            step="0.01"
            min="0"
            defaultValue={afiliado.cuota_anual ?? ""}
            placeholder="45000.00"
          />

          <Campo
            etiqueta="Fecha de afiliación"
            name="fecha_afiliacion"
            type="date"
            defaultValue={paraInput(afiliado.fecha_afiliacion)}
          />
          <Campo
            etiqueta="Vence"
            name="fecha_vencimiento"
            type="date"
            defaultValue={paraInput(afiliado.fecha_vencimiento)}
            ayuda="Suele ser el 31 de diciembre del período pagado."
          />
          <Campo etiqueta="Teléfono" name="telefono" defaultValue={afiliado.telefono ?? ""} />

          <Campo
            etiqueta="Correo"
            name="email"
            type="email"
            defaultValue={afiliado.email ?? ""}
            className="sm:col-span-2"
          />
          <Campo etiqueta="Domicilio" name="direccion" defaultValue={afiliado.direccion ?? ""} />
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="etiqueta">Notas internas</span>
          <textarea
            name="notas"
            className="campo min-h-20"
            defaultValue={afiliado.notas ?? ""}
            placeholder="Lo que el staff necesite recordar de esta empresa."
          />
        </label>

        <div className="flex justify-end gap-2">
          <Boton type="button" variante="contorno" onClick={onCancelar}>
            Cancelar
          </Boton>
          <Boton type="submit" cargando={guardando}>
            Guardar cambios
          </Boton>
        </div>
      </form>
    </Tarjeta>
  );
}
