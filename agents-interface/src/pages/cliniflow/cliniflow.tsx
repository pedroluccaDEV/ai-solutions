import { useState, useEffect, useRef } from "react";
import {
  Zap, Activity, MessageSquare, Mail, Phone, CheckCircle2,
  XCircle, ChevronRight, Layers, ExternalLink, HeartPulse,
  Sparkles, GraduationCap, Building2, Users, TrendingUp,
  CalendarCheck, BarChart3, RefreshCw, Target, Clock,
  ArrowRight, Shield, Star, Menu, X
} from "lucide-react";

/* ─────────────────────────────────────────────
   TOKENS — Paleta 1: Verde Esmeralda
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

  /* ─── Aurora ─── */
  .aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
  .ab { position: absolute; border-radius: 50%; animation: af linear infinite; will-change: transform; }
  .ab1 { width: 820px; height: 520px; top: -180px;  left: -160px;  background: rgba(74,222,128,0.13);  filter: blur(72px); animation-duration: 26s; }
  .ab2 { width: 600px; height: 460px; top:  50px;  right: -100px; background: rgba(16,185,129,0.10);  filter: blur(80px); animation-duration: 33s; animation-delay: -10s; }
  .ab3 { width: 680px; height: 400px; top:  260px; left:   25%;   background: rgba(20,184,166,0.09);  filter: blur(90px); animation-duration: 21s; animation-delay:  -6s; }
  .ab4 { width: 480px; height: 360px; bottom:160px; right: 12%;   background: rgba(74,222,128,0.08);  filter: blur(70px); animation-duration: 29s; animation-delay: -16s; }
  @keyframes af {
    0%   { transform: translate(0,0) scale(1); }
    25%  { transform: translate(32px,-44px) scale(1.06); }
    50%  { transform: translate(58px,-6px) scale(0.94); }
    75%  { transform: translate(18px,30px) scale(1.05); }
    100% { transform: translate(0,0) scale(1); }
  }

  /* ─── Layout ─── */
  .w { max-width: 1060px; margin: 0 auto; padding: 0 28px; }
  section { padding: 88px 0; position: relative; z-index: 1; }
  .sec-alt { background: var(--off); }

  /* ─── Nav ─── */
  .nav-wrap { position: fixed; top: 14px; left: 0; right: 0; z-index: 100; display: flex; justify-content: center; padding: 0 28px; }
  .nav-pill {
    max-width: 1060px; width: 100%;
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(28px);
    border: 1px solid var(--bdr2);
    border-radius: 18px;
    padding: 10px 20px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .nav-logo { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.95rem; color: var(--text); text-decoration: none; }
  .nav-logo-icon { width: 30px; height: 30px; background: var(--acc); border-radius: 8px; display: grid; place-items: center; }
  .nav-links { display: flex; align-items: center; gap: 4px; }
  .nav-links a { font-size: 0.83rem; font-weight: 500; color: var(--muted); padding: 6px 12px; border-radius: 8px; text-decoration: none; transition: all .18s; }
  .nav-links a:hover { background: var(--surf); color: var(--text); }
  .nav-cta { background: var(--acc); color: white; font-size: 0.82rem; font-weight: 600; padding: 8px 16px; border-radius: 9px; text-decoration: none; transition: all .18s; white-space: nowrap; }
  .nav-cta:hover { background: var(--acc-dark); transform: translateY(-1px); }
  .nav-mob { display: none; background: none; border: none; cursor: pointer; color: var(--text); }

  /* ─── Hero ─── */
  .hero-section { padding: 140px 0 88px; }
  .hero-g { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 56px; align-items: center; }
  .ep {
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--acc); background: rgba(22,163,74,0.08); border: 1px solid rgba(22,163,74,0.18);
    padding: 5px 13px; border-radius: 100px; margin-bottom: 20px;
  }
  .hero-h1 { font-size: clamp(2.1rem, 4.4vw, 3.2rem); font-weight: 700; line-height: 1.18; letter-spacing: -0.02em; margin-bottom: 18px; }
  .hero-h1 em { font-style: italic; font-family: var(--serif); color: var(--acc); }
  .hero-p { font-size: 1.08rem; color: var(--muted); line-height: 1.65; margin-bottom: 32px; max-width: 480px; }
  .ctas { display: flex; gap: 12px; flex-wrap: wrap; }
  .bp {
    background: var(--acc); color: white; padding: 13px 24px; border-radius: 11px;
    font-size: 0.92rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
    transition: all .22s; border: none; cursor: pointer;
  }
  .bp:hover { background: var(--acc-dark); transform: translateY(-2px); box-shadow: 0 10px 26px rgba(22,163,74,0.28); }
  .bo {
    background: transparent; color: var(--text); border: 1px solid var(--bdr2);
    padding: 13px 24px; border-radius: 11px; font-size: 0.92rem; font-weight: 500;
    text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all .22s; cursor: pointer;
  }
  .bo:hover { background: var(--surf); transform: translateY(-1px); }

  /* Hero visual */
  .hero-visual-wrap { position: relative; display: flex; align-items: center; justify-content: center; }
  .hero-glow {
    position: absolute; width: 380px; height: 380px; border-radius: 50%;
    background: radial-gradient(circle, rgba(22,163,74,0.22) 0%, transparent 70%);
    top: 50%; left: 50%; transform: translate(-50%,-50%);
    animation: glowPulse 4s ease-in-out infinite;
  }
  @keyframes glowPulse {
    0%, 100% { opacity: 0.7; transform: translate(-50%,-50%) scale(1); }
    50%       { opacity: 1;   transform: translate(-50%,-50%) scale(1.15); }
  }
  .hero-visual {
    position: relative; z-index: 1;
    animation: heroFloat 6s ease-in-out infinite;
    transform-style: preserve-3d;
  }
  @keyframes heroFloat {
    0%, 100% { transform: rotateY(-8deg) rotateX(3deg) translateY(0px); }
    50%       { transform: rotateY(-3deg) rotateX(1deg) translateY(-12px); }
  }
  .phone-mock {
    width: 200px; background: white; border-radius: 28px;
    border: 2px solid var(--bdr2); box-shadow: 0 24px 60px rgba(22,163,74,0.18), 0 4px 16px rgba(0,0,0,0.08);
    overflow: hidden;
  }
  .phone-top { background: var(--acc); padding: 14px 16px 10px; }
  .phone-top-label { font-size: 0.62rem; color: rgba(255,255,255,0.7); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
  .phone-top-name { font-size: 0.82rem; color: white; font-weight: 700; margin-top: 2px; }
  .phone-body { padding: 12px; display: flex; flex-direction: column; gap: 8px; }
  .msg { max-width: 85%; padding: 8px 11px; border-radius: 12px; font-size: 0.72rem; line-height: 1.45; }
  .msg-in  { background: var(--surf); color: var(--text); align-self: flex-start; border-bottom-left-radius: 4px; }
  .msg-out { background: var(--acc); color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
  .msg-time { font-size: 0.6rem; color: var(--subt); margin-top: 2px; }

  /* Dashboard card beside phone */
  .dash-card {
    position: absolute; right: -30px; top: 20px;
    background: white; border: 1px solid var(--bdr2); border-radius: 14px;
    padding: 12px 14px; box-shadow: 0 8px 24px rgba(22,163,74,0.12);
    min-width: 130px;
  }
  .dash-label { font-size: 0.62rem; color: var(--subt); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
  .dash-value { font-size: 1.4rem; font-weight: 700; color: var(--acc); line-height: 1.2; margin-top: 2px; }
  .dash-sub { font-size: 0.65rem; color: var(--muted); margin-top: 1px; }

  .dash-card2 {
    position: absolute; left: -20px; bottom: 30px;
    background: white; border: 1px solid var(--bdr2); border-radius: 14px;
    padding: 12px 14px; box-shadow: 0 8px 24px rgba(22,163,74,0.12);
    min-width: 120px;
  }

  /* Typing indicator */
  .typing { display: flex; gap: 3px; align-items: center; padding: 8px 11px; background: var(--surf); border-radius: 12px; width: fit-content; }
  .dot { width: 5px; height: 5px; border-radius: 50%; background: var(--subt); animation: blink 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

  /* ─── Metrics ─── */
  .met-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 2px; }
  .met-item { text-align: center; padding: 36px 24px; }
  .met-num { font-size: clamp(2rem, 4vw, 2.8rem); font-weight: 700; color: var(--acc); line-height: 1; }
  .met-num em { font-style: italic; font-family: var(--serif); }
  .met-label { font-size: 0.83rem; color: var(--muted); margin-top: 8px; line-height: 1.4; }

  /* ─── Section header ─── */
  .sh { display: inline-flex; align-items: center; gap: 6px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; color: var(--acc); margin-bottom: 13px; }
  .sec-h2 { font-size: clamp(1.65rem, 3.4vw, 2.45rem); font-weight: 700; line-height: 1.22; letter-spacing: -0.015em; margin-bottom: 16px; }
  .sec-h2 em { font-style: italic; font-family: var(--serif); color: var(--acc); }
  .sec-sub { font-size: 1rem; color: var(--muted); line-height: 1.65; max-width: 520px; }

  /* Glass card */
  .g {
    background: rgba(255,255,255,0.72); backdrop-filter: blur(22px);
    border: 1px solid var(--bdr2); border-radius: 18px;
    box-shadow: 0 2px 16px rgba(22,163,74,0.04);
    transition: all 0.22s; padding: 24px;
  }
  .g:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(22,163,74,0.12); border-color: rgba(22,163,74,0.28); }

  /* ─── Sobre ─── */
  .sobre-g { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }
  .sobre-points { display: flex; flex-direction: column; gap: 16px; margin-top: 28px; }
  .sobre-pt { display: flex; gap: 12px; align-items: flex-start; }
  .sobre-pt-icon { width: 34px; height: 34px; border-radius: 9px; background: rgba(22,163,74,0.1); display: grid; place-items: center; flex-shrink: 0; margin-top: 2px; }
  .sobre-pt h4 { font-size: 0.88rem; font-weight: 700; margin-bottom: 3px; }
  .sobre-pt p { font-size: 0.83rem; color: var(--muted); }

  /* Funil visual */
  .funil { background: white; border: 1px solid var(--bdr2); border-radius: 20px; padding: 24px; box-shadow: 0 4px 20px rgba(22,163,74,0.08); }
  .funil-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--acc); margin-bottom: 20px; }
  .funil-step { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 11px; margin-bottom: 8px; }
  .funil-step:nth-child(2) { background: rgba(22,163,74,0.06); }
  .funil-step:nth-child(3) { background: rgba(22,163,74,0.10); }
  .funil-step:nth-child(4) { background: rgba(22,163,74,0.16); }
  .funil-step:nth-child(5) { background: rgba(22,163,74,0.22); }
  .funil-ico { width: 32px; height: 32px; border-radius: 8px; background: white; border: 1px solid var(--bdr2); display: grid; place-items: center; flex-shrink: 0; }
  .funil-lbl { font-size: 0.8rem; font-weight: 600; }
  .funil-val { font-size: 0.72rem; color: var(--muted); }
  .funil-badge { margin-left: auto; font-size: 0.68rem; font-weight: 700; color: var(--acc); background: rgba(22,163,74,0.1); padding: 3px 8px; border-radius: 100px; }

  /* ─── Como funciona ─── */
  .steps-g { display: grid; grid-template-columns: repeat(3,1fr); gap: 18px; margin-top: 52px; position: relative; }
  .steps-g::before {
    content: ''; position: absolute; top: 28px; left: calc(16.66% + 9px); right: calc(16.66% + 9px);
    height: 1px; background: linear-gradient(90deg, var(--acc), var(--acc3));
    opacity: 0.3;
  }
  .step-card { padding: 28px 22px; }
  .step-num { width: 40px; height: 40px; background: rgba(22,163,74,0.1); border-radius: 10px; display: grid; place-items: center; font-size: 0.78rem; font-weight: 800; color: var(--acc); margin-bottom: 18px; }
  .step-card h3 { font-size: 0.92rem; font-weight: 700; margin-bottom: 8px; }
  .step-card p { font-size: 0.83rem; color: var(--muted); line-height: 1.55; }
  .step-icon { margin-bottom: 12px; color: var(--acc); }

  /* ─── Antes × Depois ─── */
  .ad-g { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 52px; }
  .ad-card { border-radius: 18px; padding: 28px; }
  .ad-antes { background: rgba(220,38,38,0.04); border: 1px solid rgba(220,38,38,0.15); }
  .ad-depois { background: rgba(22,163,74,0.04); border: 1px solid rgba(22,163,74,0.18); }
  .ad-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; padding: 4px 12px; border-radius: 100px; margin-bottom: 20px; }
  .ad-antes .ad-badge { color: var(--red); background: rgba(220,38,38,0.08); }
  .ad-depois .ad-badge { color: var(--acc); background: rgba(22,163,74,0.08); }
  .ad-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; font-size: 0.85rem; line-height: 1.45; }
  .ad-antes .ad-item { color: #5c1a1a; }
  .ad-depois .ad-item { color: #0f2d17; }

  /* ─── Para quem ─── */
  .quem-g { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-top: 52px; }
  .quem-card { padding: 22px; }
  .quem-ico { width: 40px; height: 40px; background: rgba(22,163,74,0.08); border-radius: 10px; display: grid; place-items: center; color: var(--acc); margin-bottom: 14px; }
  .quem-card h4 { font-size: 0.88rem; font-weight: 700; margin-bottom: 6px; }
  .quem-card p { font-size: 0.8rem; color: var(--muted); line-height: 1.5; }

  /* ─── Mais Soluções ─── */
  .mais-band {
    background: rgba(22,163,74,0.04); border-top: 1px solid rgba(22,163,74,0.1); border-bottom: 1px solid rgba(22,163,74,0.1);
    padding: 28px 0; position: relative; z-index: 1;
  }
  .mais-inner { display: flex; align-items: center; gap: 16px; }
  .mais-ico { width: 40px; height: 40px; background: rgba(22,163,74,0.1); border-radius: 10px; display: grid; place-items: center; color: var(--acc); flex-shrink: 0; }
  .mais-text { flex: 1; }
  .mais-text strong { font-size: 0.9rem; font-weight: 700; display: block; margin-bottom: 2px; }
  .mais-text span { font-size: 0.82rem; color: var(--muted); }
  .mais-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600; color: var(--acc); background: white; border: 1px solid var(--bdr2); padding: 8px 16px; border-radius: 100px; text-decoration: none; transition: all .18s; white-space: nowrap; }
  .mais-pill:hover { background: var(--surf); transform: translateY(-1px); }

  /* ─── Contato ─── */
  .contato-g { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
  .canal-list { display: flex; flex-direction: column; gap: 12px; }
  .canal { display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: 14px; border: 1px solid var(--bdr2); background: white; text-decoration: none; transition: all .22s; cursor: pointer; }
  .canal:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(22,163,74,0.1); border-color: rgba(22,163,74,0.25); }
  .canal-ico { width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center; flex-shrink: 0; }
  .canal-ico.wpp  { background: rgba(22,163,74,0.1); color: var(--acc); }
  .canal-ico.mail { background: rgba(5,150,105,0.1); color: var(--acc2); }
  .canal-ico.tel  { background: rgba(13,148,136,0.1); color: var(--acc3); }
  .canal-info strong { font-size: 0.88rem; font-weight: 700; display: block; }
  .canal-info span { font-size: 0.78rem; color: var(--muted); }
  .canal-arrow { margin-left: auto; color: var(--subt); }

  /* Form */
  .form-card { background: white; border: 1px solid var(--bdr2); border-radius: 20px; padding: 28px; }
  .form-title { font-size: 1rem; font-weight: 700; margin-bottom: 20px; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
  .form-field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; }
  .form-field label { font-size: 0.78rem; font-weight: 600; color: var(--muted); }
  .form-field input, .form-field textarea {
    padding: 10px 13px; border-radius: 9px; border: 1px solid var(--bdr2);
    font-family: var(--font); font-size: 0.85rem; color: var(--text); background: var(--off);
    transition: border .18s; outline: none; resize: none;
  }
  .form-field input:focus, .form-field textarea:focus { border-color: rgba(22,163,74,0.4); background: white; }
  .form-btn {
    width: 100%; padding: 13px; border-radius: 11px; border: none; cursor: pointer;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    color: white; font-weight: 600; font-size: 0.92rem; font-family: var(--font);
    display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: all .22s;
  }
  .form-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(22,163,74,0.28); }
  .success-state { text-align: center; padding: 32px 0; }
  .success-ico { width: 56px; height: 56px; background: rgba(22,163,74,0.1); border-radius: 50%; display: grid; place-items: center; color: var(--acc); margin: 0 auto 16px; }
  .success-state h3 { font-size: 1rem; font-weight: 700; margin-bottom: 6px; }
  .success-state p { font-size: 0.85rem; color: var(--muted); }

  /* ─── Footer ─── */
  .footer { border-top: 1px solid var(--bdr); padding: 32px 0; position: relative; z-index: 1; }
  .footer-inner { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
  .footer-logo { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.9rem; text-decoration: none; color: var(--text); }
  .footer-copy { font-size: 0.78rem; color: var(--subt); }
  .footer-links { display: flex; gap: 20px; }
  .footer-links a { font-size: 0.78rem; color: var(--subt); text-decoration: none; display: flex; align-items: center; gap: 4px; transition: color .18s; }
  .footer-links a:hover { color: var(--acc); }

  /* ─── Scroll reveal ─── */
  .rev { opacity: 0; transform: translateY(14px); transition: opacity .5s ease, transform .5s ease; }
  .rev.vis { opacity: 1; transform: translateY(0); }
  .rev.d1 { transition-delay: 0.0s; }
  .rev.d2 { transition-delay: 0.1s; }
  .rev.d3 { transition-delay: 0.2s; }

  /* ─── Hero stagger ─── */
  @keyframes up { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
  .ep   { animation: up 0.6s 0.0s ease both; }
  .h1a  { animation: up 0.6s 0.1s ease both; }
  .hpa  { animation: up 0.6s 0.2s ease both; }
  .ctaa { animation: up 0.6s 0.3s ease both; }
  .visa { animation: up 0.6s 0.4s ease both; }

  /* ─── Responsive ─── */
  @media (max-width: 768px) {
    .hero-g, .sobre-g, .contato-g, .ad-g { grid-template-columns: 1fr; }
    .steps-g, .quem-g { grid-template-columns: 1fr; }
    .met-grid { grid-template-columns: 1fr 1fr; }
    .hero-visual-wrap { display: none; }
    .steps-g::before { display: none; }
    .nav-links { display: none; }
    .nav-mob { display: block; }
    section { padding: 60px 0; }
    .hero-section { padding: 110px 0 60px; }
    .form-row { grid-template-columns: 1fr; }
    .footer-inner { flex-direction: column; text-align: center; }
    .footer-links { justify-content: center; }
    .mais-inner { flex-wrap: wrap; }
  }
`;

/* ─── Animated Chat Messages ─── */
const messages = [
  { type: "in",  text: "Olá! Você tem consulta amanhã às 14h 😊", time: "09:12" },
  { type: "out", text: "Ah é! Posso confirmar? Estava com medo de esquecer", time: "09:14" },
  { type: "in",  text: "Confirmado! ✅ Já atualizamos sua agenda.", time: "09:14" },
  { type: "in",  text: "Você costuma faltar às segundas. Deseja remarcar para quinta?", time: "09:15" },
];

export default function CliniFlowAI() {
  const [visibleMsgs, setVisibleMsgs] = useState(1);
  const [formData, setFormData] = useState({ nome: "", empresa: "", email: "", msg: "" });
  const [submitted, setSubmitted] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const revRefs = useRef<(HTMLElement | null)[]>([]);

  // Animate chat messages
  useEffect(() => {
    if (visibleMsgs < messages.length) {
      const t = setTimeout(() => setVisibleMsgs(v => v + 1), 1600);
      return () => clearTimeout(t);
    } else {
      const t = setTimeout(() => setVisibleMsgs(1), 3000);
      return () => clearTimeout(t);
    }
  }, [visibleMsgs]);

  // Scroll reveal
  useEffect(() => {
    const obs = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) (e.target as HTMLElement).classList.add("vis"); }),
      { threshold: 0.1 }
    );
    revRefs.current.forEach(el => el && obs.observe(el));
    return () => obs.disconnect();
  }, []);

  const addRev = (el: HTMLElement | null, i: number) => { revRefs.current[i] = el; };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />

      {/* Aurora */}
      <div className="aurora">
        <div className="ab ab1" />
        <div className="ab ab2" />
        <div className="ab ab3" />
        <div className="ab ab4" />
      </div>

      {/* Nav */}
      <nav className="nav-wrap">
        <div className="nav-pill">
          <a href="#hero" className="nav-logo">
            <div className="nav-logo-icon">
              <CalendarCheck size={15} color="white" />
            </div>
            CliniFlow<span style={{ color: "var(--acc)" }}>AI</span>
          </a>
          <div className="nav-links">
            <a href="#sobre">Sobre</a>
            <a href="#como">Como funciona</a>
            <a href="#quem">Para quem</a>
          </div>
          <a href="#contato" className="nav-cta">Falar com especialista →</a>
          <button className="nav-mob" onClick={() => setMobileMenu(!mobileMenu)}>
            {mobileMenu ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileMenu && (
        <div style={{ position: "fixed", top: 70, left: 16, right: 16, background: "white", borderRadius: 16, border: "1px solid var(--bdr2)", padding: 16, zIndex: 99, boxShadow: "0 8px 32px rgba(0,0,0,0.08)" }}>
          {["#sobre", "#como", "#quem", "#contato"].map(href => (
            <a key={href} href={href} onClick={() => setMobileMenu(false)}
              style={{ display: "block", padding: "10px 12px", fontSize: "0.9rem", fontWeight: 500, color: "var(--text)", textDecoration: "none", borderRadius: 8 }}>
              {href.replace("#", "").charAt(0).toUpperCase() + href.slice(2)}
            </a>
          ))}
        </div>
      )}

      {/* ─── HERO ─── */}
      <section className="hero-section" id="hero">
        <div className="w">
          <div className="hero-g">
            <div>
              <div className="ep">
                <Activity size={11} />
                IA Anti No-Show para Clínicas
              </div>
              <h1 className="hero-h1 h1a">
                Sua agenda cheia.<br />
                Seu <em>faturamento</em><br />
                sem buracos.
              </h1>
              <p className="hero-p hpa">
                Reduza faltas em até 50%, preencha horários vagos automaticamente e traga pacientes de volta — sem esforço da sua equipe.
              </p>
              <div className="ctas ctaa">
                <a href="#contato" className="bp">
                  Ver demonstração <ArrowRight size={15} />
                </a>
                <a href="#como" className="bo">
                  Como funciona
                </a>
              </div>
            </div>

            <div className="hero-visual-wrap visa">
              <div className="hero-glow" />
              <div className="hero-visual" style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                {/* Phone mockup */}
                <div className="phone-mock">
                  <div className="phone-top">
                    <div className="phone-top-label">CliniFlow AI</div>
                    <div className="phone-top-name">📱 WhatsApp</div>
                  </div>
                  <div className="phone-body">
                    {messages.slice(0, visibleMsgs).map((m, i) => (
                      <div key={i}>
                        <div className={`msg msg-${m.type}`}>{m.text}</div>
                        <div className="msg-time" style={{ textAlign: m.type === "out" ? "right" : "left" }}>{m.time}</div>
                      </div>
                    ))}
                    {visibleMsgs < messages.length && (
                      <div className="typing">
                        <div className="dot" /><div className="dot" /><div className="dot" />
                      </div>
                    )}
                  </div>
                </div>

                {/* Dashboard cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                  <div className="dash-card" style={{ position: "relative", right: "auto", top: "auto" }}>
                    <div className="dash-label">Faltas evitadas</div>
                    <div className="dash-value">↓ 47%</div>
                    <div className="dash-sub">últimos 30 dias</div>
                  </div>
                  <div className="dash-card" style={{ position: "relative", left: "auto", bottom: "auto" }}>
                    <div className="dash-label">Receita recuperada</div>
                    <div className="dash-value">R$ 9.2k</div>
                    <div className="dash-sub">este mês</div>
                  </div>
                  <div className="dash-card" style={{ position: "relative" }}>
                    <div className="dash-label">Pacientes reativados</div>
                    <div className="dash-value">38</div>
                    <div className="dash-sub">retornaram</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── MÉTRICAS ─── */}
      <div style={{ position: "relative", zIndex: 1, borderTop: "1px solid var(--bdr)", borderBottom: "1px solid var(--bdr)", background: "rgba(255,255,255,0.6)" }}>
        <div className="w">
          <div className="met-grid">
            {[
              { num: "↓50", suf: "%", label: "Redução de faltas em clínicas parceiras" },
              { num: "R$9k", suf: "+", label: "Receita mensal média recuperada" },
              { num: "3×", suf: "", label: "Mais retorno de pacientes inativos" },
              { num: "8h", suf: "/sem", label: "Economizadas pela recepção" },
            ].map((m, i) => (
              <div key={i} className="met-item rev" ref={el => addRev(el, i)}>
                <div className="met-num"><em>{m.num}</em>{m.suf}</div>
                <div className="met-label">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── SOBRE ─── */}
      <section id="sobre">
        <div className="w">
          <div className="sobre-g">
            <div>
              <div className="sh rev" ref={el => addRev(el, 10)}><Zap size={11} /> O que é</div>
              <h2 className="sec-h2 rev" ref={el => addRev(el, 11)}>
                Um motor de <em>faturamento</em><br />para sua clínica
              </h2>
              <p className="sec-sub rev" ref={el => addRev(el, 12)}>
                Não é um lembrete de consulta. É um sistema que detecta quem vai faltar antes que isso aconteça, preenche horários vagos automaticamente e traz de volta pacientes que sumiram.
              </p>
              <div className="sobre-points">
                {[
                  { ico: <Target size={15} color="var(--acc)" />, title: "Prevenção de falta, não aviso", desc: "Identifica padrões e age antes — não depois que o horário esvazia." },
                  { ico: <BarChart3 size={15} color="var(--acc)" />, title: "Agenda como ativo estratégico", desc: "Cada horário é otimizado para maximizar comparecimento e receita." },
                  { ico: <RefreshCw size={15} color="var(--acc)" />, title: "Paciente retorna sozinho", desc: "Campanhas automáticas reativam quem sumiu sem trabalho manual." },
                ].map((pt, i) => (
                  <div key={i} className="sobre-pt rev" ref={el => addRev(el, 20 + i)}>
                    <div className="sobre-pt-icon">{pt.ico}</div>
                    <div><h4>{pt.title}</h4><p>{pt.desc}</p></div>
                  </div>
                ))}
              </div>
            </div>

            <div className="funil rev" ref={el => addRev(el, 30)}>
              <div className="funil-title">🔄 Motor CliniFlow — fluxo ativo</div>
              {[
                { ico: <Activity size={14} color="var(--acc)" />, lbl: "Paciente agenda", val: "Integra com sua agenda atual", badge: "Entrada" },
                { ico: <BarChart3 size={14} color="var(--acc)" />, lbl: "IA analisa comportamento", val: "Histórico + padrões de falta", badge: "Análise" },
                { ico: <MessageSquare size={14} color="var(--acc)" />, lbl: "Mensagem inteligente", val: "WhatsApp personalizado no tom certo", badge: "Ação" },
                { ico: <CalendarCheck size={14} color="var(--acc)" />, lbl: "Horário confirmado", val: "Encaixe automático se necessário", badge: "Resultado" },
              ].map((f, i) => (
                <div key={i} className="funil-step">
                  <div className="funil-ico">{f.ico}</div>
                  <div>
                    <div className="funil-lbl">{f.lbl}</div>
                    <div className="funil-val">{f.val}</div>
                  </div>
                  <div className="funil-badge">{f.badge}</div>
                </div>
              ))}
              <div style={{ marginTop: 16, padding: "12px 14px", background: "rgba(22,163,74,0.06)", borderRadius: 10, display: "flex", alignItems: "center", gap: 10 }}>
                <TrendingUp size={16} color="var(--acc)" />
                <span style={{ fontSize: "0.8rem", color: "var(--muted)", lineHeight: 1.4 }}>Resultado: <strong style={{ color: "var(--text)" }}>menos faltas + mais faturamento todo mês</strong></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── COMO FUNCIONA ─── */}
      <section className="sec-alt" id="como">
        <div className="w">
          <div style={{ textAlign: "center" }}>
            <div className="sh rev" ref={el => addRev(el, 40)} style={{ justifyContent: "center" }}><Zap size={11} /> Como funciona</div>
            <h2 className="sec-h2 rev" ref={el => addRev(el, 41)} style={{ textAlign: "center" }}>
              3 passos. <em>Zero complicação.</em>
            </h2>
            <p className="sec-sub rev" ref={el => addRev(el, 42)} style={{ margin: "0 auto", textAlign: "center" }}>
              Você conecta uma vez. O sistema trabalha todos os dias.
            </p>
          </div>
          <div className="steps-g">
            {[
              { n: "01", ico: <CalendarCheck size={17} color="var(--acc)" />, title: "Conecte sua agenda e WhatsApp", desc: "Integração simples com Google Calendar, iClinic e outros. Em minutos, o sistema já tem acesso ao histórico dos seus pacientes." },
              { n: "02", ico: <Activity size={17} color="var(--acc)" />, title: "A IA aprende e age", desc: "Analisa quem tem risco de falta, quando os pacientes costumam sumir e quais horários estão em risco — e toma ação antes do problema." },
              { n: "03", ico: <TrendingUp size={17} color="var(--acc)" />, title: "Agenda cheia, faturamento crescendo", desc: "Menos horários vazios, mais pacientes confirmando, retornando e pagando. Você acompanha tudo no painel em tempo real." },
            ].map((s, i) => (
              <div key={i} className={`g step-card rev d${i + 1}`} ref={el => addRev(el, 50 + i)}>
                <div className="step-num">{s.n}</div>
                <div className="step-icon">{s.ico}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── ANTES × DEPOIS ─── */}
      <section>
        <div className="w">
          <div style={{ textAlign: "center" }}>
            <div className="sh rev" ref={el => addRev(el, 60)} style={{ justifyContent: "center" }}><BarChart3 size={11} /> Antes × Depois</div>
            <h2 className="sec-h2 rev" ref={el => addRev(el, 61)} style={{ textAlign: "center" }}>
              A diferença é <em>visível</em> no faturamento
            </h2>
          </div>
          <div className="ad-g">
            <div className="ad-antes ad-card rev" ref={el => addRev(el, 62)}>
              <div className="ad-badge"><XCircle size={12} /> Antes do CliniFlow</div>
              {[
                "20–40% dos pacientes faltam sem avisar",
                "Horários ficam vazios e a receita oscila",
                "Recepção passa o dia confirmando consultas",
                "Pacientes some e nunca mais voltam",
                "Impossível prever o faturamento do mês",
              ].map((t, i) => (
                <div key={i} className="ad-item">
                  <XCircle size={15} color="var(--red)" style={{ flexShrink: 0, marginTop: 1 }} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
            <div className="ad-depois ad-card rev" ref={el => addRev(el, 63)}>
              <div className="ad-badge"><CheckCircle2 size={12} /> Com CliniFlow AI</div>
              {[
                "Faltas caem pela metade — horários sempre preenchidos",
                "Encaixes automáticos quando surge um buraco",
                "Equipe foca no atendimento, não em ligações",
                "Pacientes antigos retornam com campanhas automáticas",
                "Faturamento previsível e crescendo todo mês",
              ].map((t, i) => (
                <div key={i} className="ad-item">
                  <CheckCircle2 size={15} color="var(--acc)" style={{ flexShrink: 0, marginTop: 1 }} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Mini case */}
          <div className="g rev" ref={el => addRev(el, 64)} style={{ marginTop: 24, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 0 }}>
            <div style={{ padding: "24px 28px", borderRight: "1px solid var(--bdr)" }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--subt)", marginBottom: 6 }}>Clínica Odontológica • SP</div>
              <div style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.55 }}>"Tinha 8 faltas por semana. Hoje são 2. O sistema mandou mensagem pro paciente que costumava faltar às segundas e ele remarcou sozinho."</div>
            </div>
            <div style={{ padding: "24px 28px", borderRight: "1px solid var(--bdr)" }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--subt)", marginBottom: 6 }}>Psicóloga • RJ</div>
              <div style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.55 }}>"Voltei a ter lista de espera. Antes eu ficava com horários vazios toda semana. Agora o sistema preenche automaticamente."</div>
            </div>
            <div style={{ padding: "24px 28px" }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--subt)", marginBottom: 6 }}>Clínica de Estética • MG</div>
              <div style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.55 }}>"Pacientes que estavam sumidos há meses voltaram depois da campanha automática. Sem eu precisar ligar pra nenhum."</div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── PARA QUEM ─── */}
      <section className="sec-alt" id="quem">
        <div className="w">
          <div style={{ textAlign: "center" }}>
            <div className="sh rev" ref={el => addRev(el, 70)} style={{ justifyContent: "center" }}><Users size={11} /> Para quem é</div>
            <h2 className="sec-h2 rev" ref={el => addRev(el, 71)} style={{ textAlign: "center" }}>
              Feito para quem tem <em>agenda recorrente</em>
            </h2>
            <p className="sec-sub rev" ref={el => addRev(el, 72)} style={{ margin: "0 auto", textAlign: "center" }}>
              Qualquer negócio onde falta = dinheiro perdido na hora.
            </p>
          </div>
          <div className="quem-g">
            {[
              { ico: <HeartPulse size={17} />, title: "Clínicas Odontológicas", desc: "Alta recorrência e ticket elevado — cada falta impacta direto no caixa." },
              { ico: <Sparkles size={17} />, title: "Estética e Dermatologia", desc: "Procedimentos agendados com antecedência: cancelamento sem aviso custa caro." },
              { ico: <GraduationCap size={17} />, title: "Psicólogos e Terapeutas", desc: "Agenda semanal fixa que precisa de previsibilidade total de comparecimento." },
              { ico: <Building2 size={17} />, title: "Clínicas Particulares", desc: "Médicos especialistas com agenda restrita e consultas de alto valor." },
              { ico: <Star size={17} />, title: "Fisioterapeutas", desc: "Tratamentos em série que exigem continuidade e presença constante." },
              { ico: <Shield size={17} />, title: "Clínicas Veterinárias", desc: "Consultas, vacinas e procedimentos com recorrência previsível." },
            ].map((q, i) => (
              <div key={i} className={`g quem-card rev d${(i % 3) + 1}`} ref={el => addRev(el, 80 + i)}>
                <div className="quem-ico">{q.ico}</div>
                <h4>{q.title}</h4>
                <p>{q.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── MAIS SOLUÇÕES ─── */}
      <div className="mais-band">
        <div className="w">
          <div className="mais-inner">
            <div className="mais-ico"><Layers size={18} /></div>
            <div className="mais-text">
              <strong>Explore nossas outras soluções de IA</strong>
              <span>Atendimento automatizado, vendas, marketing e mais — para qualquer nicho.</span>
            </div>
            <a href="#contato" className="mais-pill">
              <ExternalLink size={13} /> Ver todas as soluções
            </a>
          </div>
        </div>
      </div>

      {/* ─── CONTATO ─── */}
      <section id="contato">
        <div className="w">
          <div className="contato-g">
            <div>
              <div className="sh rev" ref={el => addRev(el, 90)}><MessageSquare size={11} /> Fale com a gente</div>
              <h2 className="sec-h2 rev" ref={el => addRev(el, 91)}>
                Quer isso na<br /><em>sua clínica?</em>
              </h2>
              <p className="sec-sub rev" ref={el => addRev(el, 92)} style={{ marginBottom: 28 }}>
                Mostramos como funciona com a sua agenda real. Sem compromisso, sem enrolação.
              </p>

              <div className="canal-list">
                {[
                  { cls: "wpp",  ico: <MessageSquare size={16} />, label: "WhatsApp", detail: "Resposta em até 2 horas", href: "https://wa.me/5511999999999" },
                  { cls: "mail", ico: <Mail size={16} />,          label: "E-mail",    detail: "contato@cliniflow.ai", href: "mailto:contato@cliniflow.ai" },
                  { cls: "tel",  ico: <Phone size={16} />,         label: "Telefone",  detail: "Seg–Sex, 9h–18h",  href: "tel:+5511999999999" },
                ].map((c, i) => (
                  <a key={i} href={c.href} className="canal rev" ref={el => addRev(el, 93 + i)}>
                    <div className={`canal-ico ${c.cls}`}>{c.ico}</div>
                    <div className="canal-info">
                      <strong>{c.label}</strong>
                      <span>{c.detail}</span>
                    </div>
                    <ChevronRight size={15} className="canal-arrow" />
                  </a>
                ))}
              </div>
            </div>

            <div className="form-card rev" ref={el => addRev(el, 97)}>
              {submitted ? (
                <div className="success-state">
                  <div className="success-ico"><CheckCircle2 size={26} /></div>
                  <h3>Mensagem enviada!</h3>
                  <p>Entraremos em contato em breve para apresentar a solução.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit}>
                  <div className="form-title">Enviar mensagem</div>
                  <div className="form-row">
                    <div className="form-field">
                      <label>Nome</label>
                      <input required placeholder="Seu nome" value={formData.nome} onChange={e => setFormData(p => ({ ...p, nome: e.target.value }))} />
                    </div>
                    <div className="form-field">
                      <label>Empresa / Clínica</label>
                      <input placeholder="Nome da clínica" value={formData.empresa} onChange={e => setFormData(p => ({ ...p, empresa: e.target.value }))} />
                    </div>
                  </div>
                  <div className="form-field">
                    <label>E-mail</label>
                    <input required type="email" placeholder="seu@email.com" value={formData.email} onChange={e => setFormData(p => ({ ...p, email: e.target.value }))} />
                  </div>
                  <div className="form-field">
                    <label>Como podemos ajudar?</label>
                    <textarea rows={4} placeholder="Conte sobre sua clínica e o principal desafio com agendamentos..." value={formData.msg} onChange={e => setFormData(p => ({ ...p, msg: e.target.value }))} />
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

      {/* ─── FOOTER ─── */}
      <footer className="footer">
        <div className="w">
          <div className="footer-inner">
            <a href="#hero" className="footer-logo">
              <div className="nav-logo-icon" style={{ width: 24, height: 24, borderRadius: 6 }}>
                <CalendarCheck size={12} color="white" />
              </div>
              CliniFlow<span style={{ color: "var(--acc)" }}>AI</span>
            </a>
            <span className="footer-copy">© 2025 CliniFlow AI. Todos os direitos reservados.</span>
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