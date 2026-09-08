import { Navigate, Route, Routes } from 'react-router-dom'

import { TableView } from '@/pages/TableView'

/**
 * Componente raíz de la vista del cliente.
 *
 * Ruta única: ``/bar/:slug/t/:hash``, que es la URL codificada en el QR de cada
 * mesa. Cualquier otra ruta redirige a una página de error sencilla.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/bar/:slug/t/:hash" element={<TableView />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
