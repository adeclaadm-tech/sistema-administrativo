/** Pantalla 1h: ficha completa, revisión de documentos y registro de pago. */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Aviso,
  Boton,
  Campo,
  Cargando,
  DocumentoBadge,
  EstadoBadge,
  Tarjeta,
  Vacio,
} from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import EditarAfiliado from "../../components/EditarAfiliado";
import {
  AREA_CONTACTO,
  categoriaTexto,
  PISTA_DOCUMENTO,
  TIPO_DOCUMENTO,
  fecha,
  money,
} from "../../lib/format";
import { useAuth } from "../../lib/auth";
import type { Afiliado, Documento, Pagina, Pago, Proforma } from "../../lib/types";

function Dato({ etiqueta, valor, mono = false }: { etiqueta: string; valor: string; mono?: boolean }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="etiqueta">{etiqueta}</span>
      <span className={mono ? "cifra font-mono text-sm" : "text-sm"}>{valor}</span>
    </div>
  );
}

export default function AfiliadoDetalle() {
  const { id = "" } = useParams();
  const { puedeEscribir } = useAuth();

  const [afiliado, setAfiliado] = useState<Afiliado | null>(null);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [pagos, setPagos] = useState<Pago[]>([]);
  const [proformas, setProformas] = useState<Proforma[]>([]);
  const [formularioPago, setFormularioPago] = useState(false);
  const [editando, setEditando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(() => {
    api.get<Afiliado>(`/afiliados/${id}`).then(setAfiliado).catch(() => setAfiliado(null));
    api
      .get<Pagina<Documento>>("/documentos", { afiliado_id: id, per_page: 50 })
      .then((p) => setDocumentos(p.items))
      .catch(() => setDocumentos([]));
    api
      .get<Pagina<Pago>>("/pagos", { afiliado_id: id, per_page: 50 })
      .then((p) => setPagos(p.items))
      .catch(() => setPagos([]));
    api
      .get<Proforma[]>("/proformas", { afiliado_id: id })
      .then(setProformas)
      .catch(() => setProformas([]));
  }, [id]);

  useEffect(cargar, [cargar]);

  async function revisar(documentoId: string, aprobado: boolean) {
    setError(null);
    const motivo = aprobado
      ? null
      : window.prompt("¿Por qué se rechaza? El afiliado va a leer este mensaje.");
    if (!aprobado && !motivo) return;
    try {
      await api.post(`/documentos/${documentoId}/revision`, { aprobado, motivo_rechazo: motivo });
      cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo guardar la revisión.");
    }
  }

  async function registrarPago(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;
    setGuardando(true);
    setError(null);
    try {
      const respuesta = await api.post<{ proforma_numero: string | null }>(
        `/pagos/afiliado/${id}`,
        {
          monto: datos.monto,
          fecha: datos.fecha,
          metodo: datos.metodo,
          referencia: datos.referencia || null,
          concepto: datos.concepto || null,
          periodo: datos.periodo ? Number(datos.periodo) : null,
          generar_proforma: true,
          renovar_afiliacion: datos.renovar === "on",
        },
      );
      setMensaje(
        respuesta.proforma_numero
          ? `Pago registrado. Proforma ${respuesta.proforma_numero} emitida.`
          : "Pago registrado.",
      );
      setFormularioPago(false);
      cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo registrar el pago.");
    } finally {
      setGuardando(false);
    }
  }

  if (!afiliado) return <Cargando />;

  const proformaDe = new Map(proformas.filter((p) => p.pago_id).map((p) => [p.pago_id, p]));
  const porRevisar = documentos.filter((d) => d.estado === "pendiente").length;
  const contactos = new Map(afiliado.contactos.map((c) => [c.area, c]));

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex items-center gap-2 text-sm text-tinta-suave">
        <Link to="/admin/afiliados" className="hover:text-tinta">
          Afiliados
        </Link>
        <span>/</span>
        <span className="text-tinta">{afiliado.nombre}</span>
      </nav>

      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="etiqueta">
            {afiliado.fecha_afiliacion
              ? `Miembro desde ${new Date(afiliado.fecha_afiliacion).getFullYear()}`
              : "Sin fecha de afiliación"}
          </span>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-heading text-3xl font-semibold">{afiliado.nombre}</h1>
            <EstadoBadge estado={afiliado.estado} />
          </div>
        </div>
        {puedeEscribir ? (
          <div className="flex gap-2">
            <Boton
              variante="contorno"
              onClick={() => {
                setEditando((v) => !v);
                setFormularioPago(false);
              }}
            >
              {editando ? "Cerrar edición" : "Editar ficha"}
            </Boton>
            <Boton onClick={() => setFormularioPago((v) => !v)}>
              {formularioPago ? "Cancelar" : "Registrar pago"}
            </Boton>
          </div>
        ) : (
          <span className="text-xs text-tinta-tenue">Perfil de consulta · solo lectura</span>
        )}
      </header>

      {mensaje ? <Aviso tono="teal">{mensaje}</Aviso> : null}
      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      {editando && puedeEscribir ? (
        <EditarAfiliado
          afiliado={afiliado}
          onCancelar={() => setEditando(false)}
          onGuardado={(actualizado) => {
            setAfiliado(actualizado);
            setEditando(false);
            setMensaje("Ficha actualizada.");
          }}
        />
      ) : null}

      {formularioPago && puedeEscribir ? (
        <Tarjeta className="flex flex-col gap-5">
          <h2 className="font-heading text-xl font-semibold">Registrar pago</h2>
          <form onSubmit={registrarPago} className="flex flex-col gap-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Campo
                etiqueta="Monto"
                name="monto"
                type="number"
                step="0.01"
                min="0"
                defaultValue={afiliado.cuota_anual ?? ""}
                required
              />
              <Campo
                etiqueta="Fecha"
                name="fecha"
                type="date"
                defaultValue={new Date().toISOString().slice(0, 10)}
                required
              />
              <label className="flex flex-col gap-1.5">
                <span className="etiqueta">Método</span>
                <select name="metodo" className="campo" defaultValue="transferencia">
                  <option value="transferencia">Transferencia</option>
                  <option value="cheque">Cheque</option>
                  <option value="efectivo">Efectivo</option>
                  <option value="tarjeta">Tarjeta</option>
                  <option value="otro">Otro</option>
                </select>
              </label>
              <Campo etiqueta="Referencia" name="referencia" placeholder="TRF-884210" />
              <Campo
                etiqueta="Período"
                name="periodo"
                type="number"
                defaultValue={new Date().getFullYear()}
              />
              <Campo etiqueta="Concepto" name="concepto" placeholder="Cuota anual" />
            </div>

            <label className="flex items-center gap-2 text-sm text-tinta-suave">
              <input type="checkbox" name="renovar" defaultChecked className="accent-teal-boton" />
              Renovar la afiliación: mueve el vencimiento al 31 de diciembre del período y la deja
              activa.
            </label>

            <div className="flex justify-end">
              <Boton type="submit" cargando={guardando}>
                Registrar y emitir proforma
              </Boton>
            </div>
          </form>
        </Tarjeta>
      ) : null}

      <Tarjeta className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Dato etiqueta="RNC" valor={afiliado.rnc_cedula ?? "—"} mono />
        <Dato etiqueta="Representante" valor={afiliado.representante ?? "—"} />
        <Dato etiqueta="Tipo" valor={categoriaTexto(afiliado.categoria)} />
        <Dato etiqueta="Vence" valor={fecha(afiliado.fecha_vencimiento)} mono />
        <Dato etiqueta="Correo" valor={afiliado.email ?? "—"} />
        <Dato etiqueta="Teléfono" valor={afiliado.telefono ?? "—"} mono />
        <Dato etiqueta="Domicilio" valor={afiliado.direccion ?? "—"} />
        <Dato etiqueta="Cuota anual" valor={money(afiliado.cuota_anual)} mono />
      </Tarjeta>

      <Tarjeta className="flex flex-col gap-5">
        <h2 className="font-heading text-xl font-semibold">Contactos por área</h2>
        <div className="grid gap-5 md:grid-cols-3">
          {(["contabilidad", "marketing", "comercial"] as const).map((area) => {
            const contacto = contactos.get(area);
            return (
              <div key={area} className="flex flex-col gap-1.5 border-l-2 border-teal-suave pl-4">
                <span className="etiqueta">{AREA_CONTACTO[area]}</span>
                {contacto ? (
                  <>
                    <span className="font-medium">{contacto.nombre}</span>
                    <span className="text-sm text-tinta-suave">{contacto.cargo ?? "—"}</span>
                    <span className="cifra font-mono text-xs text-tinta-suave">
                      {contacto.telefono ?? "—"}
                    </span>
                    <span className="text-xs break-all text-tinta-suave">{contacto.email ?? "—"}</span>
                  </>
                ) : (
                  <span className="text-sm text-tinta-tenue">Sin contacto registrado.</span>
                )}
              </div>
            );
          })}
        </div>
      </Tarjeta>

      <div className="grid gap-5 xl:grid-cols-2">
        <Tarjeta className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl font-semibold">Documentos subidos</h2>
            {porRevisar > 0 ? (
              <span className="font-mono text-[0.68rem] tracking-wider text-pendiente uppercase">
                {porRevisar} por revisar
              </span>
            ) : null}
          </div>

          {documentos.length === 0 ? (
            <Vacio titulo="Sin documentos" detalle="El afiliado todavía no ha subido nada." />
          ) : (
            <ul className="flex flex-col divide-y divide-borde">
              {documentos.map((doc) => (
                <li key={doc.id} className="flex flex-wrap items-center gap-3 py-3">
                  <div className="flex min-w-48 flex-1 flex-col gap-0.5">
                    <span className="text-sm font-medium">{TIPO_DOCUMENTO[doc.tipo]}</span>
                    <span className="cifra font-mono text-[0.68rem] text-tinta-tenue">
                      {PISTA_DOCUMENTO[doc.tipo]} · {doc.nombre_archivo ?? "sin archivo"}
                    </span>
                  </div>
                  <DocumentoBadge estado={doc.estado} />
                  {doc.url ? (
                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-teal-boton hover:underline"
                    >
                      Ver
                    </a>
                  ) : null}
                  {puedeEscribir && doc.estado === "pendiente" ? (
                    <span className="flex gap-1">
                      <Boton variante="fantasma" onClick={() => void revisar(doc.id, true)}>
                        Aprobar
                      </Boton>
                      <Boton
                        variante="fantasma"
                        className="text-vencido"
                        onClick={() => void revisar(doc.id, false)}
                      >
                        Rechazar
                      </Boton>
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>

        <Tarjeta className="flex flex-col gap-4">
          <h2 className="font-heading text-xl font-semibold">Historial de pagos</h2>

          {pagos.length === 0 ? (
            <Vacio titulo="Sin pagos" detalle="Registra el primer pago desde el botón de arriba." />
          ) : (
            // Cinco columnas dentro de media tarjeta: sin scroll propio, el
            // método y el monto terminan pegados uno al otro.
            <div className="-mx-2 overflow-x-auto px-2">
              <table className="w-full min-w-[26rem] text-sm">
                <thead>
                  <tr className="border-b border-borde">
                    <th className="etiqueta py-2 pr-4 text-left">Período</th>
                    <th className="etiqueta py-2 pr-4 text-left">Proforma</th>
                    <th className="etiqueta py-2 pr-4 text-left">Fecha</th>
                    <th className="etiqueta py-2 pr-4 text-left">Método</th>
                    <th className="etiqueta py-2 pl-4 text-right">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {pagos.map((pago) => (
                    <tr key={pago.id} className="border-b border-borde last:border-0">
                      <td className="py-3 pr-4">{pago.concepto ?? `Cuota ${pago.periodo ?? ""}`}</td>
                      <td className="cifra py-3 pr-4 font-mono text-xs whitespace-nowrap text-tinta-suave">
                        {proformaDe.get(pago.id)?.numero ?? "—"}
                      </td>
                      <td className="py-3 pr-4 whitespace-nowrap text-tinta-suave">
                        {fecha(pago.fecha)}
                      </td>
                      <td className="py-3 pr-4 text-tinta-suave capitalize">{pago.metodo}</td>
                      <td className="cifra py-3 pl-4 text-right font-mono whitespace-nowrap">
                        {money(pago.monto)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Tarjeta>
      </div>
    </div>
  );
}
