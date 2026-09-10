/**
 * Imagotipo oficial de ADECLA.
 *
 * El archivo trae el isotipo teal, la palabra "adecla" en tinta y el nombre
 * completo de la asociación debajo. Como el texto es oscuro, sobre fondos
 * oscuros no se lee: ahí el logo va dentro de una placa blanca en vez de
 * recolorearlo con filtros, que arruinaría el teal del isotipo.
 */

const RUTA = "/images/adecla-logo.png";
const ALTO = { compacto: "h-7", normal: "h-9", grande: "h-11" } as const;

export default function Logo({
  tamano = "normal",
  sobreFondoOscuro = false,
  className = "",
}: {
  tamano?: keyof typeof ALTO;
  sobreFondoOscuro?: boolean;
  className?: string;
}) {
  const imagen = (
    <img
      src={RUTA}
      alt="ADECLA · Asociación de Desarrolladores y Constructores de la Altagracia"
      className={`${ALTO[tamano]} w-auto`}
      // Reservan el espacio antes de que cargue, para que la cabecera no salte.
      width={900}
      height={290}
      decoding="async"
    />
  );

  if (!sobreFondoOscuro) return <span className={className}>{imagen}</span>;

  return (
    <span className={`inline-flex rounded-lg bg-superficie px-3 py-2 ${className}`}>{imagen}</span>
  );
}
