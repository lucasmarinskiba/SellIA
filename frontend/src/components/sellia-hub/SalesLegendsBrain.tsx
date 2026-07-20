'use client'

/**
 * SALES LEGENDS BRAIN
 *
 * Dedicado a los más grandes vendedores de la historia. Cada uno = playbook
 * tactico que la IA invoca según situación. Trading-card style.
 *
 * Diferencia con MasterMindCouncil: éste es 100% EJECUCIÓN DE VENTA.
 * Scripts, frameworks, tonality, opening lines, closing lines.
 */

import { useState, useMemo } from 'react'
import {
  Trophy, Quote, Activity, Sparkles, Filter, Star, Zap,
  TrendingUp, Award, Crown, Target, Flame, ChevronRight, Bot, Play
} from 'lucide-react'

type LegendSpecialty = 'deals' | 'persuasion' | 'demo' | 'copy' | 'insurance' | 'retail' | 'auto' | 'door' | 'influence' | 'state'

interface Legend {
  id: string
  name: string
  emoji: string
  era: string
  hallmark: string
  specialty: LegendSpecialty
  signatureTechnique: string
  worldRecord: string
  sampleScript: string
  quote: string
  activeIn: string
  invocationsToday: number
  color: string
  industry: string
}

const LEGENDS: Legend[] = [
  {
    id: 'jg', name: 'Joe Girard', emoji: '🏎', era: '1963-1978',
    hallmark: 'Guinness · Vendedor más grande del mundo',
    specialty: 'auto', industry: 'Automotriz',
    signatureTechnique: 'Law of 250 · cada cliente conoce 250 personas',
    worldRecord: '13,001 autos vendidos · récord aún imbatido',
    sampleScript: '"Te mando 12 tarjetas al año diciendo solo \'I like you\'. Sin pedir nada. Cuando necesites algo, vas a recordarme."',
    quote: '"La gente le compra a la gente que le cae bien."',
    activeIn: 'Follow-up post-cierre · referrals · birthday touch',
    invocationsToday: 47, color: '#ef4444',
  },
  {
    id: 'bf', name: 'Ben Feldman', emoji: '💼', era: '1942-1993',
    hallmark: 'NYL Legend · $1.8B en seguros de vida',
    specialty: 'insurance', industry: 'Seguros',
    signatureTechnique: 'Storytelling · proyecta el futuro del cliente',
    worldRecord: '$100M en pólizas en un solo año (1960s)',
    sampleScript: '"Permitame mostrarle algo: si murieras esta noche, ¿cómo se levanta tu familia mañana?" *muestra cheque en blanco*',
    quote: '"No vendo seguros, vendo problemas resueltos."',
    activeIn: 'Productos high-ticket · objeción de precio',
    invocationsToday: 23, color: '#3b82f6',
  },
  {
    id: 'jb', name: 'Jordan Belfort', emoji: '🐺', era: '1990s · presente',
    hallmark: 'Wolf of Wall Street · Straight Line System',
    specialty: 'persuasion', industry: 'Finanzas · Coaching',
    signatureTechnique: 'Straight Line · certainty 3 puntos: producto/yo/empresa',
    worldRecord: 'Stratton Oakmont · $1B+ levantado en años 90',
    sampleScript: '"Imaginate esto: ¿te imaginás dentro de 3 meses con esto resuelto?" *pausa* "Es exactamente lo que mi cliente Juan dijo antes de..."',
    quote: '"Vender es transferencia de certeza."',
    activeIn: 'Manejo de objeciones · tonality · cierre',
    invocationsToday: 89, color: '#f97316',
  },
  {
    id: 'zz', name: 'Zig Ziglar', emoji: '🤝', era: '1968-2012',
    hallmark: 'Vendedor a motivational speaker · 30+ libros',
    specialty: 'influence', industry: 'Cookware · Coaching',
    signatureTechnique: 'Asumptive close · "¿cuándo?", no "¿si?"',
    worldRecord: 'Top vendedor cookware nacional USA',
    sampleScript: '"¿Preferís empezar el martes o el jueves?" *no le da opción de no empezar*',
    quote: '"Vas a tener todo lo que quieras si ayudás a otros."',
    activeIn: 'Cierre asumtivo · relación largo plazo',
    invocationsToday: 56, color: '#22c55e',
  },
  {
    id: 'dc', name: 'Dale Carnegie', emoji: '👥', era: '1936-presente',
    hallmark: 'How to Win Friends and Influence People · 30M+ copias',
    specialty: 'influence', industry: 'Comunicación universal',
    signatureTechnique: '6 ways to make people like you · nombre + escucha',
    worldRecord: 'Libro más vendido de business · 80+ años',
    sampleScript: '"Mariana, ¡exactamente! Eso que dijiste sobre el costo... me hace pensar..." *usa nombre + valida + redirige*',
    quote: '"El nombre de una persona es para ella el sonido más dulce."',
    activeIn: 'Rapport building · empatía táctica',
    invocationsToday: 124, color: '#a855f7',
  },
  {
    id: 'tr', name: 'Tony Robbins', emoji: '🔥', era: '1980-presente',
    hallmark: 'Performance coach · NLP + state management',
    specialty: 'state', industry: 'Coaching · Eventos',
    signatureTechnique: 'State anchoring · postura + tonality + breathing',
    worldRecord: '50M+ personas impactadas · UPW worldwide',
    sampleScript: '"PARA. Respirá. Cambiá tu fisiología y cambiás tu estado. ¿Cómo va a estar tu vida en 5 años SI NO compras esto?"',
    quote: '"El precio de tu vida es el precio que pones a tu tiempo."',
    activeIn: 'Reframe emocional · cierre transformacional',
    invocationsToday: 67, color: '#fbbf24',
  },
  {
    id: 'dt', name: 'Donald Trump', emoji: '🏢', era: '1980s-presente',
    hallmark: 'Art of the Deal · anchoring extremo',
    specialty: 'deals', industry: 'Real estate · Branding',
    signatureTechnique: 'Anchor alto · negocia para abajo · "I have leverage"',
    worldRecord: 'Brand Trump valuado en $3B+',
    sampleScript: '"Este producto vale $5,000. Tranquilamente. Pero solo para vos, hoy: $1,997. Mañana no te puedo garantizar el mismo precio."',
    quote: '"El peor error en negocios es decir sí cuando hay que decir no."',
    activeIn: 'Anchoring · negociación high-stakes',
    invocationsToday: 34, color: '#fbbf24',
  },
  {
    id: 'mk', name: 'Mary Kay Ash', emoji: '💄', era: '1963-2001',
    hallmark: 'Mary Kay Cosmetics · empoderamiento femenino',
    specialty: 'retail', industry: 'Cosmética · Direct sales',
    signatureTechnique: 'Reconocimiento público · trofeos · pink Cadillac',
    worldRecord: 'Empresa de $4B+ · 3.5M consultoras',
    sampleScript: '"Mariana, vos sos increíble. Mirá lo que lograste este mes. *te muestra premio*. Imaginá cuando llegues al próximo nivel..."',
    quote: '"Imaginá que todas tus clientas tienen un letrero en la frente que dice: hacéme sentir importante."',
    activeIn: 'Fidelización · gamification · advocates',
    invocationsToday: 28, color: '#ec4899',
  },
  {
    id: 'do', name: 'David Ogilvy', emoji: '✍️', era: '1948-1999',
    hallmark: 'Father of Advertising · Ogilvy & Mather',
    specialty: 'copy', industry: 'Publicidad · Direct response',
    signatureTechnique: 'Long-form copy · facts > fluff · big idea',
    worldRecord: 'Campañas Rolls-Royce, Hathaway, Schweppes',
    sampleScript: '"A 60 millas por hora, el sonido más fuerte en este Rolls-Royce viene del reloj eléctrico." *un hecho, no claim*',
    quote: '"Si no vende, no es creativo."',
    activeIn: 'Copywriting · headlines · ads que convierten',
    invocationsToday: 78, color: '#06b6d4',
  },
  {
    id: 'rp', name: 'Ron Popeil', emoji: '🍗', era: '1956-2021',
    hallmark: 'Infomercials · "But wait, there\'s more!"',
    specialty: 'demo', industry: 'Productos consumidor',
    signatureTechnique: 'Demo en vivo · stacking valor · "set it and forget it"',
    worldRecord: '$2B+ en productos vendidos via TV',
    sampleScript: '"Mirá esto. *demo en vivo*. Pero esperá... ¡hay más! Si llamás ahora, recibís TAMBIÉN..." *stacking infinito*',
    quote: '"Set it and forget it."',
    activeIn: 'Video demos · stacking bonus · urgency',
    invocationsToday: 45, color: '#f59e0b',
  },
  {
    id: 'jp', name: 'John H. Patterson', emoji: '📜', era: '1884-1922',
    hallmark: 'NCR · padre del entrenamiento de ventas moderno',
    specialty: 'door', industry: 'Cash registers · B2B',
    signatureTechnique: 'Sales pyramid · script estandarizado · territorios',
    worldRecord: 'Inventó el manual de ventas, pitch book, quotas',
    sampleScript: '"Sr. comerciante, ¿sabe cuánto pierde por día sin un registro? *muestra cifra*. ¿Cuándo prefiere instalación, mañana o jueves?"',
    quote: '"Capacitá. Capacitá. Y después capacitá más."',
    activeIn: 'Procesos B2B · entrenamiento de scripts',
    invocationsToday: 19, color: '#84cc16',
  },
  {
    id: 'ma', name: 'Markita Andrews', emoji: '🍪', era: '1980s',
    hallmark: 'Girl Scout · $80,000 en cookies a los 13',
    specialty: 'door', industry: 'D2C · Door-to-door',
    signatureTechnique: 'Ask big · "¿comprarías 30 cajas?" → contraoferta 5',
    worldRecord: 'Récord mundial Girl Scout · libro propio',
    sampleScript: '"Hola, vendo cookies para enviarme a un viaje. ¿Comprarías 50 cajas?" *si dice no* "OK, ¿qué tal 10?"',
    quote: '"Si no pedís, no te dan."',
    activeIn: 'Door-to-door · cold outreach · anchor pricing',
    invocationsToday: 14, color: '#fbbf24',
  },
  {
    id: 'ef', name: 'Erica Feidner', emoji: '🎹', era: '1990s-2010s',
    hallmark: 'Steinway · $40M en pianos vendidos',
    specialty: 'demo', industry: 'Lujo · Pianos',
    signatureTechnique: 'Piano-matching · empatía profunda · cliente toca',
    worldRecord: '#1 vendedora Steinway 7 años seguidos',
    sampleScript: '"Sentate. Tocá. *silencio*. Este piano fue hecho para vos. ¿No lo sentís?" *vende experiencia, no producto*',
    quote: '"Vendo el sueño, no el instrumento."',
    activeIn: 'High-ticket emocional · productos premium',
    invocationsToday: 11, color: '#a855f7',
  },
  {
    id: 'jt', name: 'Jeffrey Gitomer', emoji: '📕', era: '1995-presente',
    hallmark: 'Little Red Book of Selling · Sales Bible',
    specialty: 'persuasion', industry: 'B2B · Sales training',
    signatureTechnique: 'Likeability + trust > techniques · WHY they buy',
    worldRecord: '15+ libros bestsellers de ventas',
    sampleScript: '"No me cuentes lo que vendés. Contame por qué TU cliente te compra a vos y no al competidor."',
    quote: '"La gente no le compra a empresas. Le compra a personas."',
    activeIn: 'B2B · trust building · diferenciación',
    invocationsToday: 32, color: '#dc2626',
  },
  {
    id: 'bt', name: 'Brian Tracy', emoji: '🎯', era: '1980-presente',
    hallmark: 'Psychology of Selling · 80M+ libros',
    specialty: 'influence', industry: 'Coaching · Sales psych',
    signatureTechnique: 'ABC · Always Be Closing · 7-step process',
    worldRecord: '5,000+ empresas entrenadas worldwide',
    sampleScript: '"Cada conversación es una pequeña venta. Pediles que digan sí 3 veces antes de la gran pregunta."',
    quote: '"Las ventas no son sobre cerrar. Son sobre abrir relaciones."',
    activeIn: 'Procesos · multi-step closes',
    invocationsToday: 41, color: '#0ea5e9',
  },
  {
    id: 'fb', name: 'Frank Bettger', emoji: '⚾', era: '1900-1981',
    hallmark: 'How I Raised Myself from Failure to Success',
    specialty: 'insurance', industry: 'Seguros · Béisbol',
    signatureTechnique: 'Entusiasmo + preguntas · 90% del trabajo = preparación',
    worldRecord: 'Top vendedor seguros USA años 30-40',
    sampleScript: '"Antes de hablar de mi producto, ¿me permitís 4 preguntas?" *deja que cliente venda solo*',
    quote: '"Actuá entusiasta y serás entusiasta."',
    activeIn: 'Discovery · pre-call prep · enthusiasm',
    invocationsToday: 17, color: '#10b981',
  },
  {
    id: 'ew', name: 'Elmer Wheeler', emoji: '🥩', era: '1903-1968',
    hallmark: 'Sell the Sizzle Not the Steak · Tested Selling Sentences',
    specialty: 'copy', industry: 'Wheeler Word Lab · retail',
    signatureTechnique: 'Tested phrases · 105,000 frases probadas a campo',
    worldRecord: 'Pionero del A/B testing en lenguaje de ventas',
    sampleScript: '"¿Querés ahorrar o querés un huevo?" *en lugar de "¿agregás huevo?"* — incrementó ventas malteadas 25%',
    quote: '"No vendas el bife, vendé el chisporroteo."',
    activeIn: 'A/B testing copy · headlines · words that sell',
    invocationsToday: 38, color: '#dc2626',
  },
  {
    id: 'wcs', name: 'W. Clement Stone', emoji: '✨', era: '1902-2002',
    hallmark: 'Combined Insurance · PMA (Positive Mental Attitude)',
    specialty: 'insurance', industry: 'Seguros · self-help',
    signatureTechnique: 'PMA + R2A2 · Recognize/Relate/Assimilate/Apply',
    worldRecord: '$100 iniciales → $400M imperio · 1,000+ libros enviados',
    sampleScript: '"¡HAZLO AHORA! No mañana. Mientras dudás, otro vendedor llamó a tu prospecto."',
    quote: '"Lo que la mente concibe y cree, puede lograr."',
    activeIn: 'Sales motivation · self-talk loops · acción inmediata',
    invocationsToday: 22, color: '#fbbf24',
  },
  {
    id: 'th', name: 'Tom Hopkins', emoji: '🎓', era: '1976-presente',
    hallmark: 'How to Master the Art of Selling · 4M+ entrenados',
    specialty: 'influence', industry: 'Real estate · training',
    signatureTechnique: '"Tie-down" question · siempre buscar mini-yes',
    worldRecord: '#1 real estate USA año 5 · $14M ventas vendiendo casas',
    sampleScript: '"Esta característica te ahorra tiempo, ¿no es así?" *tie-down compuesto*',
    quote: '"Soy un campeón. Los campeones no nacen, se forjan."',
    activeIn: 'Tie-downs · trial closes · scripted excellence',
    invocationsToday: 44, color: '#3b82f6',
  },
  {
    id: 'om', name: 'Og Mandino', emoji: '📜', era: '1923-1996',
    hallmark: 'The Greatest Salesman in the World · 50M+ libros',
    specialty: 'influence', industry: 'Combined Insurance · filosofía',
    signatureTechnique: '10 Scrolls · ritual diario · hábitos del éxito',
    worldRecord: 'Bestseller traducido a 25 idiomas',
    sampleScript: '"Mis fracasos, decepciones y desesperanzas son las semillas de mi éxito." *afirmación pre-call*',
    quote: '"Persistiré hasta tener éxito."',
    activeIn: 'Mindset · resilencia · daily rituals',
    invocationsToday: 19, color: '#a855f7',
  },
  {
    id: 'jbl', name: 'Jeb Blount', emoji: '📞', era: '2010-presente',
    hallmark: 'Fanatical Prospecting · Sales Gravy CEO',
    specialty: 'door', industry: 'B2B SaaS · modern outbound',
    signatureTechnique: '5C: cualifica · contacta · captura · contrata · cierra · multi-channel',
    worldRecord: 'Best-selling sales author 2010s · 30%+ regla de los CEOs',
    sampleScript: '"Tengo 27 segundos antes de que decidas si seguir hablando. ¿Me los das?"',
    quote: '"La razón #1 de fracaso en ventas: tubería vacía."',
    activeIn: 'Modern cold call · multi-channel cadence',
    invocationsToday: 71, color: '#0ea5e9',
  },
  {
    id: 'nr', name: 'Neil Rackham', emoji: '🔬', era: '1988-presente',
    hallmark: 'SPIN Selling · 35,000 llamadas analizadas en Xerox/IBM',
    specialty: 'persuasion', industry: 'B2B research · enterprise',
    signatureTechnique: 'SPIN: Situation · Problem · Implication · Need-payoff',
    worldRecord: 'Estudio más grande de ventas B2B jamás hecho',
    sampleScript: '"Ese problema que mencionás, ¿qué impacto tiene en tu equipo cuando se repite?" *Implication question*',
    quote: '"Cuanto más grave la implicación, más urgente el problema."',
    activeIn: 'B2B discovery · enterprise selling',
    invocationsToday: 88, color: '#06b6d4',
  },
  {
    id: 'mc', name: 'Mark Cuban', emoji: '🦈', era: '1995-presente',
    hallmark: 'Broadcast.com $5.7B a Yahoo · Shark Tank',
    specialty: 'deals', industry: 'Tech · sports · entrepreneurship',
    signatureTechnique: 'Out-work · responder en minutos · curiosidad sin filtro',
    worldRecord: 'De camarero a billionaire · 17 años · 1 venta',
    sampleScript: '"¿Cuál es tu margen? ¿Cuánto vendiste el año pasado? Estoy adentro / Estoy afuera." *decisión en 60 seg*',
    quote: '"Trabajá como si alguien estuviera 24/7 intentando arrebatarte todo."',
    activeIn: 'Decisión rápida · pitch en 60 seg · deal closing',
    invocationsToday: 35, color: '#dc2626',
  },
  {
    id: 'dj', name: 'Daymond John', emoji: '👕', era: '1992-presente',
    hallmark: 'FUBU $6B+ · Power of Broke · Shark Tank',
    specialty: 'deals', industry: 'Fashion · branding · Shark Tank',
    signatureTechnique: 'SHARK: Set goals · Homework · Adore · Remember · Keep swimming',
    worldRecord: 'De $40 → $6B fashion empire desde mamá',
    sampleScript: '"Si rompo tu producto en TV ahora, ¿qué hacés? Esa es tu venta real, no acá conmigo."',
    quote: '"El poder de estar quebrado te obliga a ser creativo."',
    activeIn: 'Branding personal · scrappy growth · pitch perfecto',
    invocationsToday: 26, color: '#fbbf24',
  },
  {
    id: 'kh', name: 'Kevin Harrington', emoji: '📺', era: '1984-presente',
    hallmark: 'As Seen On TV pionero · primer Shark de Shark Tank',
    specialty: 'demo', industry: 'Direct response TV · infomercials',
    signatureTechnique: 'Pitch 3-act · problema/solución/oferta · time-pressure',
    worldRecord: '$5B+ en productos vendidos · 500+ productos',
    sampleScript: '"¿Tenés este problema? *muestra dolor* ¡Conocé X! *demo dramatizado* Llamá AHORA y recibís 2 por 1 + envío gratis."',
    quote: '"Si tu producto no se entiende en 30 segundos, no se vende."',
    activeIn: 'Video pitches · stacking · urgency · TV-style',
    invocationsToday: 33, color: '#f59e0b',
  },
  {
    id: 'lg', name: 'Lori Greiner', emoji: '💎', era: '1996-presente',
    hallmark: 'Queen of QVC · 700+ productos inventados · Shark Tank',
    specialty: 'demo', industry: 'Retail · QVC · invención',
    signatureTechnique: '"Hero or zero" en 30 seg · live shopping mastery',
    worldRecord: '120+ patentes propias · ratio bate 90%+ en QVC',
    sampleScript: '"Te muestro cómo en 30 segundos esto va a resolver TU problema diario." *demo live + storytelling*',
    quote: '"Una gran idea no resuelve un problema. Una venta sí."',
    activeIn: 'Live shopping · TikTok Shop live · QVC-style',
    invocationsToday: 41, color: '#ec4899',
  },
  {
    id: 'en', name: 'Earl Nightingale', emoji: '🎙', era: '1956-1989',
    hallmark: 'The Strangest Secret · padre del personal development audio',
    specialty: 'state', industry: 'Combined Insurance · radio · self-dev',
    signatureTechnique: '"We become what we think about" · daily mind diet',
    worldRecord: 'Primer disco de oro de spoken word · 1 millón copias',
    sampleScript: '"Pensá en tu mejor cliente. Sentí cómo te sentiste cerrando con él. Ahora abrí esta nueva llamada con ESA energía."',
    quote: '"Nos convertimos en lo que pensamos."',
    activeIn: 'State management · pre-call mind primer',
    invocationsToday: 16, color: '#a855f7',
  },
  {
    id: 'mm', name: 'Maxwell Maltz', emoji: '🧠', era: '1960-1975',
    hallmark: 'Psycho-Cybernetics · 30M+ libros · self-image science',
    specialty: 'state', industry: 'Cirugía plástica · psicología',
    signatureTechnique: 'Self-image driving behavior · 21-day habit reset',
    worldRecord: 'Influencia directa en Belfort, Tony Robbins, Maltz Method',
    sampleScript: '"Antes de la llamada: visualizá 60 segundos cómo cerrás. Tu sistema nervioso no distingue entre real e imaginado."',
    quote: '"No podés actuar consistentemente diferente de cómo te ves a vos mismo."',
    activeIn: 'Pre-call visualization · confidence building',
    invocationsToday: 21, color: '#8b5cf6',
  },
  {
    id: 'rk', name: 'Robert Kiyosaki', emoji: '🏦', era: '1997-presente',
    hallmark: 'Rich Dad Poor Dad · 41M+ libros · 51 idiomas',
    specialty: 'influence', industry: 'Educación financiera · sales',
    signatureTechnique: 'Re-framing mental · activos vs pasivos · cash-flow language',
    worldRecord: '#1 personal finance book de todos los tiempos',
    sampleScript: '"¿Esto es un gasto o una inversión que te paga de vuelta? Pensá como dueño, no como empleado."',
    quote: '"Los ricos no trabajan por dinero. Los ricos hacen que el dinero trabaje para ellos."',
    activeIn: 'Reframe de precio · ROI thinking · ownership language',
    invocationsToday: 39, color: '#22c55e',
  },
  {
    id: 'bb', name: 'Bob Burg', emoji: '🎁', era: '1993-presente',
    hallmark: 'Endless Referrals · The Go-Giver · 5 leyes',
    specialty: 'influence', industry: 'B2B · referral marketing',
    signatureTechnique: 'Ley del valor · dar primero · pedir referidos sistemático',
    worldRecord: '"The Go-Giver" · 1M+ copias · traducido 28 idiomas',
    sampleScript: '"¿Conocés alguien más que tenga este desafío? Si me presentás, le doy el mismo bonus que a vos."',
    quote: '"Tu verdadero valor es cuánto valor das a otros."',
    activeIn: 'Programa referidos · networking · giver framework',
    invocationsToday: 47, color: '#10b981',
  },
  {
    id: 'ai', name: 'Anthony Iannarino', emoji: '📕', era: '2010-presente',
    hallmark: 'The Lost Art of Closing · modern B2B framework',
    specialty: 'persuasion', industry: 'B2B Enterprise · SaaS',
    signatureTechnique: '10 Commitments · cada conversación pide un compromiso específico',
    worldRecord: 'TheSalesBlog autor activo · framework adoptado por enterprise',
    sampleScript: '"Antes de cerrar la llamada, ¿podemos comprometernos a que veas la propuesta el viernes y me digas un sí o un no?"',
    quote: '"El cierre no es el final. Es la suma de 10 commitments más chicos."',
    activeIn: 'B2B multi-call · commitment ladder · enterprise',
    invocationsToday: 52, color: '#ef4444',
  },
  {
    id: 'ch', name: 'Chet Holmes', emoji: '⚙️', era: '2007-2012',
    hallmark: 'The Ultimate Sales Machine · 12 estrategias · Dream 100',
    specialty: 'persuasion', industry: 'B2B · Charlie Munger of sales',
    signatureTechnique: 'Dream 100 · enfoque obsesivo en 100 clientes ideales',
    worldRecord: 'Doblegó ventas de 60 empresas Fortune 500',
    sampleScript: '"En lugar de perseguir 1,000 leads, identificá tus 100 ideales y volveloos un proyecto de 3 años."',
    quote: '"Lo que se mide, se gestiona. Lo que se ignora, se pierde."',
    activeIn: 'Dream 100 · ABM · enterprise focus',
    invocationsToday: 29, color: '#0ea5e9',
  },
  {
    id: 'pk', name: 'Phil Knight', emoji: '👟', era: '1964-presente',
    hallmark: 'Nike co-founder · Shoe Dog · vendió zapatos desde el baúl',
    specialty: 'deals', industry: 'Sportswear · branding',
    signatureTechnique: 'Vendé la visión, no el producto · Just Do It',
    worldRecord: '$50M Nike → $200B+ marca global',
    sampleScript: '"No te estoy vendiendo zapatillas. Te estoy vendiendo la versión de vos que sale a correr a las 6am."',
    quote: '"La marca es lo único que no puede ser copiado."',
    activeIn: 'Brand storytelling · vision selling · aspirational',
    invocationsToday: 24, color: '#000000',
  },
  {
    id: 'sw', name: 'Sam Walton', emoji: '🛒', era: '1962-1992',
    hallmark: 'Walmart founder · service obsesivo · "Sundown rule"',
    specialty: 'retail', industry: 'Retail · supply chain',
    signatureTechnique: '10-foot rule · saludar a cliente a 10 pies de distancia',
    worldRecord: 'Walmart de 1 tienda → mayor retail del mundo',
    sampleScript: '"Si un cliente se acerca a 3 metros, sonreíle, mirá a los ojos y saludalo. Es la regla #1."',
    quote: '"Hay un solo jefe: el cliente. Y puede despedir a cualquiera."',
    activeIn: 'Customer service · response time · personal touch',
    invocationsToday: 31, color: '#3b82f6',
  },
  {
    id: 'el', name: 'Estée Lauder', emoji: '💋', era: '1946-2004',
    hallmark: 'Estée Lauder Cosmetics · samples + door-to-door',
    specialty: 'retail', industry: 'Cosmética · luxury',
    signatureTechnique: 'Free sample con cada compra · "regalo con propósito"',
    worldRecord: 'De 4 productos → imperio de $16B · 150 países',
    sampleScript: '"Probá esto en tu cuello, no en la muñeca. Querés que sienta TU piel, no la del bolso." *muestreo táctil*',
    quote: '"Toqué a cada mujer. Eso es lo que vendí."',
    activeIn: 'Sampling · personalized touch · cosmetics-style sales',
    invocationsToday: 23, color: '#ec4899',
  },
  {
    id: 'js', name: 'Joe Sugarman', emoji: '🕶', era: '1971-2022',
    hallmark: 'JS&A · BluBlocker · Triggers · copywriting legend',
    specialty: 'copy', industry: 'Direct response · copywriting',
    signatureTechnique: '30 psychological triggers · curiosity slope · ad as conversation',
    worldRecord: '20M+ BluBlocker sunglasses vendidos vía ad',
    sampleScript: '"Imaginate esto. Es de noche. Estás manejando. De repente, ves todo más claro que de día..." *curiosity hook*',
    quote: '"El propósito del primer párrafo es que leas el segundo."',
    activeIn: 'Long-form ads · psychological triggers · curiosity gap',
    invocationsToday: 36, color: '#06b6d4',
  },
]

