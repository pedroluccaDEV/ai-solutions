# Landing Page Style Guide — Soluções de IA
**Versão 1.0 — Padrão de Design Replicável**

---

## Visão Geral

Este guia define o sistema de design para todas as landing pages de soluções de IA. Cada página segue a mesma estrutura de seções, componentes e comportamentos — variando apenas a paleta de cores e a tipografia associada. O tema é sempre **claro (light)**.

---

## 1. Estrutura de Seções (Obrigatória)

Todas as landing pages devem conter, nesta ordem:

| # | Seção | ID | Observação |
|---|-------|----|------------|
| 1 | Navegação (Nav) | — | Fixa, pill flutuante |
| 2 | Hero | `#hero` | Split: texto à esq., animação à dir. |
| 3 | Métricas | — | 4 números de impacto |
| 4 | Sobre / O que é | `#sobre` | Texto + card visual de funil/dados |
| 5 | Como funciona | `#como` | 3 passos lineares |
| 6 | Antes × Depois | — | 2 colunas contrastando dores e benefícios |
| 7 | Para quem é | `#quem` | Grid de segmentos/personas |
| 8 | Band "Mais Soluções" | — | Faixa entre seções, sempre presente |
| 9 | Contato | `#contato` | Canais + formulário (obrigatório) |
| 10 | Footer | — | Logo, copyright, links legais |

> **Regra:** Nenhuma seção pode ser removida. A ordem pode ser ajustada levemente, mas as seções Contato e Footer são sempre as duas últimas.

---

## 2. Anatomia da Seção Hero

```
┌─────────────────────────────────────────────┐
│  NAV PILL (fixo, blur, glass)               │
└─────────────────────────────────────────────┘
┌──────────────────┬──────────────────────────┐
│                  │                          │
│  EYEBROW TAG     │                          │
│  H1 (2 linhas)   │   ANIMAÇÃO INTERATIVA    │
│  Subtítulo       │   (varia por produto)    │
│                  │                          │
│  [CTA primário]  │                          │
│  [CTA secundário]│                          │
│                  │                          │
└──────────────────┴──────────────────────────┘
```

### Animação Hero (variável por produto)
A animação à direita do hero **deve sempre**:
- Ser interativa ou auto-animada (não estática)
- Demonstrar o produto em ação
- Usar a paleta de cores da página
- Ter efeito de flutuação suave (`float animation`)
- Ter um glow radial atrás do elemento principal

**Exemplos de animações por tipo de produto:**

| Tipo de Produto | Animação Sugerida |
|----------------|-------------------|
| Atendimento / Chat | Mockup de celular com conversa animada |
| Analytics / Dados | Dashboard com gráficos em tempo real |
| Automação de processos | Flowchart/pipeline animado |
| Geração de conteúdo | Editor com texto sendo gerado |
| Voz / Call center | Visualizador de onda de áudio |
| CRM / Vendas | Kanban animado com cards movendo |

---

## 3. Sistema de Grid e Layout

```css
/* Container principal */
.w {
  max-width: 1060px;
  margin: 0 auto;
  padding: 0 28px;
}

/* Seções */
section { padding: 88px 0; }
.sec-alt { background: var(--off); } /* seções alternadas com fundo levemente diferente */

/* Hero */
.hero-g { grid-template-columns: 1.05fr 0.95fr; gap: 56px; }

/* Seções de 2 colunas (Sobre, Contato) */
.two-col { grid-template-columns: 1fr 1fr; gap: 48px; }

/* Grid de 3 colunas (Como funciona, Para quem) */
.three-col { grid-template-columns: repeat(3, 1fr); gap: 18px; }

/* Grid de métricas (4 colunas) */
.met-box { grid-template-columns: repeat(4, 1fr); }
```

**Breakpoint mobile (≤768px):** todas as grades colapsam para 1 coluna. Métricas colapsam para 2×2. A animação hero é ocultada.

---

