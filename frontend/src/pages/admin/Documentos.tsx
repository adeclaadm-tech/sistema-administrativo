/** Cola completa de revisión de documentos. */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Aviso, Boton, Cargando, Tabla, Tarjeta, Vacio } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { TIPO_DOCUMENTO, fecha } from "../../lib/format";
import { useAuth } from "../../lib/auth";
import type { DocumentoEnCola } from "../../lib/types";

export default function DocumentosAdmin() {
  const { puedeEscribir } = useAuth();
  const [cola, setCola] = useState<DocumentoEnCola[] | null>(null);
  const [procesando, setProcesando] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api
      .get<DocumentoEnCola[]>("/documentos/cola", { limite: 100 })
      .then(setCola)
      .catch(() => setCola([]));
  }, []);

  useEffect(cargar, [cargar]);

  async function revisar(id: string, aprobado: boolean) {
    const motivo = aprobado
      ? null
      : window.prompt("¿Por qué se rechaza? El afiliado va a leer este mensaje.");
    if (!aprobado && !motivo) return;

    setProcesando(id);
    setError(null);
    try {
      await api.post(`/documentos/${id}/revision`, { aprobado, motivo_rechazo: motivo });
      cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo guardar la revisión.");
    } finally {
      setProcesando(null);
    }
  }

  if (!cola) return <Cargando />;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <span className="etiqueta">{cola.length} en cola</span>
        <h1 className="font-heading text-3xl font-semibold">Documentos por revisar</h1>
      </header>

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      {cola.length === 0 ? (
        <Tarjeta>
          <Vacio titulo="La cola está vacía" detalle="Todos los documentos subidos ya fueron revisados." />
        </Tarjeta>
      ) : (
        <Tabla encabezados={["Afiliado", "Documento", "Archivo", "Subido", "Espera", ""]}>
          {cola.map((fila) => (
            <tr key={fila.id} className="border-b border-borde last:border-0 hover:bg-hueso">
              <td className="px-4 py-3">
                <Link to={`/admin/afiliados/${fila.afiliado_id}`} className="hover:text-teal-boton">
                  {fila.afiliado_nombre}
                </Link>
              </td>
              <td className="px-4 py-3 text-tinta-suave">{TIPO_DOCUMENTO[fila.tipo]}</td>
              <td className="px-4 py-3 font-mono text-xs text-tinta-tenue">
                {fila.nombre_archivo ?? "—"}
              </td>
              <td className="px-4 py-3 text-tinta-suave">{fecha(fila.fecha_subida)}</td>
              <td
                className={`cifra px-4 py-3 font-mono text-xs ${
                  fila.dias_en_espera >= 3 ? "text-vencido" : "text-tinta-suave"
                }`}
              >
                {fila.dias_en_espera === 0 ? "HOY" : `${fila.dias_en_espera} D`}
              </td>
              <td className="px-4 py-3 text-right">
                {puedeEscribir ? (
                  <span className="inline-flex gap-1">
                    <Boton
                      variante="fantasma"
                      cargando={procesando === fila.id}
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
        </Tabla>
      )}
    </div>
  );
}
