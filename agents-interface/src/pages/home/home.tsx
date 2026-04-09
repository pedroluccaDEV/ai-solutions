import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  Zap, Layers, ExternalLink, ArrowRight, ChevronRight,
  MessageSquare, Mail, Phone, CheckCircle2,
  CalendarCheck, BarChart3, FileText, Users,
  Bot, TrendingUp, Target, Sparkles, Activity,
  Star, Globe, Shield, Menu, X, MoveRight
} from "lucide-react";

/* ─────────────────────────────────────────────
   TOKENS — Paleta Verde Esmeralda (base)
   + tokens neutros para cards multi-paleta
───────────────────────────────────────────── */
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@1,400;1,500&family=Geist:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --white:    #ffffff;
    --off:      #f4fbf6;
    --surf:     #edf7f0;
    --bdr:      rgba(30,120,60,0.10);
    --bdr2:     rgba(30,120,60,0.18);
    --text:     #081a0e;
    --muted:    #4a6855;
    --subt:     #7aa886;
    --acc:      #16a34a;
    --acc2:     #059669;
    --acc3:     #0d9488;
    --acc-rgb:  22,163,74;
    --acc-dark: #15803d;
    --red:      #dc2626;
    --font:     'Geist', 'Inter', sans-serif;
    --serif:    'Lora', Georgia, serif;
  }

  html { scroll-behavior: smooth; }
  body {
    font-family: var(--font);
    color: var(--text);
    background: var(--white);
    line-height: 1.6;
    overflow-x: hidden;
  }

  /* ── Aurora ── */
  .aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
  .ab { position: absolute; border-radius: 50%; animation: af linear infinite; will-change: transform; }
  .ab1 { width:820px; height:520px; top:-180px; left:-160px; background:rgba(74,222,128,0.13); filter:blur(72px); animation-duration:26s; }
  .ab2 { width:600px; height:460px; top:50px; right:-100px; background:rgba(16,185,129,0.10); filter:blur(80px); animation-duration:33s; animation-delay:-10s; }
  .ab3 { width:680px; height:400px; top:260px; left:25%; background:rgba(20,184,166,0.09); filter:blur(90px); animation-duration:21s; animation-delay:-6s; }
  .ab4 { width:480px; height:360px; bottom:160px; right:12%; background:rgba(74,222,128,0.08); filter:blur(70px); animation-duration:29s; animation-delay:-16s; }
  @keyframes af {
    0%   { transform: translate(0,0) scale(1); }
    25%  { transform: translate(32px,-44px) scale(1.06); }
    50%  { transform: translate(58px,-6px) scale(0.94); }
    75%  { transform: translate(18px,30px) scale(1.05); }
    100% { transform: translate(0,0) scale(1); }
  }

  /* ── Layout ── */
  .w { max-width: 1060px; margin: 0 auto; padding: 0 28px; }
  section { padding: 88px 0; position: relative; z-index: 1; }
  .sec-alt { background: var(--off); }

  /* ── Nav ── */
  .nav-wrap { position: fixed; top: 14px; left: 0; right: 0; z-index: 100; display: flex; justify-content: center; padding: 0 28px; }
  .nav-pill {
    max-width: 1060px; width: 100%;
    background: rgba(255,255,255,0.72); backdrop-filter: blur(28px);
    border: 1px solid var(--bdr2); border-radius: 18px;
    padding: 10px 20px; display: flex; align-items: center; justify-content: space-between;
  }
  .nav-logo { display:flex; align-items:center; gap:8px; font-weight:700; font-size:0.95rem; color:var(--text); text-decoration:none; }
  .nav-logo-icon { width:30px; height:30px; background:var(--acc); border-radius:8px; display:grid; place-items:center; }
  .nav-links { display:flex; align-items:center; gap:4px; }
  .nav-links a { font-size:0.83rem; font-weight:500; color:var(--muted); padding:6px 12px; border-radius:8px; text-decoration:none; transition:all .18s; }
  .nav-links a:hover { background:var(--surf); color:var(--text); }
  .nav-cta { background:var(--acc); color:white; font-size:0.82rem; font-weight:600; padding:8px 16px; border-radius:9px; text-decoration:none; transition:all .18s; white-space:nowrap; }
  .nav-cta:hover { background:var(--acc-dark); transform:translateY(-1px); }
  .nav-mob { display:none; background:none; border:none; cursor:pointer; color:var(--text); }

  /* ── Hero ── */
  .hero-section { padding: 140px 0 88px; text-align: center; }
  .ep {
    display:inline-flex; align-items:center; gap:7px;
    font-size:0.72rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
    color:var(--acc); background:rgba(22,163,74,0.08); border:1px solid rgba(22,163,74,0.18);
    padding:5px 13px; border-radius:100px; margin-bottom:20px;
  }
  .hero-h1 { font-size:clamp(2.4rem,5vw,3.8rem); font-weight:700; line-height:1.14; letter-spacing:-0.025em; margin-bottom:20px; }
  .hero-h1 em { font-style:italic; font-family:var(--serif); color:var(--acc); }
  .hero-p { font-size:1.08rem; color:var(--muted); line-height:1.65; max-width:560px; margin:0 auto 36px; }

  /* CTA pair */
  .ctas { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:56px; }
  .bp { background:var(--acc); color:white; padding:13px 24px; border-radius:11px; font-size:0.92rem; font-weight:600; text-decoration:none; display:inline-flex; align-items:center; gap:8px; transition:all .22s; border:none; cursor:pointer; }
  .bp:hover { background:var(--acc-dark); transform:translateY(-2px); box-shadow:0 10px 26px rgba(22,163,74,0.28); }
  .bo { background:transparent; color:var(--text); border:1px solid var(--bdr2); padding:13px 24px; border-radius:11px; font-size:0.92rem; font-weight:500; text-decoration:none; display:inline-flex; align-items:center; gap:8px; transition:all .22s; cursor:pointer; }
  .bo:hover { background:var(--surf); transform:translateY(-1px); }

  /* Stats strip */
  .stats-strip { display:flex; align-items:center; justify-content:center; gap:0; border:1px solid var(--bdr2); border-radius:16px; overflow:hidden; background:rgba(255,255,255,0.7); backdrop-filter:blur(20px); }
  .stat-item { flex:1; padding:20px 24px; text-align:center; border-right:1px solid var(--bdr); }
  .stat-item:last-child { border-right:none; }
  .stat-num { font-size:1.6rem; font-weight:700; color:var(--acc); line-height:1; font-family:var(--serif); font-style:italic; }
  .stat-lbl { font-size:0.75rem; color:var(--muted); margin-top:4px; }

  /* ── Section header ── */
  .sh { display:inline-flex; align-items:center; gap:6px; font-size:0.7rem; font-weight:700; letter-spacing:0.09em; text-transform:uppercase; color:var(--acc); margin-bottom:13px; }
  .sec-h2 { font-size:clamp(1.65rem,3.4vw,2.45rem); font-weight:700; line-height:1.22; letter-spacing:-0.015em; margin-bottom:14px; }
  .sec-h2 em { font-style:italic; font-family:var(--serif); color:var(--acc); }
  .sec-sub { font-size:1rem; color:var(--muted); line-height:1.65; }

  /* ── Filter tabs ── */
  .filter-bar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:40px; }
  .ftab { display:inline-flex; align-items:center; gap:6px; padding:7px 16px; border-radius:100px; font-size:0.8rem; font-weight:600; border:1px solid var(--bdr2); background:white; color:var(--muted); cursor:pointer; transition:all .18s; }
  .ftab:hover { border-color:rgba(22,163,74,0.3); color:var(--acc); }
  .ftab.active { background:var(--acc); color:white; border-color:var(--acc); }

  /* ── Solution Cards ── */
  .sol-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }

  .sol-card {
    background:rgba(255,255,255,0.82); backdrop-filter:blur(22px);
    border:1px solid var(--bdr2); border-radius:22px;
    padding:0; overflow:hidden;
    transition:all 0.26s; cursor:pointer; text-decoration:none; display:flex; flex-direction:column;
    position:relative;
  }
  .sol-card:hover { transform:translateY(-4px); box-shadow:0 16px 48px rgba(22,163,74,0.13); }
  .sol-card:hover .sol-arrow { transform:translateX(3px); }

  .sol-card-top { padding:24px 24px 0; }
  .sol-card-ico-wrap { width:48px; height:48px; border-radius:13px; display:grid; place-items:center; margin-bottom:16px; }
  .sol-card-tag {
    display:inline-flex; align-items:center; gap:5px;
    font-size:0.65rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
    padding:3px 9px; border-radius:100px; margin-bottom:12px;
  }
  .sol-card h3 { font-size:1rem; font-weight:700; margin-bottom:8px; line-height:1.3; }
  .sol-card p { font-size:0.82rem; color:var(--muted); line-height:1.55; margin-bottom:20px; }

  .sol-card-metrics { display:flex; gap:0; border-top:1px solid var(--bdr); margin:0 0 0; }
  .sol-metric { flex:1; padding:12px 16px; border-right:1px solid var(--bdr); }
  .sol-metric:last-child { border-right:none; }
  .sol-metric-val { font-size:0.95rem; font-weight:700; line-height:1; }
  .sol-metric-lbl { font-size:0.62rem; color:var(--muted); margin-top:2px; }

  .sol-card-footer { padding:14px 24px; display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--bdr); margin-top:auto; }
  .sol-cta { font-size:0.82rem; font-weight:600; display:flex; align-items:center; gap:6px; }
  .sol-arrow { transition:transform .2s; }

  /* Featured card (spans 2 cols) */
  .sol-card.featured { grid-column: span 2; flex-direction:row; }
  .sol-card.featured .sol-card-top { flex:1; padding:28px; display:flex; flex-direction:column; }
  .sol-card.featured .sol-card-visual { width:260px; flex-shrink:0; background:var(--off); display:flex; align-items:center; justify-content:center; padding:24px; border-left:1px solid var(--bdr); }

  /* ── Como funciona ── */
  .steps-g { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin-top:52px; position:relative; }
  .steps-g::before { content:''; position:absolute; top:28px; left:calc(16.66% + 9px); right:calc(16.66% + 9px); height:1px; background:linear-gradient(90deg,var(--acc),var(--acc3)); opacity:0.3; }
  .step-card { padding:28px 22px; }
  .step-num { width:40px; height:40px; background:rgba(22,163,74,0.1); border-radius:10px; display:grid; place-items:center; font-size:0.78rem; font-weight:800; color:var(--acc); margin-bottom:18px; }
  .step-card h3 { font-size:0.92rem; font-weight:700; margin-bottom:8px; }
  .step-card p { font-size:0.83rem; color:var(--muted); line-height:1.55; }

  /* Glass card */
  .g { background:rgba(255,255,255,0.72); backdrop-filter:blur(22px); border:1px solid var(--bdr2); border-radius:18px; box-shadow:0 2px 16px rgba(22,163,74,0.04); transition:all 0.22s; padding:24px; }
  .g:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(22,163,74,0.12); border-color:rgba(22,163,74,0.28); }

  /* ── Mais Soluções band ── */
  .mais-band { background:rgba(22,163,74,0.04); border-top:1px solid rgba(22,163,74,0.1); border-bottom:1px solid rgba(22,163,74,0.1); padding:28px 0; position:relative; z-index:1; }
  .mais-inner { display:flex; align-items:center; gap:16px; }
  .mais-ico { width:40px; height:40px; background:rgba(22,163,74,0.1); border-radius:10px; display:grid; place-items:center; color:var(--acc); flex-shrink:0; }
  .mais-text strong { font-size:0.9rem; font-weight:700; display:block; margin-bottom:2px; }
  .mais-text span { font-size:0.82rem; color:var(--muted); }
  .mais-pill { display:inline-flex; align-items:center; gap:6px; font-size:0.82rem; font-weight:600; color:var(--acc); background:white; border:1px solid var(--bdr2); padding:8px 16px; border-radius:100px; text-decoration:none; transition:all .18s; white-space:nowrap; }
  .mais-pill:hover { background:var(--surf); transform:translateY(-1px); }

  /* ── Contato ── */
  .contato-g { display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:start; }
  .canal-list { display:flex; flex-direction:column; gap:12px; }
  .canal { display:flex; align-items:center; gap:14px; padding:16px; border-radius:14px; border:1px solid var(--bdr2); background:white; text-decoration:none; transition:all .22s; cursor:pointer; }
  .canal:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(22,163,74,0.1); border-color:rgba(22,163,74,0.25); }
  .canal-ico { width:40px; height:40px; border-radius:10px; display:grid; place-items:center; flex-shrink:0; }
  .canal-ico.wpp  { background:rgba(22,163,74,0.1); color:var(--acc); }
  .canal-ico.mail { background:rgba(5,150,105,0.1); color:var(--acc2); }
  .canal-ico.tel  { background:rgba(13,148,136,0.1); color:var(--acc3); }
  .canal-info strong { font-size:0.88rem; font-weight:700; display:block; }
  .canal-info span { font-size:0.78rem; color:var(--muted); }
  .canal-arrow { margin-left:auto; color:var(--subt); }

  .form-card { background:white; border:1px solid var(--bdr2); border-radius:20px; padding:28px; }
  .form-title { font-size:1rem; font-weight:700; margin-bottom:20px; }
  .form-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }
  .form-field { display:flex; flex-direction:column; gap:5px; margin-bottom:12px; }
  .form-field label { font-size:0.78rem; font-weight:600; color:var(--muted); }
  .form-field input, .form-field textarea, .form-field select {
    padding:10px 13px; border-radius:9px; border:1px solid var(--bdr2);
    font-family:var(--font); font-size:0.85rem; color:var(--text); background:var(--off);
    transition:border .18s; outline:none; resize:none;
  }
  .form-field input:focus, .form-field textarea:focus, .form-field select:focus { border-color:rgba(22,163,74,0.4); background:white; }
  .form-btn { width:100%; padding:13px; border-radius:11px; border:none; cursor:pointer; background:linear-gradient(135deg,var(--acc),var(--acc2)); color:white; font-weight:600; font-size:0.92rem; font-family:var(--font); display:flex; align-items:center; justify-content:center; gap:8px; transition:all .22s; }
  .form-btn:hover { transform:translateY(-2px); box-shadow:0 10px 26px rgba(22,163,74,0.28); }
  .success-state { text-align:center; padding:32px 0; }
  .success-ico { width:56px; height:56px; background:rgba(22,163,74,0.1); border-radius:50%; display:grid; place-items:center; color:var(--acc); margin:0 auto 16px; }

  /* ── Footer ── */
  .footer { border-top:1px solid var(--bdr); padding:32px 0; position:relative; z-index:1; }
  .footer-inner { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px; }
  .footer-logo { display:flex; align-items:center; gap:8px; font-weight:700; font-size:0.9rem; text-decoration:none; color:var(--text); }
  .footer-links { display:flex; gap:20px; }
  .footer-links a { font-size:0.78rem; color:var(--subt); text-decoration:none; display:flex; align-items:center; gap:4px; transition:color .18s; }
  .footer-links a:hover { color:var(--acc); }

  /* ── Scroll reveal ── */
  .rev { opacity:0; transform:translateY(14px); transition:opacity .5s ease, transform .5s ease; }
  .rev.vis { opacity:1; transform:translateY(0); }
  .rev.d1 { transition-delay:0.0s; }
  .rev.d2 { transition-delay:0.1s; }
  .rev.d3 { transition-delay:0.2s; }
  .rev.d4 { transition-delay:0.3s; }

  /* ── Hero stagger ── */
  @keyframes up { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  .a0 { animation: up 0.65s 0.00s ease both; }
  .a1 { animation: up 0.65s 0.10s ease both; }
  .a2 { animation: up 0.65s 0.20s ease both; }
  .a3 { animation: up 0.65s 0.32s ease both; }
  .a4 { animation: up 0.65s 0.44s ease both; }

  /* ── Marquee ticker ── */
  .ticker-wrap { overflow:hidden; border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr); padding:12px 0; background:rgba(255,255,255,0.5); backdrop-filter:blur(10px); position:relative; z-index:1; }
  .ticker-inner { display:flex; gap:0; animation:ticker 28s linear infinite; white-space:nowrap; width:max-content; }
  .ticker-item { display:inline-flex; align-items:center; gap:8px; padding:0 32px; font-size:0.78rem; font-weight:600; color:var(--muted); }
  .ticker-dot { width:5px; height:5px; border-radius:50%; background:var(--acc); flex-shrink:0; }
  @keyframes ticker { from { transform:translateX(0); } to { transform:translateX(-50%); } }

  /* ── Marquee logos row ── */
  .nicho-row { display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-top:32px; }
  .nicho-pill { display:inline-flex; align-items:center; gap:7px; padding:8px 16px; border-radius:100px; border:1px solid var(--bdr2); background:white; font-size:0.8rem; font-weight:600; color:var(--muted); transition:all .18s; }
  .nicho-pill:hover { border-color:rgba(22,163,74,0.3); color:var(--acc); transform:translateY(-1px); }

  /* ── Responsive ── */
  @media (max-width: 768px) {
    .sol-grid { grid-template-columns:1fr; }
    .sol-card.featured { grid-column:span 1; flex-direction:column; }
    .sol-card.featured .sol-card-visual { display:none; }
    .steps-g { grid-template-columns:1fr; }
    .steps-g::before { display:none; }
    .contato-g { grid-template-columns:1fr; }
    .nav-links { display:none; }
    .nav-mob { display:block; }
    .stats-strip { display:grid; grid-template-columns:1fr 1fr; }
    .stat-item:nth-child(2) { border-right:none; }
    .stat-item:nth-child(3) { border-right:1px solid var(--bdr); border-top:1px solid var(--bdr); }
    .stat-item:nth-child(4) { border-top:1px solid var(--bdr); }
    .form-row { grid-template-columns:1fr; }
    .footer-inner { flex-direction:column; text-align:center; }
    .footer-links { justify-content:center; }
    .mais-inner { flex-wrap:wrap; }
    section { padding:60px 0; }
    .hero-section { padding:110px 0 60px; }
    .ctas { flex-direction:column; align-items:center; }
  }
