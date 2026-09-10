/**
 * Mi perfil: datos de la empresa y los tres contactos por área.
 *
 * El RNC, la categoría y las fechas no se editan desde aquí: eso lo mueve el
 * staff desde el panel.
 */

import { useEffect, useState, type FormEvent } from "react";

import { Aviso, Boton, Campo, Cargando, Tarjeta } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { AREA_CONTACTO, categoriaTexto, fecha } from "../../lib/format";
import type { Afiliado, AreaContacto, ResumenAfiliado } from "../../lib/types";

const AREAS: AreaContacto[] = ["contabilidad", "marketing", "comercial"];

type FormaContacto = { nombre: string; cargo: string; telefono: string; email: string };
const CONTACTO_VACIO: FormaContacto = { nombre: "", cargo: "", telefono: "", email: "" };

export default function Perfil() {
  const [afiliado, setAfiliado] = useState<Afiliado | null>(null);
  const [contactos, setContactos] = useState<Record<AreaContacto, FormaContacto>>({
    contabilidad: { ...CONTACTO_VACIO },
    marketing: { ...CONTACTO_VACIO },
    comercial: { ...CONTACTO_VACIO },
  });
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<ResumenAfiliado>("/afiliados/me").then(({ afiliado }) => {
      setAfiliado(afiliado);
      setContactos((previos) => {
        const copia = { ...previos };
        for (const c of afiliado.contactos) {
          copia[c.area] = {
            nombre: c.nombre ?? "",
            cargo: c.cargo ?? "",
            telefono: c.telefono ?? "",
            email: c.email ?? "",
          };
        }
        return copia;
      });
    });
  }, []);

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;
    setGuardando(true);
    setMensaje(null);
    setError(null);

    // Solo se mandan las áreas con nombre: una sección vacía se deja como está.
    const payloadContactos: Record<string, unknown> = {};
    for (const area of AREAS) {
      const c = contactos[area];
      if (c.nombre.trim()) {
        payloadContactos[area] = {
          nombre: c.nombre.trim(),
          cargo: c.cargo.trim() || null,
          telefono: c.telefono.trim() || null,
          email: c.email.trim() || null,
        };
      }
    }

    try {
      const actualizado = await api.patch<Afiliado>("/afiliados/me", {
        representante: datos.representante || null,
        email: datos.email || null,
        telefono: datos.telefono || null,
        direccion: datos.direccion || null,
        contactos: Object.keys(payloadContactos).length ? payloadContactos : undefined,
      });
      setAfiliado(actualizado);
      setMensaje("Datos actualizados.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No pudimos guardar los cambios.");
    } finally {
      setGuardando(false);
    }
  }

  if (!afiliado) return <Cargando />;

  return (
    <form onSubmit={guardar} className="mx-auto flex max-w-3xl flex-col gap-7">
      <header className="flex flex-col gap-2">
        <span className="etiqueta">Mi perfil</span>
        <h1 className="font-heading text-3xl font-semibold">{afiliado.nombre}</h1>
        <p className="cifra font-mono text-xs tracking-wide text-tinta-suave">
          RNC {afiliado.rnc_cedula ?? "pendiente"} · {categoriaTexto(afiliado.categoria)} · vence{" "}
          {fecha(afiliado.fecha_vencimiento)}
        </p>
      </header>

      {mensaje ? <Aviso tono="teal">{mensaje}</Aviso> : null}
      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      <Tarjeta className="flex flex-col gap-5">
        <h2 className="font-heading text-xl font-semibold">Datos de la empresa</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Representante" name="representante" defaultValue={afiliado.representante ?? ""} />
          <Campo etiqueta="Correo" name="email" type="email" defaultValue={afiliado.email ?? ""} />
          <Campo etiqueta="Teléfono" name="telefono" defaultValue={afiliado.telefono ?? ""} />
          <Campo etiqueta="Domicilio" name="direccion" defaultValue={afiliado.direccion ?? ""} />
        </div>
        <p className="text-xs text-tinta-tenue">
          El RNC, la categoría y las fechas de afiliación las administra el equipo de ADECLA. Si algo
          está mal, escríbeles.
        </p>
      </Tarjeta>

      <Tarjeta className="flex flex-col gap-6">
        <div className="flex flex-col gap-1.5">
          <h2 className="font-heading text-xl font-semibold">Contactos por área</h2>
          <p className="text-sm text-tinta-suave">
            Con quién habla ADECLA en cada departamento. Sirve para cobros, convocatorias a eventos y
            oportunidades comerciales.
          </p>
        </div>

        {AREAS.map((area) => (
          <fieldset key={area} className="flex flex-col gap-4 border-t border-borde pt-5 first:border-0 first:pt-0">
            <legend className="etiqueta">{AREA_CONTACTO[area]}</legend>
            <div className="grid gap-4 sm:grid-cols-2">
              {(
                [
                  ["nombre", "Nombre", "Nombre y apellido"],
                  ["cargo", "Cargo", "Encargada de cuentas por cobrar"],
                  ["telefono", "Teléfono", "809-552-0114"],
                  ["email", "Correo electrónico", "nombre@empresa.do"],
                ] as const
              ).map(([campo, etiqueta, ejemplo]) => (
                <Campo
                  key={campo}
                  etiqueta={etiqueta}
                  placeholder={ejemplo}
                  type={campo === "email" ? "email" : "text"}
                  value={contactos[area][campo]}
                  onChange={(e) =>
                    setContactos((previos) => ({
                      ...previos,
                      [area]: { ...previos[area], [campo]: e.target.value },
                    }))
                  }
                />
              ))}
            </div>
          </fieldset>
        ))}
      </Tarjeta>

      <div className="flex justify-end">
        <Boton type="submit" cargando={guardando}>
          Guardar cambios
        </Boton>
      </div>
    </form>
  );
}
