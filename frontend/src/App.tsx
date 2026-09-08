import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AdminLayout from "./layouts/AdminLayout";
import PortalLayout from "./layouts/PortalLayout";
import { AuthProvider, Protegida } from "./lib/auth";

import Login from "./pages/afiliado/Login";
import Dashboard from "./pages/afiliado/Dashboard";
import Documentos from "./pages/afiliado/Documentos";
import Pagos from "./pages/afiliado/Pagos";
import Perfil from "./pages/afiliado/Perfil";

import LoginAdmin from "./pages/admin/Login";
import DashboardAdmin from "./pages/admin/Dashboard";
import Afiliados from "./pages/admin/Afiliados";
import AfiliadoDetalle from "./pages/admin/AfiliadoDetalle";
import DocumentosAdmin from "./pages/admin/Documentos";
import PagosAdmin from "./pages/admin/Pagos";
import Reportes from "./pages/admin/Reportes";
import Usuarios from "./pages/admin/Usuarios";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/portal" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin/login" element={<LoginAdmin />} />

          {/* Portal del afiliado */}
          <Route
            path="/portal"
            element={
              <Protegida rol="afiliado">
                <PortalLayout />
              </Protegida>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="documentos" element={<Documentos />} />
            <Route path="pagos" element={<Pagos />} />
            <Route path="perfil" element={<Perfil />} />
          </Route>

          {/* Panel administrativo */}
          <Route
            path="/admin"
            element={
              <Protegida rol="admin">
                <AdminLayout />
              </Protegida>
            }
          >
            <Route index element={<DashboardAdmin />} />
            <Route path="afiliados" element={<Afiliados />} />
            <Route path="afiliados/:id" element={<AfiliadoDetalle />} />
            <Route path="documentos" element={<DocumentosAdmin />} />
            <Route path="pagos" element={<PagosAdmin />} />
            <Route path="reportes" element={<Reportes />} />
            <Route path="usuarios" element={<Usuarios />} />
          </Route>

          <Route path="*" element={<Navigate to="/portal" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