const SPECIALTY_CONFIG: Record<LegendSpecialty, { label: string; emoji: string; color: string }> = {
  deals:      { label: 'Deals · Anchoring',  emoji: '🏢', color: '#fbbf24' },
  persuasion: { label: 'Persuasión',         emoji: '🐺', color: '#f97316' },
  demo:       { label: 'Demo en vivo',       emoji: '🍗', color: '#f59e0b' },
  copy:       { label: 'Copywriting',        emoji: '✍️', color: '#06b6d4' },
  insurance:  { label: 'High-ticket',        emoji: '💼', color: '#3b82f6' },
  retail:     { label: 'Retail · Recogn.',   emoji: '💄', color: '#ec4899' },
  auto:       { label: 'Long-term · Refer.', emoji: '🏎', color: '#ef4444' },
  door:       { label: 'Door-to-door',       emoji: '🍪', color: '#84cc16' },
  influence:  { label: 'Influencia',         emoji: '🤝', color: '#22c55e' },
  state:      { label: 'State + NLP',        emoji: '🔥', color: '#fbbf24' },
}

export default function SalesLegendsBrain() {
  const [filter, setFilter] = useState<LegendSpecialty | 'all'>('all')
  const [selectedId, setSelectedId] = useState<string>(LEGENDS[0].id)

  const filtered = useMemo(
    () => filter === 'all' ? LEGENDS : LEGENDS.filter(l => l.specialty === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const invocations = LEGENDS.reduce((s, l) => s + l.invocationsToday, 0)
    const top = [...LEGENDS].sort((a, b) => b.invocationsToday - a.invocationsToday)[0]
    return { total: LEGENDS.length, invocations, top }
  }, [])

  const specialtyCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const l of LEGENDS) c[l.specialty] = (c[l.specialty] || 0) + 1
    return c
  }, [])

  const selected = LEGENDS.find(l => l.id === selectedId)!

  return (
    <section className="relative rounded-2xl border border-red-500/20 bg-gradient-to-br from-[#1a0a0a]/40 via-[#0a0e1a]/85 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-400/80 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-red-500/25 to-amber-500/15 border border-red-500/40 flex items-center justify-center">
            <Trophy className="w-5 h-5 text-red-400" style={{ filter: 'drop-shadow(0 0 8px rgba(239,68,68,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-red-400 via-amber-400 to-red-400 bg-clip-text text-transparent">SALES LEGENDS BRAIN</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  {stats.total} leyendas vendiendo por vos</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                {stats.invocations} activaciones hoy
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Cada cierre se nutre del playbook de uno de los más grandes vendedores de la historia</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/25">
          <Flame className="w-3 h-3 text-red-400" />
          <span className="text-[10px] text-red-300">Top hoy: <span className="font-bold">{stats.top.name}</span> · {stats.top.invocationsToday}×</span>
        </div>
      </div>

      {/* Specialty filter */}
      <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2 overflow-x-auto no-scrollbar">
        <Filter className="w-3 h-3 text-white/30 shrink-0" />
        <button
          onClick={() => setFilter('all')}
          className={`shrink-0 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all ${
            filter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
          }`}
        >
          Todos · {LEGENDS.length}
        </button>
        {(Object.keys(SPECIALTY_CONFIG) as LegendSpecialty[]).map(spec => {
          const cfg = SPECIALTY_CONFIG[spec]
          const active = filter === spec
          return (
            <button
              key={spec}
              onClick={() => setFilter(spec)}
              className="shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all"
              style={
                active
                  ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                  : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              <span>{cfg.emoji}</span>
              {cfg.label} · {specialtyCounts[spec] || 0}
            </button>
          )
        })}
      </div>

      {/* Trading-card grid */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map(l => {
          const spec = SPECIALTY_CONFIG[l.specialty]
          const isSelected = selectedId === l.id
          return (
            <button
              key={l.id}
              onClick={() => setSelectedId(l.id)}
              className="text-left rounded-xl border bg-gradient-to-br from-white/[0.04] to-white/[0.01] hover:scale-[1.02] transition-all overflow-hidden group"
              style={{
                borderColor: isSelected ? `${l.color}60` : 'rgba(255,255,255,0.08)',
                boxShadow: isSelected ? `0 0 24px ${l.color}25` : 'none',
              }}
            >
              {/* Card header band */}
              <div className="h-1.5" style={{ background: `linear-gradient(90deg, ${l.color}, transparent)` }} />

              {/* Top section: avatar + name */}
              <div className="p-3 flex items-start gap-3 border-b border-white/[0.04]">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0" style={{
                  background: `${l.color}15`,
                  border: `2px solid ${l.color}40`,
                  boxShadow: `0 0 12px ${l.color}20`,
                }}>
                  {l.emoji}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <p className="text-sm font-bold text-white truncate">{l.name}</p>
                    {l.invocationsToday > 50 && (
                      <span className="text-[8px] px-1 py-0.5 rounded bg-red-500/20 text-red-400 font-mono">🔥 HOT</span>
                    )}
                  </div>
                  <p className="text-[10px] text-white/40 font-mono">{l.era}</p>
                  <p className="text-[10px] truncate" style={{ color: l.color }}>{l.industry}</p>
                </div>
              </div>

              {/* Hallmark */}
              <div className="p-3 space-y-2">
                <div>
                  <p className="text-[8px] uppercase tracking-widest text-white/40 font-mono mb-0.5">HALLMARK</p>
                  <p className="text-[11px] text-white/80 leading-snug">{l.hallmark}</p>
                </div>

                <div className="rounded-md p-2 bg-black/30 border border-white/[0.05]">
                  <p className="text-[8px] uppercase tracking-widest font-mono mb-0.5" style={{ color: l.color }}>TÉCNICA SIGNATURE</p>
                  <p className="text-[10px] text-white/70 leading-snug italic">{l.signatureTechnique}</p>
                </div>

                {/* Footer stats */}
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase" style={{ background: `${spec.color}18`, color: spec.color }}>
                    {spec.emoji} {spec.label}
                  </span>
                  <span className="text-[10px] text-white/40 flex items-center gap-0.5 tabular-nums">
                    <Activity className="w-2.5 h-2.5" />
                    {l.invocationsToday}
                  </span>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected legend detail */}
      <div className="mx-4 mb-4 rounded-xl border p-5"
        style={{
          background: `linear-gradient(135deg, ${selected.color}0a, transparent)`,
          borderColor: `${selected.color}30`,
          boxShadow: `0 0 24px ${selected.color}12`,
        }}>

        <div className="flex items-start gap-4 mb-4 flex-wrap">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-4xl shrink-0" style={{
            background: `${selected.color}18`,
            border: `2px solid ${selected.color}50`,
            boxShadow: `0 0 16px ${selected.color}30`,
          }}>
            {selected.emoji}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-xl font-black text-white mb-1">{selected.name}</h3>
            <p className="text-xs text-white/60 mb-1">{selected.hallmark}</p>
            <div className="flex items-center gap-3 text-[10px] flex-wrap">
              <span className="text-white/40 font-mono">{selected.era}</span>
              <span style={{ color: selected.color }}>· {selected.industry}</span>
            </div>
          </div>
          <div className="text-right shrink-0">
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-mono">Activado hoy</p>
            <p className="text-2xl font-black tabular-nums" style={{ color: selected.color }}>{selected.invocationsToday}×</p>
          </div>
        </div>

        {/* Quote */}
        <div className="rounded-lg p-3 bg-black/30 border border-white/[0.06] mb-3">
          <div className="flex items-start gap-2">
            <Quote className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{ color: selected.color }} />
            <p className="text-sm text-white/85 italic leading-snug">{selected.quote}</p>
          </div>
        </div>

        {/* Grid: world record + signature */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <div className="rounded-lg p-3 border" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mb-1 flex items-center gap-1">
              <Trophy className="w-2.5 h-2.5" /> RÉCORD MUNDIAL
            </p>
            <p className="text-[11px] text-white/80 leading-snug">{selected.worldRecord}</p>
          </div>
          <div className="rounded-lg p-3 border" style={{ background: `${selected.color}08`, borderColor: `${selected.color}25` }}>
            <p className="text-[9px] uppercase tracking-widest font-bold mb-1 flex items-center gap-1" style={{ color: selected.color }}>
              <Crown className="w-2.5 h-2.5" /> TÉCNICA SIGNATURE
            </p>
            <p className="text-[11px] text-white/80 leading-snug">{selected.signatureTechnique}</p>
          </div>
        </div>

        {/* Sample script */}
        <div className="rounded-lg p-3 bg-gradient-to-br from-emerald-500/[0.05] to-transparent border border-emerald-500/20 mb-3">
          <p className="text-[9px] uppercase tracking-widest text-emerald-400 font-bold mb-2 flex items-center gap-1">
            <Play className="w-2.5 h-2.5" /> SCRIPT QUE LA IA USA · ESTILO {selected.name.toUpperCase()}
          </p>
          <p className="text-sm text-white/90 italic leading-relaxed font-light">{selected.sampleScript}</p>
        </div>

        {/* Active in */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/[0.06] border border-purple-500/20">
          <Bot className="w-3 h-3 text-purple-400 shrink-0" />
          <span className="text-[10px] text-purple-300">Activo en: <span className="text-white font-bold">{selected.activeIn}</span></span>
        </div>
      </div>

      {/* Footer · skill-creator hook */}
      <div className="px-5 py-3 border-t border-white/[0.06] bg-gradient-to-r from-red-500/[0.04] to-transparent flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-[11px] text-white/60">
          <Zap className="w-3 h-3 text-red-400" />
          <span>IA elige al legend correcto según contexto del lead</span>
        </div>
        <button className="text-[11px] px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300 font-bold flex items-center gap-1.5 hover:bg-red-500/30 transition-all">
          <Sparkles className="w-3 h-3" />
          Agregar legend
        </button>
      </div>
    </section>
  )
}
