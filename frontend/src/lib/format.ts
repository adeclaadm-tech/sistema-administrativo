import type {
  AreaContacto,
  Categoria,
  EstadoAfiliado,
  EstadoDocumento,
  TipoDocumento,
} from "./types";

const PESOS = new Intl.NumberFormat("es-DO", {
  style: "currency",
  currency: "DOP",
  minimumFractionDigits: 2,
});

export function money(valor: string | number | null | undefined): string {
  if (valor === null || valor === undefined || valor === "") return "—";
  return PESOS.format(Number(valor)).replace("DOP", "RD$");
}

/** Cifras del dashboard: RD$ 8.82M en vez de siete dígitos ilegibles. */
export function moneyCorto(valor: string | number | null | undefined): string {
  const n = Number(valor ?? 0);
  if (n >= 1_000_000) return `RD$ ${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `RD$ ${(n / 1_000).toFixed(0)}K`;
  return money(n);
}

const SOLO_FECHA = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * `new Date("2026-12-31")` se interpreta como medianoche UTC y, en Santo
 * Domingo (UTC-4), se muestra como 30 de diciembre. Las fechas sin hora que
 * manda el backend (vencimiento, fecha de pago) son días de calendario, no
 * instantes: se arman en horario local para que el día no se corra.
 * Los campos con hora (`fecha_subida`, `creado_en`) sí llevan zona y pasan
 * por el constructor normal.
 */
function aFechaLocal(valor: string): Date {
  const partes = SOLO_FECHA.exec(valor);
  if (!partes) return new Date(valor);
  return new Date(Number(partes[1]), Number(partes[2]) - 1, Number(partes[3]));
}

export function fecha(valor: string | null | undefined): string {
  if (!valor) return "—";
  return aFechaLocal(valor).toLocaleDateString("es-DO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function fechaCorta(valor: string | null | undefined): string {
  if (!valor) return "—";
  return aFechaLocal(valor).toLocaleDateString("es-DO", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
  });
}

export function pesoArchivo(bytes: number | null | undefined): string {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const ESTADO_AFILIADO: Record<EstadoAfiliado, string> = {
  activo: "Activo",
  pendiente: "Pendiente",
  vencido: "Vencido",
};

export const ESTADO_DOCUMENTO: Record<EstadoDocumento, string> = {
  pendiente: "En revisión",
  aprobado: "Aprobado",
  rechazado: "Rechazado",
};

export const CATEGORIA: Record<Categoria, string> = {
  clase_a: "Clase A",
  clase_b: "Clase B",
  clase_c: "Clase C",
};

export const TIPO_DOCUMENTO: Record<TipoDocumento, string> = {
  rnc_nid: "Registro Nacional del Contribuyente",
  cedula: "Cédula del representante",
  soporte_pago: "Soporte de pago de la cuota",
  doc_representante: "Documentos del representante",
};

export const PISTA_DOCUMENTO: Record<TipoDocumento, string> = {
  rnc_nid: "RNC / NID",
  cedula: "Ambas caras",
  soporte_pago: "Comprobante",
  doc_representante: "Poder o acta",
};

export const AREA_CONTACTO: Record<AreaContacto, string> = {
  contabilidad: "Contabilidad",
  marketing: "Marketing",
  comercial: "Comercial",
};

/** Frase de la cabecera del portal según el estado de la afiliación. */
export function notaEstado(estado: EstadoAfiliado, dias: number | null): string {
  if (estado === "activo") {
    const cola = dias !== null ? ` Te quedan ${dias} días.` : "";
    return `Tu afiliación está vigente.${cola} La proforma de renovación te llega 30 días antes del vencimiento.`;
  }
  if (estado === "pendiente") {
    return "Tu renovación está en revisión. Falta validar el soporte de pago de la cuota.";
  }
  const cola = dias !== null ? ` Venció hace ${Math.abs(dias)} días.` : "";
  return `Tu afiliación venció.${cola} Sube el soporte de pago para reactivarla.`;
}
