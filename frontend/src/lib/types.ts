/** Tipos que devuelve el backend. Reflejan los schemas de Pydantic. */

export type Rol = "afiliado" | "admin";
export type SubRol = "administrador" | "consultor";
export type EstadoAfiliado = "activo" | "pendiente" | "vencido";
export type Categoria = "clase_a" | "clase_b" | "clase_c";
export type TipoDocumento = "rnc_nid" | "cedula" | "soporte_pago" | "doc_representante";
export type EstadoDocumento = "pendiente" | "aprobado" | "rechazado";
export type AreaContacto = "contabilidad" | "marketing" | "comercial";
export type MetodoPago = "transferencia" | "cheque" | "efectivo" | "tarjeta" | "otro";

export interface Usuario {
  id: string;
  email: string;
  nombre: string;
  rol: Rol;
  sub_rol: SubRol | null;
  activo: boolean;
  creado_en: string;
}

export interface Sesion {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  usuario: Usuario;
  afiliado_id: string | null;
}

export interface Contacto {
  id: string;
  afiliado_id: string;
  area: AreaContacto;
  nombre: string;
  cargo: string | null;
  telefono: string | null;
  email: string | null;
}

export interface Afiliado {
  id: string;
  usuario_id: string | null;
  nombre: string;
  rnc_cedula: string;
  categoria: Categoria;
  estado: EstadoAfiliado;
  representante: string | null;
  email: string | null;
  telefono: string | null;
  direccion: string | null;
  fecha_afiliacion: string | null;
  fecha_vencimiento: string | null;
  cuota_anual: string | null;
  notas: string | null;
  contactos: Contacto[];
  creado_en: string;
  actualizado_en: string;
}

export interface AfiliadoFila {
  id: string;
  nombre: string;
  rnc_cedula: string;
  representante: string | null;
  categoria: Categoria;
  estado: EstadoAfiliado;
  fecha_vencimiento: string | null;
}

export interface ResumenAfiliado {
  afiliado: Afiliado;
  dias_para_vencer: number | null;
  progreso_anual: number;
  documentos_aprobados: number;
  documentos_totales: number;
  documentos_pendientes: number;
  ultimo_pago: string | null;
}

export interface Documento {
  id: string;
  afiliado_id: string;
  tipo: TipoDocumento;
  estado: EstadoDocumento;
  nombre_archivo: string | null;
  content_type: string | null;
  tamano_bytes: number | null;
  fecha_subida: string;
  fecha_revision: string | null;
  motivo_rechazo: string | null;
  url: string | null;
}

export interface DocumentoEnCola {
  id: string;
  afiliado_id: string;
  afiliado_nombre: string;
  tipo: TipoDocumento;
  nombre_archivo: string | null;
  fecha_subida: string;
  dias_en_espera: number;
}

export interface Pago {
  id: string;
  afiliado_id: string;
  monto: string;
  moneda: string;
  fecha: string;
  metodo: MetodoPago;
  referencia: string | null;
  concepto: string | null;
  periodo: number | null;
  comprobante_url: string | null;
  notas: string | null;
  registrado_por_usuario_id: string | null;
  creado_en: string;
}

export interface Proforma {
  id: string;
  afiliado_id: string;
  pago_id: string | null;
  numero: string;
  fecha_generacion: string;
  monto: string | null;
  concepto: string | null;
  pdf_url: string | null;
  url: string | null;
}

export interface Metricas {
  total_afiliados: number;
  activos: number;
  pendientes: number;
  vencidos: number;
  proximos_a_vencer: number;
  documentos_por_revisar: number;
  nuevos_en_el_ano: number;
  recaudado_periodo: string;
  variacion_recaudacion: number | null;
}

export interface FilaCategoria {
  categoria: Categoria;
  total: number;
  activos: number;
  pendientes: number;
  vencidos: number;
  recaudado: string;
}

export interface BarraMes {
  mes: string;
  anio: number;
  activos: number;
  pendientes: number;
  vencidos: number;
  recaudado: string;
}

export interface ReporteResumen {
  tipo: string;
  desde: string | null;
  hasta: string | null;
  nuevas_afiliaciones: number;
  renovaciones: number;
  bajas: number;
  recaudado: string;
  por_mes: BarraMes[];
  por_categoria: FilaCategoria[];
  total_afiliados: number;
}

export interface Pagina<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