## 4. Componentes Reutilizáveis

### 4.1 Nav Pill
- Posição: `fixed`, `top: 14px`, centralizado com `max-width: 1060px`
- Fundo: `rgba(255,255,255,0.7)` + `backdrop-filter: blur(28px)`
- Borda: `1px solid var(--bdr2)`, `border-radius: 18px`
- Conteúdo: Logo (ícone + nome) → links de nav → botão CTA
- O botão CTA da nav sempre aponta para `#contato`

### 4.2 Eyebrow Tag (`.ep`)
```css
display: inline-flex; align-items: center; gap: 7px;
font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--acc); background: rgba(var(--acc-rgb), 0.08);
border: 1px solid rgba(var(--acc-rgb), 0.18);
padding: 5px 13px; border-radius: 100px;
```
- Sempre acompanhado de um ícone Lucide (tamanho 11px)
- Texto em uppercase descreve a proposta de valor macro

### 4.3 Glass Card (`.g`)
```css
background: rgba(255,255,255,0.72);
backdrop-filter: blur(22px);
border: 1px solid var(--bdr2);
border-radius: 18px;
box-shadow: 0 2px 16px rgba(var(--acc-rgb), 0.04);
transition: all 0.22s;
```
**Hover:** `translateY(-2px)`, sombra mais intensa, borda mais marcada.

### 4.4 Seção Header (`.sh`)
```css
display: inline-flex; align-items: center; gap: 6px;
font-size: 0.7rem; font-weight: 700; letter-spacing: 0.09em;
text-transform: uppercase; color: var(--acc);
margin-bottom: 13px;
```
- Sempre com ícone Lucide 11px
- Precede o `h2` de cada seção

### 4.5 Botões CTA
```css
/* Primário */
.bp {
  background: var(--acc); color: white;
  padding: 12px 22px; border-radius: 11px;
  font-size: 0.9rem; font-weight: 600;
}
.bp:hover { background: var(--acc-dark); transform: translateY(-2px); box-shadow: 0 10px 26px rgba(var(--acc-rgb), 0.28); }

/* Secundário (outline) */
.bo {
  background: transparent; color: var(--text);
  border: 1px solid var(--bdr2);
  padding: 12px 22px; border-radius: 11px;
}
.bo:hover { background: var(--surf); }
```

### 4.6 Card de Passo (Como funciona)
- Número em badge quadrado com fundo tintado
- H3 + parágrafo descritivo
- Linha conectora horizontal entre os 3 cards (via pseudo-elemento `::before`)

### 4.7 Cards Antes × Depois
- Dois cards lado a lado
- "Antes": borda e tint em vermelho (`--red`)
- "Depois": borda e tint em verde (`--acc`)
- Cada item usa ícone `XCircle` (vermelho) ou `CheckCircle2` (verde) da Lucide

### 4.8 Formulário de Contato (Obrigatório)
```
┌─────────────────────────────────────┐
│ Enviar mensagem                     │
│                                     │
│ [Nome]          [Empresa]           │
│ [E-mail]                            │
│ [Como podemos ajudar? — textarea]   │
│                                     │
│ [Enviar mensagem →]                 │
└─────────────────────────────────────┘
```
- Após envio: exibe estado de sucesso com ícone `Check`
- O botão de envio usa gradiente de `var(--acc)` para `var(--acc2)`

### 4.9 Cards de Canal de Contato (Obrigatório)
Três canais mínimos obrigatórios:
- **WhatsApp** — ícone `MessageSquare`, link `wa.me`
- **E-mail** — ícone `Mail`, link `mailto:`
- **Telefone** — ícone `Phone`, link `tel:`

Estrutura de cada card:
```
[Ícone colorido] [Label bold] [Detalhe/horário] [ChevronRight]
```

### 4.10 Faixa "Mais Soluções"
- Posicionada entre "Para quem" e "Contato"
- Fundo semitransparente com blur
- Ícone `Layers` + texto descritivo + botão-pill `ExternalLink`
- Sempre presente — permite cross-sell entre produtos