`;

/* ── Paleta accent por solução ── */
const palettes: Record<string, { acc: string; rgb: string; bg: string; border: string; tagBg: string; tagColor: string }> = {
  green:  { acc:"#16a34a", rgb:"22,163,74",   bg:"rgba(22,163,74,0.08)",   border:"rgba(22,163,74,0.18)",   tagBg:"rgba(22,163,74,0.08)",   tagColor:"#16a34a" },
  blue:   { acc:"#2563eb", rgb:"37,99,235",   bg:"rgba(37,99,235,0.08)",   border:"rgba(37,99,235,0.18)",   tagBg:"rgba(37,99,235,0.08)",   tagColor:"#2563eb" },
  amber:  { acc:"#d97706", rgb:"217,119,6",   bg:"rgba(217,119,6,0.08)",   border:"rgba(217,119,6,0.18)",   tagBg:"rgba(217,119,6,0.08)",   tagColor:"#d97706" },
  violet: { acc:"#7c3aed", rgb:"124,58,237",  bg:"rgba(124,58,237,0.08)",  border:"rgba(124,58,237,0.18)",  tagBg:"rgba(124,58,237,0.08)",  tagColor:"#7c3aed" },
  slate:  { acc:"#334155", rgb:"51,65,85",    bg:"rgba(51,65,85,0.08)",    border:"rgba(51,65,85,0.18)",    tagBg:"rgba(51,65,85,0.08)",    tagColor:"#334155" },
  teal:   { acc:"#0d9488", rgb:"13,148,136",  bg:"rgba(13,148,136,0.08)",  border:"rgba(13,148,136,0.18)",  tagBg:"rgba(13,148,136,0.08)",  tagColor:"#0d9488" },
};

/* ── Solutions data ── */
const solutions = [
  {
    id: "cliniflow-ai",
    path: "/cliniflow-ai",
    palette: "green",
    tag: "Saúde",
    title: "CliniFlow AI",
    desc: "Reduz faltas em até 50%, preenche horários vagos automaticamente e traz pacientes de volta — sem esforço da equipe.",
    icon: <CalendarCheck size={22} />,
    metrics: [{ val: "↓50%", lbl: "Menos faltas" }, { val: "R$9k+", lbl: "Recuperados/mês" }],
    featured: true,
    nicho: "Clínicas & Saúde",
  },
  {
    id: "ai-crm",
    path: "/ai-crm",
    palette: "blue",
    tag: "Vendas",
    title: "AI CRM",
    desc: "Automatize o acompanhamento de leads, classifique oportunidades e aumente sua taxa de conversão com inteligência.",
    icon: <Users size={22} />,
    metrics: [{ val: "+38%", lbl: "Conversão" }, { val: "3×", lbl: "Mais follow-up" }],
    featured: false,
    nicho: "Vendas & CRM",
  },
  {
    id: "trainify",
    path: "/trainify",
    palette: "amber",
    tag: "Fitness",
    title: "Trainify AI",
    desc: "Crie treinos e planos alimentares 100% personalizados para cada aluno em segundos, com base no perfil e objetivo.",
    icon: <Activity size={22} />,
    metrics: [{ val: "10s", lbl: "Por plano" }, { val: "+4×", lbl: "Retenção" }],
    featured: false,
    nicho: "Fitness & Personal",
  },
  {
    id: "contract-ai",
    path: "/contract-ai",
    palette: "slate",
    tag: "Jurídico",
    title: "Contract AI",
    desc: "Gere, revise e analise contratos com velocidade e precisão. Reduza riscos e tempo de fechamento em até 80%.",
    icon: <FileText size={22} />,
    metrics: [{ val: "↓80%", lbl: "Tempo de geração" }, { val: "99%", lbl: "Precisão" }],
    featured: false,
    nicho: "Jurídico & Docs",
  },
  {
    id: "reply-ai",
    path: "/reply-ai",
    palette: "violet",
    tag: "Atendimento",
    title: "Reply AI",
    desc: "Responda clientes no WhatsApp, Instagram e e-mail 24/7 com uma IA que entende contexto e fecha negócios.",
    icon: <MessageSquare size={22} />,
    metrics: [{ val: "24/7", lbl: "Disponível" }, { val: "↓70%", lbl: "Tempo resposta" }],
    featured: false,
    nicho: "Atendimento",
  },
  {
    id: "content-ai",
    path: "/content-ai",
    palette: "teal",
    tag: "Marketing",
    title: "Content AI",
    desc: "Gere posts, e-mails, anúncios e roteiros de vídeo alinhados ao tom da marca — em volume e consistência.",
    icon: <Sparkles size={22} />,
    metrics: [{ val: "100×", lbl: "Mais conteúdo" }, { val: "+55%", lbl: "Engajamento" }],
    featured: false,
    nicho: "Marketing",
  },
];

const categories = ["Todos", "Saúde", "Vendas", "Fitness", "Jurídico", "Atendimento", "Marketing"];

const tickerItems = [
  "Reduza faltas na clínica", "Feche mais contratos", "Automatize atendimento",
  "Gere treinos personalizados", "Produza conteúdo em escala", "Converta mais leads",
  "Responda 24/7 no WhatsApp", "Analise contratos com precisão",
];

/* ── Mini visual for featured card ── */
function FeaturedVisual() {
  const [pulse, setPulse] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setPulse(p => (p + 1) % 3), 900);
    return () => clearInterval(t);
  }, []);
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:8, width:"100%" }}>
      {[
        { label:"Taxa de no-show", before:"31%", after:"11%", color:"#16a34a" },
        { label:"Agenda preenchida", before:"68%", after:"96%", color:"#059669" },
        { label:"Pacientes reativados", before:"4/mês", after:"27/mês", color:"#0d9488" },
      ].map((row, i) => (
        <div key={i} style={{ background:"white", border:"1px solid rgba(30,120,60,0.12)", borderRadius:10, padding:"10px 14px" }}>
          <div style={{ fontSize:"0.65rem", fontWeight:700, color:"#7aa886", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:5 }}>{row.label}</div>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ fontSize:"0.78rem", color:"#aaa", textDecoration:"line-through" }}>{row.before}</span>
            <MoveRight size={11} color="#ccc" />
            <span style={{ fontSize:"0.88rem", fontWeight:700, color:row.color }}>{row.after}</span>
            {pulse === i && <span style={{ width:6, height:6, borderRadius:"50%", background:row.color, display:"inline-block", animation:"up 0.3s ease" }} />}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function HomeCatalog() {
  const [activeFilter, setActiveFilter] = useState("Todos");
  const [formData, setFormData] = useState({ nome:"", empresa:"", email:"", solucao:"", msg:"" });
  const [submitted, setSubmitted] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const revRefs = useRef<(HTMLElement | null)[]>([]);

  const filtered = activeFilter === "Todos"
    ? solutions
    : solutions.filter(s => s.tag === activeFilter);

  useEffect(() => {
    const obs = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) (e.target as HTMLElement).classList.add("vis"); }),
      { threshold: 0.1 }
    );
    revRefs.current.forEach(el => el && obs.observe(el));
    return () => obs.disconnect();
  }, []);

  const r = (el: HTMLElement | null, i: number) => { revRefs.current[i] = el; };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />

      {/* Aurora */}
      <div className="aurora">
        <div className="ab ab1" /><div className="ab ab2" />
        <div className="ab ab3" /><div className="ab ab4" />
      </div>

      {/* ── NAV ── */}
      <nav className="nav-wrap">
        <div className="nav-pill">
          <a href="#hero" className="nav-logo">
            <div className="nav-logo-icon"><Zap size={15} color="white" /></div>
            AI<span style={{ color:"var(--acc)" }}>Solutions</span>
          </a>
          <div className="nav-links">
            <a href="#solucoes">Soluções</a>
            <a href="#como">Como funciona</a>
            <a href="#nichos">Nichos</a>
          </div>
          <a href="#contato" className="nav-cta">Falar com especialista →</a>
          <button className="nav-mob" onClick={() => setMobileMenu(!mobileMenu)}>
            {mobileMenu ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {mobileMenu && (
        <div style={{ position:"fixed", top:70, left:16, right:16, background:"white", borderRadius:16, border:"1px solid var(--bdr2)", padding:16, zIndex:99, boxShadow:"0 8px 32px rgba(0,0,0,0.08)" }}>
          {["#solucoes","#como","#nichos","#contato"].map(href => (
            <a key={href} href={href} onClick={() => setMobileMenu(false)} style={{ display:"block", padding:"10px 12px", fontSize:"0.9rem", fontWeight:500, color:"var(--text)", textDecoration:"none", borderRadius:8 }}>
              {href.slice(1).charAt(0).toUpperCase() + href.slice(2)}
            </a>
          ))}
        </div>
      )}

      {/* ── HERO ── */}
      <section className="hero-section" id="hero">
        <div className="w">
          <div className="ep a0"><Layers size={11} /> Portfólio de Soluções com IA</div>
          <h1 className="hero-h1 a1">
            IA que resolve<br /><em>problemas reais</em><br />de negócio
          </h1>
          <p className="hero-p a2">
            Soluções prontas para automatizar, converter e crescer — cada uma construída para um problema específico, com resultado mensurável.
          </p>
          <div className="ctas a3">
            <a href="#solucoes" className="bp">Explorar soluções <ArrowRight size={15} /></a>
            <a href="#contato" className="bo">Falar com especialista</a>
          </div>

          {/* Stats strip */}
          <div className="stats-strip a4">
            {[
              { num:"6+",    lbl:"Soluções disponíveis" },
              { num:"300+",  lbl:"Empresas usando" },
              { num:"R$2M+", lbl:"Receita gerada/mês" },
              { num:"98%",   lbl:"Satisfação dos clientes" },
            ].map((s, i) => (
              <div key={i} className="stat-item">
                <div className="stat-num">{s.num}</div>
                <div className="stat-lbl">{s.lbl}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TICKER ── */}
      <div className="ticker-wrap">
        <div className="ticker-inner">
          {[...tickerItems, ...tickerItems].map((t, i) => (
            <span key={i} className="ticker-item">
              <span className="ticker-dot" />{t}
            </span>
          ))}
        </div>
      </div>

      {/* ── SOLUÇÕES ── */}
      <section id="solucoes">
        <div className="w">
          <div style={{ display:"flex", alignItems:"flex-end", justifyContent:"space-between", flexWrap:"wrap", gap:16, marginBottom:12 }}>
            <div>
              <div className="sh rev" ref={el => r(el, 0)}><Zap size={11} /> Catálogo</div>
              <h2 className="sec-h2 rev" ref={el => r(el, 1)}>Escolha a solução <em>certa</em><br />para o seu negócio</h2>
            </div>
            <p className="sec-sub rev" ref={el => r(el, 2)} style={{ maxWidth:320 }}>Cada produto resolve um problema específico e entrega ROI claro desde o primeiro mês.</p>
          </div>

          {/* Filter */}
          <div className="filter-bar rev" ref={el => r(el, 3)}>
            {categories.map(cat => (
              <button key={cat} className={`ftab${activeFilter === cat ? " active" : ""}`} onClick={() => setActiveFilter(cat)}>
                {cat}
              </button>
            ))}
          </div>

          {/* Cards grid */}
          <div className="sol-grid">
            {filtered.map((sol, i) => {
              const p = palettes[sol.palette];
              const isFeat = sol.featured && activeFilter === "Todos";
              return (
                <Link
                  key={sol.id}
                  to={sol.path}
                  className={`sol-card rev d${(i % 3) + 1}${isFeat ? " featured" : ""}`}
                  ref={el => r(el as HTMLElement | null, 10 + i)}
                  style={{ borderColor: p.border }}
                >
                  <div className="sol-card-top">
                    {/* Icon */}
                    <div className="sol-card-ico-wrap" style={{ background: p.bg }}>
                      <span style={{ color: p.acc }}>{sol.icon}</span>
                    </div>
                    {/* Tag */}
                    <div className="sol-card-tag" style={{ background: p.tagBg, color: p.tagColor, border:`1px solid ${p.border}` }}>
                      {sol.tag}
                    </div>
                    <h3>{sol.title}</h3>
                    <p>{sol.desc}</p>
                  </div>

                  {/* Metrics row */}
                  <div className="sol-card-metrics" style={{ borderColor: p.border }}>
                    {sol.metrics.map((m, mi) => (
                      <div key={mi} className="sol-metric" style={{ borderColor: p.border }}>
                        <div className="sol-metric-val" style={{ color: p.acc }}>{m.val}</div>
                        <div className="sol-metric-lbl">{m.lbl}</div>
                      </div>
                    ))}
                  </div>

                  <div className="sol-card-footer" style={{ borderColor: p.border }}>
                    <span className="sol-cta" style={{ color: p.acc }}>
                      Ver solução <ChevronRight size={14} className="sol-arrow" />
                    </span>
                    <span style={{ fontSize:"0.72rem", color:"var(--subt)" }}>{sol.nicho}</span>
                  </div>

                  {isFeat && (
                    <div className="sol-card-visual">
                      <FeaturedVisual />
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── COMO FUNCIONA ── */}
      <section className="sec-alt" id="como">
        <div className="w">
          <div style={{ textAlign:"center" }}>
            <div className="sh rev" ref={el => r(el, 30)} style={{ justifyContent:"center" }}><Zap size={11} /> Processo</div>
            <h2 className="sec-h2 rev" ref={el => r(el, 31)} style={{ textAlign:"center" }}>Da escolha ao <em>resultado</em> em 3 passos</h2>
            <p className="sec-sub rev" ref={el => r(el, 32)} style={{ textAlign:"center", margin:"0 auto", maxWidth:480 }}>Sem implementação complexa. Sem meses de espera. Você começa a ver retorno rápido.</p>
          </div>
          <div className="steps-g">
            {[
              { n:"01", ico:<Target size={17} color="var(--acc)" />, title:"Escolha a solução certa", desc:"Você identifica o problema mais urgente do seu negócio e selecionamos a solução com maior impacto imediato." },
              { n:"02", ico:<Zap size={17} color="var(--acc)" />, title:"Integração rápida", desc:"Conectamos com suas ferramentas existentes (WhatsApp, Google Calendar, CRM, etc.) em poucos dias, sem complicação." },
              { n:"03", ico:<TrendingUp size={17} color="var(--acc)" />, title:"Resultados mensuráveis", desc:"Acompanhe métricas claras no painel: faturamento recuperado, conversões aumentadas e tempo economizado." },
            ].map((s, i) => (
              <div key={i} className={`g step-card rev d${i + 1}`} ref={el => r(el, 40 + i)}>
                <div className="step-num">{s.n}</div>
                <div style={{ marginBottom:12, color:"var(--acc)" }}>{s.ico}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── NICHOS ── */}
      <section id="nichos">
        <div className="w" style={{ textAlign:"center" }}>
          <div className="sh rev" ref={el => r(el, 50)} style={{ justifyContent:"center" }}><Globe size={11} /> Nichos atendidos</div>
          <h2 className="sec-h2 rev" ref={el => r(el, 51)} style={{ textAlign:"center" }}>Funciona para <em>qualquer</em> segmento</h2>
          <p className="sec-sub rev" ref={el => r(el, 52)} style={{ margin:"0 auto", maxWidth:520, textAlign:"center" }}>Nossas soluções são adaptadas para o vocabulário, desafios e fluxo de cada setor.</p>
          <div className="nicho-row rev" ref={el => r(el, 53)}>
            {[
              { ico:<CalendarCheck size={14} />, label:"Clínicas & Saúde" },
              { ico:<Users size={14} />, label:"Vendas & CRM" },
              { ico:<Activity size={14} />, label:"Fitness & Personal" },
              { ico:<FileText size={14} />, label:"Jurídico" },
              { ico:<MessageSquare size={14} />, label:"Atendimento" },
              { ico:<Sparkles size={14} />, label:"Marketing" },
              { ico:<Globe size={14} />, label:"E-commerce" },
              { ico:<Shield size={14} />, label:"Seguros" },
              { ico:<Star size={14} />, label:"Imóveis" },
              { ico:<Bot size={14} />, label:"SaaS" },
              { ico:<BarChart3 size={14} />, label:"Financeiro" },
              { ico:<TrendingUp size={14} />, label:"Consultoria" },
            ].map((n, i) => (
              <div key={i} className="nicho-pill">
                <span style={{ color:"var(--acc)" }}>{n.ico}</span>
                {n.label}
              </div>
            ))}
          </div>

          {/* Social proof strip */}
          <div className="g rev" ref={el => r(el, 54)} style={{ marginTop:40, display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:0, padding:0, overflow:"hidden" }}>
            {[
              { quote:"Recuperamos R$12k no primeiro mês com o CliniFlow. Nunca pensei que agenda pudesse gerar tanto.", author:"Dr. Felipe R.", role:"Dentista — SP" },
              { quote:"O AI CRM dobrou nossa taxa de fechamento em 6 semanas. Hoje é impossível trabalhar sem ele.", author:"Carla M.", role:"Gestora Comercial — RJ" },
              { quote:"O Contract AI reduziu em 80% o tempo dos nossos contratos. Nossos clientes ficaram impressionados.", author:"Pedro A.", role:"Advogado — MG" },
            ].map((q, i) => (
              <div key={i} style={{ padding:"24px 28px", borderRight: i < 2 ? "1px solid var(--bdr)" : "none" }}>
                <div style={{ display:"flex", gap:2, marginBottom:12 }}>
                  {[...Array(5)].map((_, s) => <Star key={s} size={12} fill="var(--acc)" color="var(--acc)" />)}
                </div>
                <p style={{ fontSize:"0.82rem", color:"var(--muted)", lineHeight:1.6, marginBottom:12 }}>"{q.quote}"</p>
                <div style={{ fontSize:"0.78rem", fontWeight:700 }}>{q.author}</div>
                <div style={{ fontSize:"0.72rem", color:"var(--subt)" }}>{q.role}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── MAIS SOLUÇÕES band ── */}
      <div className="mais-band">
        <div className="w">
          <div className="mais-inner">
            <div className="mais-ico"><Layers size={18} /></div>
            <div className="mais-text">
              <strong>Quer uma solução personalizada para o seu setor?</strong>
              <span>Desenvolvemos produtos sob medida para nichos específicos. Fale com nossa equipe.</span>
            </div>
            <a href="#contato" className="mais-pill"><ExternalLink size={13} /> Solicitar proposta</a>
          </div>
        </div>
      </div>

      {/* ── CONTATO ── */}
      <section id="contato" className="sec-alt">
        <div className="w">
          <div className="contato-g">
            <div>
              <div className="sh rev" ref={el => r(el, 60)}><MessageSquare size={11} /> Fale com a gente</div>
              <h2 className="sec-h2 rev" ref={el => r(el, 61)}>Qual problema você<br />quer <em>resolver</em> primeiro?</h2>
              <p className="sec-sub rev" ref={el => r(el, 62)} style={{ marginBottom:28 }}>
                Nossa equipe entende o seu setor e indica a solução com maior ROI para o seu momento atual.
              </p>
              <div className="canal-list">
                {[
                  { cls:"wpp",  ico:<MessageSquare size={16} />, label:"WhatsApp",  detail:"Resposta em até 2h",       href:"https://wa.me/5541999999999" },
                  { cls:"mail", ico:<Mail size={16} />,          label:"E-mail",    detail:"contato@aisolutions.com.br", href:"mailto:contato@aisolutions.com.br" },
                  { cls:"tel",  ico:<Phone size={16} />,         label:"Telefone",  detail:"Seg–Sex, 9h–18h",           href:"tel:+5541999999999" },
                ].map((c, i) => (
                  <a key={i} href={c.href} className="canal rev" ref={el => r(el, 63 + i)}>
                    <div className={`canal-ico ${c.cls}`}>{c.ico}</div>
                    <div className="canal-info"><strong>{c.label}</strong><span>{c.detail}</span></div>
                    <ChevronRight size={15} className="canal-arrow" />
                  </a>
                ))}
              </div>
            </div>

            <div className="form-card rev" ref={el => r(el, 70)}>
              {submitted ? (
                <div className="success-state">
                  <div className="success-ico"><CheckCircle2 size={26} /></div>
                  <h3 style={{ fontWeight:700, marginBottom:6 }}>Mensagem enviada!</h3>
                  <p style={{ fontSize:"0.85rem", color:"var(--muted)" }}>Nossa equipe entrará em contato em breve para indicar a melhor solução.</p>
                </div>
              ) : (
                <form onSubmit={e => { e.preventDefault(); setSubmitted(true); }}>
                  <div className="form-title">Enviar mensagem</div>
                  <div className="form-row">
                    <div className="form-field">
                      <label>Nome</label>
                      <input required placeholder="Seu nome" value={formData.nome} onChange={e => setFormData(p => ({ ...p, nome: e.target.value }))} />
                    </div>
                    <div className="form-field">
                      <label>Empresa</label>
                      <input placeholder="Sua empresa" value={formData.empresa} onChange={e => setFormData(p => ({ ...p, empresa: e.target.value }))} />
                    </div>
                  </div>
                  <div className="form-field">
                    <label>E-mail</label>
                    <input required type="email" placeholder="seu@email.com" value={formData.email} onChange={e => setFormData(p => ({ ...p, email: e.target.value }))} />
                  </div>
                  <div className="form-field">
                    <label>Qual solução te interessa?</label>
                    <select value={formData.solucao} onChange={e => setFormData(p => ({ ...p, solucao: e.target.value }))}>
                      <option value="">Selecione uma solução...</option>
                      {solutions.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
                      <option value="custom">Solução personalizada</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label>Qual problema quer resolver?</label>
                    <textarea rows={3} placeholder="Conte brevemente o desafio do seu negócio..." value={formData.msg} onChange={e => setFormData(p => ({ ...p, msg: e.target.value }))} />
                  </div>
                  <button type="submit" className="form-btn">
                    Enviar mensagem <ArrowRight size={15} />
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="footer">
        <div className="w">
          <div className="footer-inner">
            <a href="#hero" className="footer-logo">
              <div className="nav-logo-icon" style={{ width:24, height:24, borderRadius:6 }}>
                <Zap size={12} color="white" />
              </div>
              AI<span style={{ color:"var(--acc)" }}>Solutions</span>
            </a>
            <span style={{ fontSize:"0.78rem", color:"var(--subt)" }}>© {new Date().getFullYear()} AI Solutions. Todos os direitos reservados.</span>
            <div className="footer-links">
              <a href="#"><ChevronRight size={11} />Privacidade</a>
              <a href="#"><ChevronRight size={11} />Termos de uso</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}