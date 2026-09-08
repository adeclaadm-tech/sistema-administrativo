/** Cuentas del panel. Solo las ve y las toca un administrador. */

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { Aviso, Boton, Campo, Cargando, Tabla, Tarjeta } from "../../components/ui";
import { ApiError, api } from "../../lib/api";
import { fecha } from "../../lib/format";
import type { Usuario } from "../../lib/types";

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[] | null>(null);
  const [creando, setCreando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api.get<Usuario[]>("/usuarios").then(setUsuarios).catch(() => setUsuarios([]));
  }, []);

  useEffect(cargar, [cargar]);

  async function crear(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = Object.fromEntries(new FormData(formulario)) as Record<string, string>;
    setGuardando(true);
    setError(null);
    try {
      await api.post("/usuarios", datos);
      formulario.reset();
      setCreando(false);
      cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo crear la cuenta.");
    } finally {
      setGuardando(false);
    }
  }

  async function alternar(usuario: Usuario) {
    setError(null);
    try {
      await api.patch(`/usuarios/${usuario.id}`, { activo: !usuario.activo });
      cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo actualizar la cuenta.");
    }
  }

  if (!usuarios) return <Cargando />;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="etiqueta">{usuarios.length} cuentas</span>
          <h1 className="font-heading text-3xl font-semibold">Usuarios del staff</h1>
        </div>
        <Boton onClick={() => setCreando((v) => !v)}>
          {creando ? "Cancelar" : "Nueva cuenta"}
        </Boton>
      </header>

      {error ? <Aviso tono="vencido">{error}</Aviso> : null}

      {creando ? (
        <Tarjeta className="flex flex-col gap-5">
          <form onSubmit={crear} className="flex flex-col gap-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Campo etiqueta="Nombre" name="nombre" required />
              <Campo etiqueta="Correo institucional" name="email" type="email" required />
              <Campo
                etiqueta="Contraseña"
                name="password"
                type="password"
                minLength={8}
                ayuda="Mínimo 8 caracteres."
                required
              />
              <label className="flex flex-col gap-1.5">
                <span className="etiqueta">Permisos</span>
                <select name="sub_rol" className="campo" defaultValue="consultor">
                  <option value="consultor">Consultor · consulta y exporta</option>
                  <option value="administrador">Administrador · gestiona todo</option>
                </select>
              </label>
            </div>
            <div className="flex justify-end">
              <Boton type="submit" cargando={guardando}>
                Crear cuenta
              </Boton>
            </div>
          </form>
        </Tarjeta>
      ) : null}

      <Tabla encabezados={["Nombre", "Correo", "Permisos", "Alta", "Estado", ""]}>
        {usuarios.map((usuario) => (
          <tr key={usuario.id} className="border-b border-borde last:border-0">
            <td className="px-4 py-3 font-medium">{usuario.nombre}</td>
            <td className="px-4 py-3 text-tinta-suave">{usuario.email}</td>
            <td className="px-4 py-3 text-tinta-suave capitalize">{usuario.sub_rol ?? "—"}</td>
            <td className="px-4 py-3 text-tinta-suave">{fecha(usuario.creado_en)}</td>
            <td className="px-4 py-3">
              <span
                className={`rounded-full px-2.5 py-1 text-[0.68rem] font-semibold tracking-wider uppercase ${
                  usuario.activo ? "bg-activo-suave text-activo" : "bg-borde text-tinta-suave"
                }`}
              >
                {usuario.activo ? "Activa" : "Desactivada"}
              </span>
            </td>
            <td className="px-4 py-3 text-right">
              <Boton variante="fantasma" onClick={() => void alternar(usuario)}>
                {usuario.activo ? "Desactivar" : "Reactivar"}
              </Boton>
            </td>
          </tr>
        ))}
      </Tabla>

      <p className="text-xs text-tinta-tenue">
        El consultor entra al panel, mira fichas y descarga reportes. Aprobar documentos, registrar
        pagos y crear cuentas queda del lado del administrador.
      </p>
    </div>
  );
}
