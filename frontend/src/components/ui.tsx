/**
 * Piezas compartidas por los dos portales.
 *
 * Todas siguen el sistema del MVP del torneo: teal como acento escaso, tarjetas
 * planas en reposo, montos y RNC en cifra tabular.
 */

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

import type { EstadoAfiliado, EstadoDocumento } from "../lib/types";
import { ESTADO_AFILIADO, ESTADO_DOCUMENTO } from "../lib/format";

/* -------------------------------------------------------------------------- */
/* Marca                                                                      */
/* -------------------------------------------------------------------------- */

export function Logo({ compacto = false, invertido = false }: { compacto?: boolean; invertido?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span
        className={`grid place-items-center rounded-lg bg-teal font-heading font-semibold text-white ${
          compacto ? "h-7 w-7 text-base" : "h-9 w-9 text-xl"
        }`}
      >
        A
      </span>
      <span
        className={`font-heading font-semibold tracking-wide ${compacto ? "text-lg" : "text-xl"} ${
          invertido ? "text-hueso" : "text-tinta"
        }`}
      >
        ADECLA
      </span>
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/* Controles                                                                  */
/* -------------------------------------------------------------------------- */

type VarianteBoton = "primario" | "contorno" | "fantasma" | "peligro";

const VARIANTES: Record<VarianteBoton, string> = {
  primario: "bg-teal-boton text-hueso hover:bg-teal-hover",
  contorno: "border border-borde text-tinta hover:border-borde-fuerte hover:bg-borde/40",
  fantasma: "text-tinta-suave hover:text-tinta hover:bg-borde/40",
  peligro: "border border-vencido/40 text-vencido hover:bg-vencido-suave",
};

interface BotonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: VarianteBoton;
  cargando?: boolean;
}

export function Boton({
  variante = "primario",
  cargando = false,
  className = "",
  children,
  disabled,
  ...resto
}: BotonProps) {
  return (
    <button
      {...resto}
      disabled={disabled || cargando}
      className={`inline-flex items-center justify-center gap-2 rounded-[8px] px-4 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-55 ${VARIANTES[variante]} ${className}`}
    >
      {cargando ? "Un momento…" : children}
    </button>
  );
}

interface CampoProps extends InputHTMLAttributes<HTMLInputElement> {
  etiqueta: string;
  ayuda?: string;
  error?: string;
}

export function Campo({ etiqueta, ayuda, error, className = "", ...resto }: CampoProps) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="etiqueta">{etiqueta}</span>
      <input
        {...resto}
        aria-invalid={error ? true : undefined}
        className={`campo ${error ? "border-vencido" : ""} ${className}`}
      />
      {error ? (
        <span className="text-xs text-vencido">{error}</span>
      ) : ayuda ? (
        <span className="text-xs text-tinta-tenue">{ayuda}</span>
      ) : null}
    </label>
  );
}

export function Selector({
  etiqueta,
  children,
  ...resto
}: { etiqueta: string; children: ReactNode } & InputHTMLAttributes<HTMLSelectElement>) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="etiqueta">{etiqueta}</span>
      <select {...(resto as object)} className="campo">
        {children}
      </select>
    </label>
  );
}

/* -------------------------------------------------------------------------- */
/* Superficies                                                                */
/* -------------------------------------------------------------------------- */

export function Tarjeta({
  children,
  className = "",
  interactiva = false,
}: {
  children: ReactNode;
  className?: string;
  interactiva?: boolean;
}) {
  return (
    <div className={`tarjeta p-6 ${interactiva ? "tarjeta-interactiva" : ""} ${className}`}>
      {children}
    </div>
  );
}

export function Metrica({
  etiqueta,
  valor,
  pie,
  acento,
  interactiva = false,
}: {
  etiqueta: string;
  valor: string | number;
  pie?: string;
  acento?: "teal" | "pendiente" | "vencido";
  interactiva?: boolean;
}) {
  const color =
    acento === "pendiente" ? "text-pendiente" : acento === "vencido" ? "text-vencido" : "text-tinta";
  return (
    <Tarjeta className="flex w-full flex-col gap-1.5" interactiva={interactiva}>
      <span className="etiqueta">{etiqueta}</span>
      <span className={`cifra font-heading text-4xl leading-none font-semibold ${color}`}>
        {valor}
      </span>
      {pie ? <span className="text-xs text-tinta-tenue">{pie}</span> : null}
    </Tarjeta>
  );
}

/* -------------------------------------------------------------------------- */
/* Estados                                                                    */
/* -------------------------------------------------------------------------- */

const TONO_AFILIADO: Record<EstadoAfiliado, string> = {
  activo: "bg-activo-suave text-activo",
  pendiente: "bg-pendiente-suave text-pendiente",
  vencido: "bg-vencido-suave text-vencido",
};

const TONO_DOCUMENTO: Record<EstadoDocumento, string> = {
  aprobado: "bg-activo-suave text-activo",
  pendiente: "bg-pendiente-suave text-pendiente",
  rechazado: "bg-vencido-suave text-vencido",
};

export function EstadoBadge({ estado }: { estado: EstadoAfiliado }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-[0.7rem] font-semibold tracking-[0.08em] uppercase ${TONO_AFILIADO[estado]}`}
    >
      {ESTADO_AFILIADO[estado]}
    </span>
  );
}

export function DocumentoBadge({ estado }: { estado: EstadoDocumento }) {
  return (
    <span
      className={`inline-flex rounded-md px-2.5 py-1 text-[0.68rem] font-semibold tracking-[0.07em] uppercase ${TONO_DOCUMENTO[estado]}`}
    >
      {ESTADO_DOCUMENTO[estado]}
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/* Mensajería                                                                 */
/* -------------------------------------------------------------------------- */

export function Aviso({
  tono = "pendiente",
  children,
}: {
  tono?: "pendiente" | "vencido" | "teal";
  children: ReactNode;
}) {
  const tonos = {
    pendiente: "bg-pendiente-suave text-tinta",
    vencido: "bg-vencido-suave text-tinta",
    teal: "bg-teal-suave text-tinta",
  };
  return (
    <div className={`rounded-[10px] px-4 py-3 text-sm ${tonos[tono]}`} role="status">
      {children}
    </div>
  );
}

export function Vacio({ titulo, detalle }: { titulo: string; detalle?: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5 py-14 text-center">
      <p className="font-heading text-lg text-tinta">{titulo}</p>
      {detalle ? <p className="max-w-sm text-sm text-tinta-tenue">{detalle}</p> : null}
    </div>
  );
}

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return <p className="py-14 text-center text-sm text-tinta-tenue">{texto}</p>;
}

/* -------------------------------------------------------------------------- */
/* Tabla                                                                      */
/* -------------------------------------------------------------------------- */

export function Tabla({ encabezados, children }: { encabezados: string[]; children: ReactNode }) {
  return (
    <div className="tarjeta overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-borde">
            {encabezados.map((h) => (
              <th key={h} className="etiqueta px-4 py-3 text-left whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
