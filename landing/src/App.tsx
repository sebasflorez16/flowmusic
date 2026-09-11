import { useState } from 'react'

import { RegisterForm } from './RegisterForm'

export default function App() {
  const [plan, setPlan] = useState<'pro' | 'premium' | null>(null)

  return (
    <>
      <div className="wrap">
        <nav>
          <div className="brand">
            <span className="dot">🎵</span> MusicFlow
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <a className="btn ghost" href="#planes">
              Ver planes
            </a>
            <a
              className="btn ghost"
              href={import.meta.env.VITE_DASHBOARD_URL ?? 'https://app.getflowmusic.com'}
            >
              Iniciar sesión
            </a>
          </div>
        </nav>

        <header className="hero">
          <h1>
            Convierte la música de tu bar en una máquina que{' '}
            <span className="grad">vende más bebidas</span>
          </h1>
          <p>
            Tus clientes piden canciones desde la mesa con un QR. Mientras esperan,
            el contador los invita a pedir otra ronda. Tú controlas todo.
          </p>
          <a className="btn" href="#planes">
            Empezar ahora →
          </a>
        </header>
      </div>

      <section className="wrap">
        <h2>El problema</h2>
        <p className="sub">
          La música repetitiva aburre. La gente se va sin pedir más. No sabes qué
          promocionar. MusicFlow lo resuelve.
        </p>
        <div className="grid">
          <div className="glass card">
            <div className="icon">🔁</div>
            <h3>Playlists repetitivas</h3>
            <p>Tus clientes piden lo que quieren escuchar, desde su mesa.</p>
          </div>
          <div className="glass card">
            <div className="icon">⏳</div>
            <h3>Se van sin consumir</h3>
            <p>El contador de "estrés positivo" invita a pedir otra bebida mientras esperan.</p>
          </div>
          <div className="glass card">
            <div className="icon">📢</div>
            <h3>Promociones invisibles</h3>
            <p>Mensajes y cupones en la pantalla y en el celular del cliente.</p>
          </div>
        </div>
      </section>

      <section className="wrap">
        <h2>Cómo funciona</h2>
        <p className="sub">Tres pasos. Cero complicaciones.</p>
        <div className="steps">
          <div className="glass step">
            <div className="num">1</div>
            <h3>Pega el QR en la mesa</h3>
            <p>Cada mesa tiene su QR con la marca de tu bar.</p>
          </div>
          <div className="glass step">
            <div className="num">2</div>
            <h3>El cliente pide su canción</h3>
            <p>Busca en todo YouTube y la pide desde su celular.</p>
          </div>
          <div className="glass step">
            <div className="num">3</div>
            <h3>Suena en tu TV</h3>
            <p>La apruebas y entra a la cola. Se reproduce sola, una tras otra.</p>
          </div>
        </div>
      </section>

      <section className="wrap">
        <h2>Todo lo que incluye</h2>
        <p className="sub">Pensado para bares, restaurantes y discotecas.</p>
        <div className="grid">
          <div className="glass card">
            <div className="icon">🎧</div>
            <h3>AutoDJ por género</h3>
            <p>Cuando la cola se vacía, suena música del estilo de tu bar (vallenato, reggaetón, salsa…).</p>
          </div>
          <div className="glass card">
            <div className="icon">📱</div>
            <h3>QR con tu marca</h3>
            <p>Genera QRs personalizados con tu logo para imprimir y pegar en las mesas.</p>
          </div>
          <div className="glass card">
            <div className="icon">📊</div>
            <h3>Estadísticas reales</h3>
            <p>Peticiones, canciones más pedidas y ventas estimadas.</p>
          </div>
          <div className="glass card">
            <div className="icon">🎟️</div>
            <h3>Cupones y mensajes</h3>
            <p>Promociones que rotan en la TV y en el celular del cliente.</p>
          </div>
        </div>
      </section>

      <section className="wrap" id="planes">
        <h2>Planes simples</h2>
        <p className="sub">Sin permanencia. Cancela cuando quieras.</p>
        <div className="pricing">
          <div className="glass price">
            <h3>Pro</h3>
            <div className="amount">$60.000</div>
            <p style={{ color: 'var(--muted)' }}>COP / mes</p>
            <ul>
              <li>✓ Hasta 8 mesas</li>
              <li>✓ Cola y peticiones</li>
              <li>✓ AutoDJ por género</li>
              <li>✓ QR con marca</li>
              <li>✓ Mensajes y cupones</li>
            </ul>
            <a className="btn" href="#registro" onClick={() => setPlan('pro')} style={{ width: '100%' }}>
              Empezar con Pro
            </a>
          </div>
          <div className="glass price featured">
            <h3>Premium</h3>
            <div className="amount">$120.000</div>
            <p style={{ color: 'var(--muted)' }}>COP / mes</p>
            <ul>
              <li>✓ Todo lo de Pro</li>
              <li>✓ Mesas ilimitadas</li>
              <li>✓ Estadísticas avanzadas</li>
              <li>✓ Soporte prioritario</li>
            </ul>
            <a className="btn" href="#registro" onClick={() => setPlan('premium')} style={{ width: '100%' }}>
              Empezar con Premium
            </a>
          </div>
        </div>
      </section>

      <section className="wrap" id="registro">
        <h2>Crea tu cuenta</h2>
        <p className="sub">Registra tu bar y empieza a configurarlo hoy mismo.</p>
        <div style={{ maxWidth: 560, margin: '0 auto' }}>
          <RegisterForm
            key={plan ?? 'pro'}
            initialPlan={plan ?? 'pro'}
            onClose={() => setPlan(null)}
          />
        </div>
      </section>

      <section className="wrap cta">
        <h2>¿Listo para vender más bebidas?</h2>
        <a className="btn" href="#planes" style={{ fontSize: 17, padding: '16px 30px' }}>
          Crear mi bar gratis →
        </a>
      </section>

      <footer>
        <div className="wrap">MusicFlow © {new Date().getFullYear()} · Hecho para bares y restaurantes</div>
      </footer>
    </>
  )
}