### 4.11 Aurora Background
- 4 blobs radiais animados em posição `fixed`
- Cores derivadas da paleta da página (`--acc`, `--acc2`, `--acc3`)
- `filter: blur(70–90px)`, opacidade baixa
- `z-index: 0`, `pointer-events: none`
- Duração de animação variada (21s–33s) para evitar sincronia

---

## 5. Iconografia

**Biblioteca obrigatória:** [Lucide React](https://lucide.dev)

### Ícones por Seção

| Seção | Ícones usados |
|-------|--------------|
| Nav / Logo | `Zap` (ou ícone do produto) |
| Hero eyebrow | `Activity`, `Sparkles`, `Zap` |
| Métricas | sem ícone (só números) |
| Sobre — cards | `Zap`, `Target`, `BarChart3` |
| Como funciona | `MessageSquare`, `Zap`, `CheckCircle2` |
| Antes × Depois | `XCircle`, `CheckCircle2` |
| Para quem | ícone por segmento (veja abaixo) |
| Contato canais | `MessageSquare`, `Mail`, `Phone` |
| Mais Soluções | `Layers`, `ExternalLink` |
| Footer | `ChevronRight` |

### Ícones de Segmento por Nicho

| Nicho | Ícone |
|-------|-------|
| Saúde / Clínicas | `HeartPulse` |
| Imóveis | `Building2` |
| Estética / Beleza | `Sparkles` |
| Educação | `GraduationCap` |
| Serviços / Técnico | `Wrench` |
| E-commerce / Varejo | `ShoppingBag` |
| Financeiro | `TrendingUp` |
| Jurídico | `Shield` |
| Tecnologia | `Globe` |
| Marketing | `MousePointerClick` |

> **Regra de tamanho:** ícones em text = 11–13px; ícones em cards = 15–17px; ícones em badges de canal = 16px; ícones decorativos = 12px.

---

## 6. Tipografia

Cada paleta define sua própria dupla tipográfica. A regra é:
- **Display / Headings:** fonte com personalidade forte
- **Serif itálico:** fonte complementar para destaques em `h1`, `h2` (a palavra-chave do título)
- **Body / UI:** fonte limpa e altamente legível

### Escala Tipográfica

| Token | Tamanho | Peso | Uso |
|-------|---------|------|-----|
| `h1` | `clamp(2.1rem, 4.4vw, 3.3rem)` | 700 | Título hero |
| `h2` | `clamp(1.65rem, 3.4vw, 2.45rem)` | 700 | Títulos de seção |
| `h3` | `0.92rem` | 700 | Cards e subsections |
| `h4` | `0.88rem` | 700 | Segmentos |
| body | `1rem` | 400 | Parágrafos |
| small | `0.83rem` | 400 | Labels, campos |
| micro | `0.72–0.78rem` | 500–700 | Tags, badges, eyebrows |

### Regra do Itálico em Títulos
Todo `h1` e `h2` tem uma palavra ou frase-chave em `font-style: italic` usando a fonte serif da paleta, na cor `var(--acc)`. Isso cria identidade visual consistente entre as páginas.

---

## 7. Paletas de Cores

Cada paleta inclui: tokens CSS, dupla tipográfica e personalidade.

---

### Paleta 1 — Verde Esmeralda *(base deste guia)*
**Personalidade:** Confiança, crescimento, tecnologia acessível

```css
:root {
  --white: #ffffff;
  --off:   #f4fbf6;
  --surf:  #edf7f0;
  --bdr:   rgba(30,120,60,0.10);
  --bdr2:  rgba(30,120,60,0.18);
  --text:  #081a0e;
  --muted: #4a6855;
  --subt:  #7aa886;
  --acc:   #16a34a;
  --acc2:  #059669;
  --acc3:  #0d9488;
  --acc-rgb: 22,163,74;
  --acc-dark: #15803d;
  --red:   #dc2626;
  --font:  'Geist', 'Inter', sans-serif;
  --serif: 'Lora', Georgia, serif;
}
```

**Tipografia:** Geist (display) + Lora Italic (destaque)
**Google Fonts:** `Geist:wght@300;400;500;600;700` + `Lora:ital,wght@1,400;1,500`
**Aurora blobs:** `rgba(74,222,128,*)`, `rgba(16,185,129,*)`, `rgba(20,184,166,*)`

---

### Paleta 2 — Azul Safira
**Personalidade:** Tecnologia, precisão, corporativo moderno

```css
:root {
  --white: #ffffff;
  --off:   #f0f6ff;
  --surf:  #e8f0fe;
  --bdr:   rgba(30,80,200,0.10);
  --bdr2:  rgba(30,80,200,0.18);
  --text:  #07112b;
  --muted: #3d5a8a;
  --subt:  #7090c0;
  --acc:   #2563eb;
  --acc2:  #1d4ed8;
  --acc3:  #0ea5e9;
  --acc-rgb: 37,99,235;
  --acc-dark: #1e40af;
  --red:   #dc2626;
  --font:  'DM Sans', 'Inter', sans-serif;
  --serif: 'Playfair Display', Georgia, serif;
}
```

**Tipografia:** DM Sans (display) + Playfair Display Italic (destaque)
**Google Fonts:** `DM+Sans:wght@300;400;500;600;700` + `Playfair+Display:ital,wght@1,400;1,600`
**Aurora blobs:** `rgba(96,165,250,*)`, `rgba(14,165,233,*)`, `rgba(99,102,241,*)`

---

### Paleta 3 — Âmbar Dourado
**Personalidade:** Premium, resultados, conversão, energia

```css
:root {
  --white: #ffffff;
  --off:   #fffbf0;
  --surf:  #fef3c7;
  --bdr:   rgba(160,100,0,0.10);
  --bdr2:  rgba(160,100,0,0.18);
  --text:  #1c0f00;
  --muted: #7c5c20;
  --subt:  #b08040;
  --acc:   #d97706;
  --acc2:  #b45309;
  --acc3:  #f59e0b;
  --acc-rgb: 217,119,6;
  --acc-dark: #92400e;
  --red:   #dc2626;
  --font:  'Syne', 'Inter', sans-serif;
  --serif: 'Cormorant Garamond', Georgia, serif;
}
```

**Tipografia:** Syne (display) + Cormorant Garamond Italic (destaque)
**Google Fonts:** `Syne:wght@400;500;600;700;800` + `Cormorant+Garamond:ital,wght@1,400;1,600`
**Aurora blobs:** `rgba(251,191,36,*)`, `rgba(245,158,11,*)`, `rgba(249,115,22,*)`

---

### Paleta 4 — Violeta Púrpura
**Personalidade:** Inovação, criatividade, IA de ponta, agências

```css
:root {
  --white: #ffffff;
  --off:   #faf6ff;
  --surf:  #f3e8ff;
  --bdr:   rgba(120,40,200,0.10);
  --bdr2:  rgba(120,40,200,0.18);
  --text:  #120a1e;
  --muted: #5b3f82;
  --subt:  #9b74c0;
  --acc:   #7c3aed;
  --acc2:  #6d28d9;
  --acc3:  #a855f7;
  --acc-rgb: 124,58,237;
  --acc-dark: #5b21b6;
  --red:   #dc2626;
  --font:  'Space Grotesk', 'Inter', sans-serif;
  --serif: 'DM Serif Display', Georgia, serif;
}
```

**Tipografia:** Space Grotesk (display) + DM Serif Display Italic (destaque)
**Google Fonts:** `Space+Grotesk:wght@300;400;500;600;700` + `DM+Serif+Display:ital@1`
**Aurora blobs:** `rgba(167,139,250,*)`, `rgba(168,85,247,*)`, `rgba(99,102,241,*)`

---

### Paleta 5 — Slate Grafite
**Personalidade:** Minimalismo sofisticado, B2B enterprise, seriedade

```css
:root {
  --white: #ffffff;
  --off:   #f6f7f9;
  --surf:  #eef0f4;
  --bdr:   rgba(60,70,90,0.10);
  --bdr2:  rgba(60,70,90,0.18);
  --text:  #0d1117;
  --muted: #4a5568;
  --subt:  #8895aa;
  --acc:   #334155;
  --acc2:  #1e293b;
  --acc3:  #475569;
  --acc-rgb: 51,65,85;
  --acc-dark: #0f172a;
  --red:   #dc2626;
  --font:  'Instrument Sans', 'Inter', sans-serif;
  --serif: 'Instrument Serif', Georgia, serif;
}
```

**Tipografia:** Instrument Sans (display) + Instrument Serif Italic (destaque)
**Google Fonts:** `Instrument+Sans:wght@400;500;600;700` + `Instrument+Serif:ital@1`
**Aurora blobs:** `rgba(148,163,184,*)`, `rgba(100,116,139,*)`, `rgba(71,85,105,*)`

> **Nota Paleta 5:** O CTA primário usa `--acc` (escuro), não verde. O hover usa `--acc-dark`. Para acentos positivos (ícones de checkmark, etc.), use `--acc3`.

---

## 8. Tabela Resumo de Paletas

| # | Nome | Acento | Font Display | Font Serif | Melhor Para |
|---|------|--------|-------------|------------|-------------|
| 1 | Verde Esmeralda | `#16a34a` | Geist | Lora | Atendimento, saúde, varejo |
| 2 | Azul Safira | `#2563eb` | DM Sans | Playfair Display | SaaS, dados, analytics |
| 3 | Âmbar Dourado | `#d97706` | Syne | Cormorant Garamond | Vendas, conversão, premium |
| 4 | Violeta Púrpura | `#7c3aed` | Space Grotesk | DM Serif Display | Agências, criativo, IA avançada |
| 5 | Slate Grafite | `#334155` | Instrument Sans | Instrument Serif | Enterprise, B2B, consultoria |

---

## 9. Efeito Aurora (Background)

Cada página tem 4 blobs radiais animados em `position: fixed`:

```css
.aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }

.ab {
  position: absolute; border-radius: 50%;
  animation: af linear infinite; will-change: transform;
}

/* Posições padrão dos 4 blobs */
.ab1 { width: 820px; height: 520px; top: -180px;  left: -160px;  filter: blur(72px); animation-duration: 26s; }
.ab2 { width: 600px; height: 460px; top:   50px;  right: -100px; filter: blur(80px); animation-duration: 33s; animation-delay: -10s; }
.ab3 { width: 680px; height: 400px; top:  260px;  left:    25%;  filter: blur(90px); animation-duration: 21s; animation-delay:  -6s; }
.ab4 { width: 480px; height: 360px; bottom: 160px; right: 12%;  filter: blur(70px); animation-duration: 29s; animation-delay: -16s; }

@keyframes af {
  0%   { transform: translate(0,0) scale(1); }
  25%  { transform: translate(32px,-44px) scale(1.06); }
  50%  { transform: translate(58px,-6px) scale(0.94); }
  75%  { transform: translate(18px,30px) scale(1.05); }
  100% { transform: translate(0,0) scale(1); }
}
```

As cores de cada blob devem ser derivadas de `--acc`, `--acc2`, `--acc3` com opacidade de **0.06–0.32**.

---

## 10. Animações e Comportamentos

### Reveal ao Scroll
Todos os cards e elementos de seção usam `IntersectionObserver` para entrada:

```css
.rev { opacity: 0; transform: translateY(14px); transition: opacity .5s ease, transform .5s ease; }
.rev.vis { opacity: 1; transform: translateY(0); }
```

Adicionar `transition-delay` incremental nos grids:
```
card 1: delay 0s
card 2: delay 0.1s
card 3: delay 0.2s
```

### Animação de Entrada Hero
```css
@keyframes up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Stagger por elemento */
.ep  { animation: up 0.6s 0.0s ease both; }
h1   { animation: up 0.6s 0.1s ease both; }
.hp  { animation: up 0.6s 0.2s ease both; }
.ctas{ animation: up 0.6s 0.3s ease both; }
```

### Float da Animação Hero
```css
@keyframes heroFloat {
  0%, 100% { transform: rotateY(-14deg) rotateX(5deg) translateY(0px); }
  50%       { transform: rotateY(-8deg)  rotateX(3deg) translateY(-12px); }
}
.hero-visual { animation: heroFloat 6s ease-in-out infinite; }
```

### Glow Pulsante
```css
@keyframes glowPulse {
  0%, 100% { opacity: 0.7; transform: translate(-50%,-50%) scale(1); }
  50%       { opacity: 1;   transform: translate(-50%,-50%) scale(1.15); }
}
.hero-glow { animation: glowPulse 4s ease-in-out infinite; }
```

---

## 11. Checklist de Nova Landing Page

Ao criar uma nova landing page, verificar:

**Setup**
- [ ] Escolher paleta (1–5)
- [ ] Importar fontes corretas do Google Fonts
- [ ] Definir todos os tokens CSS da paleta escolhida
- [ ] Configurar 4 blobs aurora com cores da paleta

**Seções**
- [ ] Nav pill com logo + 4 links + botão CTA
- [ ] Hero: eyebrow + H1 com itálico + subtítulo + 2 CTAs + animação interativa
- [ ] Métricas: 4 números de impacto relevantes ao produto
- [ ] Sobre: texto explicativo + card visual (funil, gráfico, demo)
- [ ] Como funciona: 3 passos com ícones Lucide
- [ ] Antes × Depois: dores vs. benefícios com `XCircle` e `CheckCircle2`
- [ ] Para quem: grid de segmentos com ícone + título + descrição
- [ ] Faixa "Mais Soluções" com `Layers` e `ExternalLink`
- [ ] Contato: 3 canais (WhatsApp, Email, Tel) + formulário completo
- [ ] Footer: logo + copyright + links legais

**Qualidade**
- [ ] Todos os ícones são da biblioteca Lucide React
- [ ] Scroll reveal em todos os cards de seção
- [ ] Animação float na visual do hero
- [ ] Formulário com estado de sucesso após envio
- [ ] Responsivo: teste em 375px de largura
- [ ] Smooth scroll em todos os links de nav

---

## 12. Variáveis CSS — Template Base

```css
:root {
  /* Superfícies */
  --white:    #ffffff;
  --off:      /* fundo levemente tintado de seções alt */;
  --surf:     /* fundo de elementos internos */;

  /* Bordas */
  --bdr:      /* borda sutil */;
  --bdr2:     /* borda um pouco mais visível */;

  /* Texto */
  --text:     /* cor principal do texto */;
  --muted:    /* texto secundário */;
  --subt:     /* texto terciário / placeholders */;

  /* Acentos */
  --acc:      /* cor primária de ação */;
  --acc2:     /* variação escura do acento */;
  --acc3:     /* acento complementar (terceiro tom) */;
  --acc-rgb:  /* R,G,B do --acc para uso em rgba() */;
  --acc-dark: /* versão mais escura para hover */;

  /* Estado */
  --red:      #dc2626; /* erro, negativo — constante em todas as paletas */

  /* Tipografia */
  --font:     'Display Font', sans-serif;
  --serif:    'Serif Font', Georgia, serif;
}
```

---

*Este documento é a fonte de verdade para o desenvolvimento de landing pages de soluções de IA. Qualquer divergência de implementação deve ser resolvida com base neste guia.*