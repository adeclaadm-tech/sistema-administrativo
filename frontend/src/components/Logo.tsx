/**
 * Imagotipo oficial de ADECLA.
 *
 * Sobre fondo oscuro va en blanco de una tinta, no dentro de una placa
 * blanca: la placa metía un rectángulo ajeno en medio del bloque teal y se
 * comía la composición. El logo monocromo es un uso previsto en cualquier
 * manual de marca y se integra con el fondo en vez de pelearse con él.
 */

const RUTA = "/images/adecla-logo.png";
const ALTO = { compacto: "h-7", normal: "h-9", grande: "h-12" } as const;

export default function Logo({
  tamano = "normal",
  sobreFondoOscuro = false,
  className = "",
}: {
  tamano?: keyof typeof ALTO;
  sobreFondoOscuro?: boolean;
  className?: string;
}) {
  return (
    <img
      src={RUTA}
      alt="ADECLA · Asociación de Desarrolladores y Constructores de la Altagracia"
      // brightness-0 lleva todo a negro e invert lo sube a blanco: deja el
      // imagotipo completo en una sola tinta, isotipo incluido.
      className={`${ALTO[tamano]} w-auto ${sobreFondoOscuro ? "brightness-0 invert" : ""} ${className}`}
      // Reservan el espacio antes de que cargue, para que la cabecera no salte.
      width={900}
      height={290}
      decoding="async"
    />
  );
}
