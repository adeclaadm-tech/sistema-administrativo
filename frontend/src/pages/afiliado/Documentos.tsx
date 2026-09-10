/** Pantalla 1c: carga de documentos con el estado de cada uno. */

import { useEffect, useRef, useState } from "react";

import { Aviso, Boton, Cargando, DocumentoBadge, Tarjeta } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { PISTA_DOCUMENTO, TIPO_DOCUMENTO, fecha, pesoArchivo } from "../../lib/format";
import type { Documento, TipoDocumento } from "../../lib/types";

const REQUERIDOS: TipoDocumento[] = ["rnc_nid", "cedula", "soporte_pago", "doc_representante"];

export default function Documentos() {
  const [documentos, setDocumentos] = useState<Documento[] | null>(null);
  const [subiendo, setSubiendo] = useState<TipoDocumento | null>(null);
  const [error, setError] = useState<string | null>(null);
  const referencias = useRef<Record<string, HTMLInputElement | null>>({});

  const cargar = () =>
    api.get<Documento[]>("/documentos/me").then(setDocumentos).catch(() => setDocumentos([]));

  useEffect(() => {
    void cargar();
  }, []);

  async function subir(tipo: TipoDocumento, archivo: File) {
    setSubiendo(tipo);
    setError(null);
    const cuerpo = new FormData();
    cuerpo.append("tipo", tipo);
    cuerpo.append("archivo", archivo);
    try {
      await api.post("/documentos/me", cuerpo);
      await cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No pudimos subir el archivo.");
    } finally {
      setSubiendo(null);
    }
  }

  if (!documentos) return <Cargando />;

  const porTipo = new Map(documentos.map((d) => [d.tipo, d]));
  const rechazados = documentos.filter((d) => d.estado === "rechazado");
  const pendientes = documentos.filter((d) => d.estado === "pendiente");

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-7">
      <header className="flex flex-col gap-2.5">
        <h1 className="font-heading text-3xl">Carga de documentos</h1>
        <p className="max-w-xl leading-relaxed text-tinta-suave">
          Sube los cuatro documentos requeridos para mantener tu afiliación vigente. Formatos PDF,
          JPG o PNG, hasta 10 MB por archivo. El equipo de ADECLA revisa cada carga en un plazo de 3
          días laborables.
        </p>
      </header>

      {rechazados.length > 0 ? (
        <Aviso tono="vencido">
          <strong className="font-semibold">
            {rechazados.length === 1 ? "1 documento rechazado." : `${rechazados.length} documentos rechazados.`}
          </strong>{" "}
          {rechazados[0].motivo_rechazo ?? "Vuelve a subirlo para completar la renovación."}
        </Aviso>
      ) : pendientes.length > 0 ? (
        <Aviso>
          <strong className="font-semibold">
            {pendientes.length === 1 ? "1 documento en revisión." : `${pendientes.length} documentos en revisión.`}
          </strong>{" "}
          Te avisamos por correo en cuanto el equipo los valide.
        </Aviso>
      ) : null}

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      <div className="flex flex-col gap-4">
        {REQUERIDOS.map((tipo) => {
          const doc = porTipo.get(tipo);
          const esteSubiendo = subiendo === tipo;

          return (
            <Tarjeta
              key={tipo}
              className={`flex flex-wrap items-center gap-5 ${
                doc?.estado === "rechazado" ? "border-vencido" : ""
              }`}
            >
              <span className="grid h-13 w-10 items-end justify-center rounded-md border border-borde bg-hueso pb-1.5 font-mono text-[0.6rem] text-tinta-tenue">
                {doc?.content_type?.includes("pdf") ? "PDF" : doc ? "IMG" : "—"}
              </span>

              <div className="flex min-w-52 flex-1 flex-col gap-1">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="font-semibold">{TIPO_DOCUMENTO[tipo]}</span>
                  <span className="font-mono text-[0.6rem] tracking-wider text-tinta-tenue uppercase">
                    {PISTA_DOCUMENTO[tipo]}
                  </span>
                </div>
                <span className="cifra font-mono text-xs text-tinta-suave">
                  {doc
                    ? `${doc.nombre_archivo ?? "archivo"} · ${pesoArchivo(doc.tamano_bytes)} · subido ${fecha(doc.fecha_subida)}`
                    : "Sin archivo"}
                </span>
                {doc?.estado === "rechazado" && doc.motivo_rechazo ? (
                  <span className="text-xs text-vencido">{doc.motivo_rechazo}</span>
                ) : null}
              </div>

              {doc ? <DocumentoBadge estado={doc.estado} /> : null}

              <input
                ref={(el) => {
                  referencias.current[tipo] = el;
                }}
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                className="hidden"
                onChange={(e) => {
                  const archivo = e.target.files?.[0];
                  if (archivo) void subir(tipo, archivo);
                  e.target.value = "";
                }}
              />
              <Boton
                variante={doc ? "fantasma" : "primario"}
                cargando={esteSubiendo}
                onClick={() => referencias.current[tipo]?.click()}
              >
                {doc ? "Reemplazar" : "Subir archivo"}
              </Boton>
            </Tarjeta>
          );
        })}
      </div>
    </div>
  );
}
