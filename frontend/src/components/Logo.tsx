/**
 * Imagotipo de ADECLA para la interfaz.
 *
 * Se usa la versión sin el nombre completo debajo. En pantalla el logo vive
 * entre 28 y 48 px de alto, y a esa escala esa línea no se lee: queda como una
 * mancha gris que ensucia el bloque. El nombre completo aparece escrito aparte
 * donde hace falta —el pie del portal y el hero del login—, así que no se
 * pierde nada. El archivo con la línea se reserva para el PDF de la proforma,
 * que se imprime a tamaño suficiente.
 *
 * Sobre fondo oscuro va en blanco de una tinta. Es un uso previsto en
 * cualquier manual de marca y se integra con el fondo, a diferencia de meterlo
 * dentro de una placa blanca.
 */

const RUTA = "/images/adecla-logo-simple.png";
const ALTO = { compacto: "h-6", normal: "h-8", grande: "h-10" } as const;

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
    // El envoltorio con `w-fit` es lo que protege la proporción: como hijo
    // directo de un contenedor flex en columna, la imagen se estira a todo el
    // ancho disponible (align-items: stretch) y el logo sale deformado.
    <span className={`flex w-fit shrink-0 items-center ${className}`}>
      <img
        src={RUTA}
        alt="ADECLA"
        // brightness-0 lleva todo a negro e invert lo sube a blanco: deja el
        // imagotipo en una sola tinta, isotipo incluido.
        className={`${ALTO[tamano]} w-auto ${sobreFondoOscuro ? "brightness-0 invert" : ""}`}
        // Reservan el espacio antes de que cargue, para que la cabecera no salte.
        width={720}
        height={146}
        decoding="async"
      />
    </span>
  );
}
