import { useEffect, type ReactNode } from 'react'

const DASHBOARD_URL = import.meta.env.VITE_DASHBOARD_URL ?? 'https://app.getflowmusic.com'
const WHATSAPP = '573202074066'
const EMAIL = 'hola@getflowmusic.com'
const PHONE = '+57 320 207 4066'

const WA_LINK = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(
  'Hola, quiero MusicFlow en mi bar',
)}`

/** Revela los elementos al entrar en pantalla (fade-up con blur). */
function useReveal() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll('[data-reveal]'))
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('in')
            io.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -60px 0px' },
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
}

/** Íconos de línea finos (sin emojis). */
const ICON_PATHS: Record<string, ReactNode> = {
  note: (
    <>
      <path d="M9 17V5l10-2v12" />
      <circle cx="6.5" cy="17.5" r="2.5" />
      <circle cx="16.5" cy="15.5" r="2.5" />
    </>
  ),
  qr: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <path d="M14 14h3v3" />
      <path d="M21 14v7h-7" />
    </>
  ),
  screen: (
    <>
      <rect x="2.5" y="5" width="19" height="12.5" rx="2.5" />
      <path d="M8 21h8" />
    </>
  ),
  megaphone: (
    <>
      <path d="M4 10v4a1 1 0 0 0 1 1h2l6 4V5L7 9H5a1 1 0 0 0-1 1z" />
      <path d="M17.5 8.5a4 4 0 0 1 0 7" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20h16" />
      <path d="M7 20v-6" />
      <path d="M12 20V6" />
      <path d="M17 20v-9" />
    </>
  ),
  ticket: (
    <>
      <path d="M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1.5a2.5 2.5 0 0 0 0 5V16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-1.5a2.5 2.5 0 0 0 0-5z" />
      <path d="M13 6.5v11" strokeDasharray="2 2.5" />
    </>
  ),
  chat: <path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H9l-5 4V6z" />,
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="M4 7.5l8 5.5 8-5.5" />
    </>
  ),
  phone: (
    <path d="M6 3.5h3.5l1.8 4.5-2.2 1.6a12.5 12.5 0 0 0 5.3 5.3l1.6-2.2 4.5 1.8V20a1.5 1.5 0 0 1-1.6 1.5A17.5 17.5 0 0 1 4.5 5.1 1.5 1.5 0 0 1 6 3.5z" />
  ),
}

function Icon({ name }: { name: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="24"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.35"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICON_PATHS[name]}
    </svg>
  )
}

const FEATURES = [
  {
    icon: 'note',
    title: 'AutoDJ que nunca se detiene',
    text: 'Cuando no hay peticiones, el AutoDJ pone música del género del bar. Si YouTube falla, sigue sonando desde el catálogo local.',
  },
  {
    icon: 'qr',
    title: 'Peticiones por QR',
    text: 'Cada mesa escanea su QR y pide la canción que quiera. Sin apps, sin fricción, sin filas.',
  },
  {
    icon: 'screen',
    title: 'Pantalla TV con videos',
    text: 'La música suena en video en la pantalla del bar, con la mesa que pidió cada canción.',
  },
  {
    icon: 'megaphone',
    title: 'Marketing en pantalla',
    text: 'Mensajes y promociones rotando entre canciones: la promoción de la casa, siempre visible.',
  },
  {
    icon: 'chart',
    title: 'Estadísticas del bar',
    text: 'Qué se pide, a qué hora y desde qué mesa. Datos reales para vender más.',
  },
  {
    icon: 'ticket',
    title: 'Cupones y mesas',
    text: 'Gestiona tus mesas y lanza cupones para incentivar el consumo.',
  },
]

const PLANS = [
  {
    name: 'Pro',
    price: '60.000',
    mesas: 8,
    featured: false,
    features: ['8 mesas con QR', 'AutoDJ que nunca se detiene', 'Pantalla TV con videos', 'Peticiones ilimitadas'],
  },
  {
    name: 'Plus',
    price: '90.000',
    mesas: 12,
    featured: true,
    features: ['12 mesas con QR', 'Todo lo de Pro', 'Mensajes de marketing rotativos', 'Soporte prioritario'],
  },
  {
    name: 'Premium',
    price: '120.000',
    mesas: 16,
    featured: false,
    features: ['16 mesas con QR', 'Todo lo de Plus', 'Estadísticas avanzadas', 'Acompañamiento dedicado'],
  },
]

export default function App() {
  useReveal()

  return (
    <>
      {/* Nav isla */}
      <div className="nav-shell">
        <nav className="nav">
          <a className="brand" href="#top" aria-label="MusicFlow">
            <img src="/logo-letra.png" alt="MusicFlow" />
          </a>
          <div className="links">
            <a href="#como">Cómo funciona</a>
            <a href="#incluye">Qué incluye</a>
            <a href="#planes">Planes</a>
            <a href="#contacto">Contacto</a>
          </div>
          <a className="cta" href={DASHBOARD_URL}>
            Entrar
          </a>
        </nav>
      </div>

      <main id="top">
        {/* Hero */}
        <section className="hero-section">
          <div className="wrap">
            <div className="hero">
              <div>
                <span className="eyebrow" data-reveal>
                  <span className="dot" /> Música inteligente para bares
                </span>
                <h1 style={{ marginTop: 22 }} data-reveal>
                  La música de tu bar, <span className="grad">que vende más bebidas</span>
                </h1>
                <p className="lead" data-reveal>
                  Tus clientes piden canciones desde el QR de su mesa, tú apruebas en un toque y suenan en la
                  pantalla del bar. La música nunca se detiene y cada canción invita a la siguiente ronda.
                </p>
                <div className="actions" data-reveal>
                  <a className="btn" href={WA_LINK} target="_blank" rel="noreferrer">
                    Hablar con nosotros
                    <span className="ico">↗</span>
                  </a>
                  <a className="btn ghost" href="#como">
                    Ver cómo funciona
                  </a>
                </div>
                <div className="trust" data-reveal>
                  <span>
                    <b>Sin apps</b> para tus clientes
                  </span>
                  <span>
                    <b>Instalación</b> en minutos
                  </span>
                  <span>
                    <b>Soporte</b> humano
                  </span>
                </div>
              </div>

              <div className="shell" data-reveal>
                <div className="core player">
                  <span className="badge">
                    <span className="dot" /> Sonando ahora
                  </span>
                  <div className="track">
                    <div className="cover" />
                    <div>
                      <div className="t">Los Caminos De La Vida</div>
                      <div className="a">Los Diablitos · Mesa 4</div>
                    </div>
                    <div className="bars">
                      <i style={{ animationDelay: '0s' }} />
                      <i style={{ animationDelay: '0.15s' }} />
                      <i style={{ animationDelay: '0.3s' }} />
                      <i style={{ animationDelay: '0.45s' }} />
                      <i style={{ animationDelay: '0.6s' }} />
                    </div>
                  </div>
                  <div className="queue">
                    <div className="qi">
                      <span className="n">2</span>
                      <span className="name">Volver</span>
                      <span className="m">Mesa 7</span>
                    </div>
                    <div className="qi">
                      <span className="n">3</span>
                      <span className="name">La Gota Fría</span>
                      <span className="m">Mesa 1</span>
                    </div>
                    <div className="qi">
                      <span className="n">4</span>
                      <span className="name">AutoDJ · Vallenato</span>
                      <span className="m">fondo</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Problema / valor */}
        <section>
          <div className="wrap">
            <div className="section-head center">
              <span className="eyebrow" data-reveal>
                <span className="dot" /> El problema
              </span>
              <h2 data-reveal>
                Un bar sin música <span className="grad">pierde la noche</span>
              </h2>
              <p className="sub" data-reveal>
                Cuando la música se corta, la gente se va. MusicFlow mantiene el ambiente prendido y convierte
                cada mesa en un DJ.
              </p>
            </div>

            <div className="bento">
              <div className="shell cell wide" data-reveal>
                <div className="core pad">
                  <div className="icon-chip">
                    <Icon name="note" />
                  </div>
                  <h3>El ambiente no se apaga</h3>
                  <p>
                    El AutoDJ elige música del estilo del bar automáticamente. Si nadie pide, sigue sonando; si
                    YouTube falla, continúa desde el catálogo. Cero silencios.
                  </p>
                </div>
              </div>
              <div className="shell cell wide" data-reveal>
                <div className="core pad">
                  <div className="icon-chip">
                    <Icon name="chart" />
                  </div>
                  <h3>Más consumo por mesa</h3>
                  <p>
                    Poder pedir tu canción engancha. La gente se queda, vuelve a pedir y pide otra ronda
                    mientras suena «su» canción.
                  </p>
                </div>
              </div>
              <div className="shell cell wide" data-reveal>
                <div className="core pad">
                  <div className="icon-chip">
                    <Icon name="screen" />
                  </div>
                  <h3>Control total del dueño</h3>
                  <p>
                    Apruebas o rechazas cada petición, ves qué mesa la hizo y saltas o eliminas lo que no
                    quieras. Tú mandas en la música.
                  </p>
                </div>
              </div>
              <div className="shell cell wide" data-reveal>
                <div className="core pad">
                  <div className="icon-chip">
                    <Icon name="megaphone" />
                  </div>
                  <h3>Publicidad que sí se ve</h3>
                  <p>
                    Entre canciones, la pantalla muestra tus promociones y mensajes. Marketing en el punto
                    exacto donde el cliente decide.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Banda con imagen — La gente */}
        <section className="band" style={{ backgroundImage: 'url(/photos/crowd.jpg)' }}>
          <div className="band-inner" data-reveal>
            <h2>
              Cuando piden <span className="grad">su canción</span>, el bar se prende
            </h2>
            <p className="sub">
              La gente participa, se queda más tiempo y celebra. La música deja de ser de fondo y se vuelve la
              fiesta.
            </p>
          </div>
        </section>

        {/* Cómo funciona */}
        <section id="como">
          <div className="wrap">
            <div className="section-head center">
              <span className="eyebrow" data-reveal>
                <span className="dot" /> Cómo funciona
              </span>
              <h2 data-reveal>
                Tres pasos y <span className="grad">el bar suena solo</span>
              </h2>
            </div>

            <div className="steps">
              <div className="shell step" data-reveal>
                <div className="core pad">
                  <div className="num">PASO 01</div>
                  <h3 style={{ margin: '12px 0 8px' }}>El cliente escanea su QR</h3>
                  <p className="muted-sm">
                    Cada mesa tiene su QR impreso. El cliente lo escanea y entra al buscador de música del bar,
                    sin descargar nada.
                  </p>
                </div>
              </div>
              <div className="shell step" data-reveal>
                <div className="core pad">
                  <div className="num">PASO 02</div>
                  <h3 style={{ margin: '12px 0 8px' }}>Pide su canción</h3>
                  <p className="muted-sm">
                    Busca y pide la canción que quiera. Tú la ves al instante en el panel, con la mesa que la
                    pidió.
                  </p>
                </div>
              </div>
              <div className="shell step" data-reveal>
                <div className="core pad">
                  <div className="num">PASO 03</div>
                  <h3 style={{ margin: '12px 0 8px' }}>Suena en la pantalla</h3>
                  <p className="muted-sm">
                    Con un toque apruebas y la canción suena en video en la TV del bar. La mesa lo ve y lo
                    celebra.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Banda con imagen — La música */}
        <section className="band" style={{ backgroundImage: 'url(/photos/mixer.jpg)' }}>
          <div className="band-inner" data-reveal>
            <h2>
              La música <span className="grad">nunca se detiene</span>
            </h2>
            <p className="sub">
              El AutoDJ mantiene el ambiente del género de tu bar, sin silencios y sin que nadie tenga que
              estar pendiente.
            </p>
          </div>
        </section>

        {/* Qué incluye */}
        <section id="incluye">
          <div className="wrap">
            <div className="section-head center">
              <span className="eyebrow" data-reveal>
                <span className="dot" /> Qué incluye
              </span>
              <h2 data-reveal>
                Todo lo que un bar necesita, <span className="grad">en un solo lugar</span>
              </h2>
            </div>

            <div className="bento">
              {FEATURES.map((f) => (
                <div className="shell cell" key={f.title} data-reveal>
                  <div className="core pad">
                    <div className="icon-chip">
                      <Icon name={f.icon} />
                    </div>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Planes */}
        <section id="planes">
          <div className="wrap">
            <div className="section-head center">
              <span className="eyebrow" data-reveal>
                <span className="dot" /> Planes
              </span>
              <h2 data-reveal>
                Un plan para <span className="grad">cada tamaño de bar</span>
              </h2>
              <p className="sub" data-reveal>
                Elige por mesas. Todos incluyen peticiones por QR, AutoDJ y pantalla TV. Sin contratos largos.
              </p>
            </div>

            <div className="plans">
              {PLANS.map((p) => (
                <div className={`shell plan ${p.featured ? 'featured' : ''}`} key={p.name} data-reveal>
                  {p.featured && <span className="flag">Más elegido</span>}
                  <div className="core">
                    <div className="name">{p.name}</div>
                    <div className="amount">
                      ${p.price}
                      <span> /mes</span>
                    </div>
                    <div className="mesas">Hasta {p.mesas} mesas</div>
                    <ul>
                      {p.features.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                    <a className="btn" href={WA_LINK} target="_blank" rel="noreferrer">
                      Contratar {p.name}
                      <span className="ico">↗</span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Contacto */}
        <section id="contacto">
          <div className="wrap">
            <div className="section-head center">
              <span className="eyebrow" data-reveal>
                <span className="dot" /> Contacto
              </span>
              <h2 data-reveal>
                ¿Listo para <span className="grad">escuchar la diferencia?</span>
              </h2>
              <p className="sub" data-reveal>
                Escríbenos y te mostramos MusicFlow funcionando. Te acompañamos en la instalación y en la
                puesta en marcha de tu bar.
              </p>
            </div>

            <div className="contact">
              <a className="shell cell" href={WA_LINK} target="_blank" rel="noreferrer" data-reveal>
                <div className="core pad center">
                  <div className="icon-chip center-chip">
                    <Icon name="chat" />
                  </div>
                  <h3>WhatsApp</h3>
                  <p>{PHONE}</p>
                  <p className="link">Escríbenos</p>
                </div>
              </a>
              <a className="shell cell" href={`mailto:${EMAIL}`} data-reveal>
                <div className="core pad center">
                  <div className="icon-chip center-chip">
                    <Icon name="mail" />
                  </div>
                  <h3>Email</h3>
                  <p>{EMAIL}</p>
                  <p className="link">Enviar correo</p>
                </div>
              </a>
              <a className="shell cell" href={`tel:${PHONE.replace(/\s/g, '')}`} data-reveal>
                <div className="core pad center">
                  <div className="icon-chip center-chip">
                    <Icon name="phone" />
                  </div>
                  <h3>Teléfono</h3>
                  <p>{PHONE}</p>
                  <p className="link">Llamar</p>
                </div>
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <div className="wrap footer-grid">
          <img src="/logo-letra.png" alt="MusicFlow" />
          <span>MusicFlow © {new Date().getFullYear()} · Música inteligente para bares</span>
          <a href={DASHBOARD_URL}>Acceso dueños</a>
        </div>
      </footer>
    </>
  )
}
