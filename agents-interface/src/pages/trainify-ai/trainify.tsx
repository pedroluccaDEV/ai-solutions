import { useState, useEffect, useRef } from "react";
import {
  Zap, Activity, Sparkles, CheckCircle2, XCircle, ChevronRight,
  MessageSquare, Mail, Phone, Layers, ExternalLink, Target,
  BarChart3, Dumbbell, Clock, Users, TrendingUp, Wrench,
  GraduationCap, Shield, Globe, HeartPulse, Repeat, Star,
  ArrowRight, Check
} from "lucide-react";

/* ─── Google Fonts ─── */
const FontLink = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Cormorant+Garamond:ital,wght@1,400;1,600&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

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
      --green: #16a34a;
      --font:  'Syne', 'Inter', sans-serif;
      --serif: 'Cormorant Garamond', Georgia, serif;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: var(--font);
      color: var(--text);
      background: var(--white);
      overflow-x: hidden;
      line-height: 1.6;
    }

    h1,h2,h3,h4,h5 { line-height: 1.15; }

    .w { max-width: 1060px; margin: 0 auto; padding: 0 28px; }
    section { padding: 88px 0; position: relative; z-index: 1; }
    .sec-alt { background: var(--off); }

    /* Aurora */
    .aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
    .ab { position: absolute; border-radius: 50%; animation: af linear infinite; will-change: transform; }
    .ab1 { width: 820px; height: 520px; top: -180px; left: -160px; filter: blur(72px); animation-duration: 26s; background: radial-gradient(ellipse, rgba(251,191,36,0.22) 0%, transparent 70%); }
    .ab2 { width: 600px; height: 460px; top: 50px; right: -100px; filter: blur(80px); animation-duration: 33s; animation-delay: -10s; background: radial-gradient(ellipse, rgba(245,158,11,0.18) 0%, transparent 70%); }
    .ab3 { width: 680px; height: 400px; top: 260px; left: 25%; filter: blur(90px); animation-duration: 21s; animation-delay: -6s; background: radial-gradient(ellipse, rgba(249,115,22,0.14) 0%, transparent 70%); }
    .ab4 { width: 480px; height: 360px; bottom: 160px; right: 12%; filter: blur(70px); animation-duration: 29s; animation-delay: -16s; background: radial-gradient(ellipse, rgba(217,119,6,0.16) 0%, transparent 70%); }

    @keyframes af {
      0%   { transform: translate(0,0) scale(1); }
      25%  { transform: translate(32px,-44px) scale(1.06); }
      50%  { transform: translate(58px,-6px) scale(0.94); }
      75%  { transform: translate(18px,30px) scale(1.05); }
      100% { transform: translate(0,0) scale(1); }
    }

    /* Nav */
    .nav-pill {
      position: fixed; top: 14px; left: 50%; transform: translateX(-50%);
      width: calc(100% - 40px); max-width: 1060px;
      background: rgba(255,255,255,0.78); backdrop-filter: blur(28px);
      border: 1px solid var(--bdr2); border-radius: 18px;
      padding: 10px 20px; display: flex; align-items: center; gap: 20px;
      z-index: 999; box-shadow: 0 2px 24px rgba(217,119,6,0.08);
    }
    .nav-logo { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.95rem; color: var(--text); text-decoration: none; }
    .nav-logo-icon { width: 28px; height: 28px; background: linear-gradient(135deg, var(--acc), var(--acc3)); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; }
    .nav-links { display: flex; gap: 6px; flex: 1; margin-left: 12px; }
    .nav-links a { font-size: 0.82rem; font-weight: 500; color: var(--muted); text-decoration: none; padding: 5px 10px; border-radius: 8px; transition: all 0.18s; }
    .nav-links a:hover { color: var(--text); background: var(--surf); }
    .nav-cta { margin-left: auto; background: linear-gradient(135deg, var(--acc), var(--acc2)); color: white; border: none; padding: 8px 18px; border-radius: 10px; font-size: 0.82rem; font-weight: 700; cursor: pointer; font-family: var(--font); transition: all 0.2s; white-space: nowrap; }
    .nav-cta:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(217,119,6,0.3); }

    /* Eyebrow */
    .ep {
      display: inline-flex; align-items: center; gap: 7px;
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
      color: var(--acc); background: rgba(217,119,6,0.08);
      border: 1px solid rgba(217,119,6,0.18);
      padding: 5px 13px; border-radius: 100px; margin-bottom: 18px;
    }

    /* Hero */
    .hero { padding: 148px 0 80px; min-height: 100vh; display: flex; align-items: center; }
    .hero-g { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 56px; align-items: center; }
    .hero h1 { font-size: clamp(2.1rem, 4.4vw, 3.3rem); font-weight: 800; line-height: 1.08; margin-bottom: 18px; letter-spacing: -0.02em; }
    .hero h1 em { font-style: italic; font-family: var(--serif); color: var(--acc); font-weight: 600; }
    .hero p { font-size: 1.05rem; color: var(--muted); margin-bottom: 32px; line-height: 1.65; max-width: 420px; }
    .ctas { display: flex; gap: 12px; flex-wrap: wrap; }
    .bp { background: linear-gradient(135deg, var(--acc), var(--acc2)); color: white; border: none; padding: 13px 24px; border-radius: 11px; font-size: 0.9rem; font-weight: 700; cursor: pointer; font-family: var(--font); transition: all 0.22s; display: inline-flex; align-items: center; gap: 8px; text-decoration: none; }
    .bp:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(217,119,6,0.32); }
    .bo { background: transparent; color: var(--text); border: 1px solid var(--bdr2); padding: 13px 24px; border-radius: 11px; font-size: 0.9rem; font-weight: 600; cursor: pointer; font-family: var(--font); transition: all 0.22s; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }
    .bo:hover { background: var(--surf); }

    /* Hero visual */
    .hero-visual-wrap { position: relative; display: flex; justify-content: center; }
    .hero-glow { position: absolute; width: 380px; height: 380px; border-radius: 50%; background: radial-gradient(ellipse, rgba(251,191,36,0.35) 0%, transparent 70%); top: 50%; left: 50%; transform: translate(-50%,-50%); animation: glowPulse 4s ease-in-out infinite; }
    .hero-visual { animation: heroFloat 6s ease-in-out infinite; position: relative; z-index: 1; }
    @keyframes heroFloat {
      0%,100% { transform: rotateY(-14deg) rotateX(5deg) translateY(0px); }
      50%      { transform: rotateY(-8deg) rotateX(3deg) translateY(-12px); }
    }
    @keyframes glowPulse {
      0%,100% { opacity: 0.7; transform: translate(-50%,-50%) scale(1); }
      50%      { opacity: 1; transform: translate(-50%,-50%) scale(1.15); }
    }

    /* Workout card mockup */
    .wk-card { background: white; border-radius: 20px; box-shadow: 0 24px 60px rgba(0,0,0,0.12); width: 320px; overflow: hidden; border: 1px solid var(--bdr2); }
    .wk-header { background: linear-gradient(135deg, var(--acc), var(--acc2)); padding: 18px 20px; color: white; }
    .wk-header-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
    .wk-badge { background: rgba(255,255,255,0.2); font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; letter-spacing: 0.06em; text-transform: uppercase; }
    .wk-name { font-size: 1.1rem; font-weight: 700; }
    .wk-sub { font-size: 0.75rem; opacity: 0.8; margin-top: 2px; }
    .wk-exercises { padding: 14px; display: flex; flex-direction: column; gap: 8px; }
    .wk-ex { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px; background: var(--off); border: 1px solid var(--bdr); }
    .wk-ex-num { width: 22px; height: 22px; border-radius: 6px; background: linear-gradient(135deg, var(--acc3), var(--acc)); color: white; font-size: 0.65rem; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .wk-ex-info { flex: 1; }
    .wk-ex-name { font-size: 0.78rem; font-weight: 700; color: var(--text); }
    .wk-ex-detail { font-size: 0.68rem; color: var(--muted); margin-top: 1px; }
    .wk-ex-check { width: 18px; height: 18px; border-radius: 50%; background: rgba(22,163,74,0.12); display: flex; align-items: center; justify-content: center; }
    .wk-footer { padding: 10px 14px 14px; display: flex; gap: 8px; }
    .wk-btn-primary { flex: 1; background: linear-gradient(135deg, var(--acc), var(--acc2)); color: white; border: none; padding: 9px; border-radius: 9px; font-size: 0.75rem; font-weight: 700; cursor: pointer; font-family: var(--font); }
    .wk-btn-sec { background: var(--surf); color: var(--muted); border: 1px solid var(--bdr2); padding: 9px 12px; border-radius: 9px; font-size: 0.75rem; font-weight: 600; cursor: pointer; font-family: var(--font); }
    .wk-timer { display: flex; align-items: center; gap: 4px; font-size: 0.68rem; color: var(--subt); margin: 0 14px 8px; background: rgba(217,119,6,0.06); border: 1px solid rgba(217,119,6,0.1); border-radius: 7px; padding: 5px 8px; }
    .wk-generating { display: flex; flex-direction: column; gap: 6px; padding: 8px 14px 14px; }
    .wk-gen-label { font-size: 0.67rem; font-weight: 700; color: var(--acc); text-transform: uppercase; letter-spacing: 0.07em; display: flex; align-items: center; gap: 5px; }
    .wk-bar { height: 5px; border-radius: 20px; background: var(--surf); overflow: hidden; }
    .wk-bar-fill { height: 100%; border-radius: 20px; background: linear-gradient(90deg, var(--acc3), var(--acc)); animation: barFill 1.6s ease-in-out infinite alternate; }
    @keyframes barFill { from { width: 30%; } to { width: 95%; } }

    /* Section header */
    .sh { display: inline-flex; align-items: center; gap: 6px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; color: var(--acc); margin-bottom: 13px; }
    h2 { font-size: clamp(1.65rem, 3.4vw, 2.45rem); font-weight: 800; letter-spacing: -0.02em; margin-bottom: 16px; }
    h2 em { font-style: italic; font-family: var(--serif); color: var(--acc); font-weight: 600; }

    /* Glass card */
    .g { background: rgba(255,255,255,0.72); backdrop-filter: blur(22px); border: 1px solid var(--bdr2); border-radius: 18px; box-shadow: 0 2px 16px rgba(217,119,6,0.04); transition: all 0.22s; }
    .g:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(217,119,6,0.1); border-color: rgba(217,119,6,0.25); }

    /* Metrics */
    .met-box { display: grid; grid-template-columns: repeat(4,1fr); gap: 18px; }
    .met-item { text-align: center; padding: 28px 16px; }
    .met-num { font-size: 2.6rem; font-weight: 800; color: var(--acc); line-height: 1; font-family: var(--serif); font-style: italic; }
    .met-label { font-size: 0.78rem; color: var(--muted); margin-top: 6px; font-weight: 600; }

    /* Sobre */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }
    .sobre-cards { display: flex; flex-direction: column; gap: 14px; }
    .sobre-card { padding: 18px 20px; display: flex; align-items: flex-start; gap: 14px; }
    .sobre-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(217,119,6,0.1); color: var(--acc); flex-shrink: 0; }
    .sobre-card h4 { font-size: 0.88rem; font-weight: 700; margin-bottom: 4px; }
    .sobre-card p { font-size: 0.82rem; color: var(--muted); line-height: 1.5; }

    /* Steps */
    .three-col { display: grid; grid-template-columns: repeat(3,1fr); gap: 18px; position: relative; }
    .three-col::before { content: ''; position: absolute; top: 36px; left: 20%; right: 20%; height: 1px; background: linear-gradient(90deg, transparent, var(--bdr2), transparent); z-index: 0; }
    .step-card { padding: 28px 22px; position: relative; z-index: 1; }
    .step-num { width: 42px; height: 42px; border-radius: 12px; background: linear-gradient(135deg, rgba(217,119,6,0.12), rgba(245,158,11,0.08)); border: 1px solid rgba(217,119,6,0.2); color: var(--acc); font-size: 0.8rem; font-weight: 800; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
    .step-card h3 { font-size: 0.95rem; font-weight: 700; margin-bottom: 8px; }
    .step-card p { font-size: 0.82rem; color: var(--muted); line-height: 1.55; }

    /* Antes depois */
    .ad-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    .ad-card { padding: 28px; border-radius: 18px; }
    .ad-antes { background: rgba(220,38,38,0.04); border: 1px solid rgba(220,38,38,0.15); }
    .ad-depois { background: rgba(217,119,6,0.04); border: 1px solid rgba(217,119,6,0.2); }
    .ad-title { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 18px; }
    .ad-antes .ad-title { color: var(--red); }
    .ad-depois .ad-title { color: var(--acc); }
    .ad-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; font-size: 0.85rem; line-height: 1.5; }
    .ad-antes .ad-item { color: #7c2d2d; }
    .ad-depois .ad-item { color: #7c3d00; }

    /* Para quem */
    .quem-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
    .quem-card { padding: 22px; display: flex; align-items: flex-start; gap: 14px; }
    .quem-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(217,119,6,0.08); color: var(--acc); flex-shrink: 0; }
    .quem-card h4 { font-size: 0.87rem; font-weight: 700; margin-bottom: 4px; }
    .quem-card p { font-size: 0.78rem; color: var(--muted); line-height: 1.45; }

    /* More solutions band */
    .band { background: rgba(254,243,199,0.6); backdrop-filter: blur(14px); border-top: 1px solid var(--bdr2); border-bottom: 1px solid var(--bdr2); padding: 28px 0; }
    .band-inner { display: flex; align-items: center; gap: 16px; }
    .band-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(217,119,6,0.1); display: flex; align-items: center; justify-content: center; color: var(--acc); flex-shrink: 0; }
    .band-text { flex: 1; }
    .band-text strong { font-size: 0.9rem; font-weight: 700; display: block; margin-bottom: 2px; }
    .band-text span { font-size: 0.8rem; color: var(--muted); }
    .band-btn { background: var(--white); border: 1px solid var(--bdr2); color: var(--text); padding: 8px 16px; border-radius: 100px; font-size: 0.8rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.18s; white-space: nowrap; font-family: var(--font); }
    .band-btn:hover { background: var(--surf); }

    /* Contact */
    .contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
    .channel-list { display: flex; flex-direction: column; gap: 12px; margin-top: 28px; }
    .channel { padding: 16px 18px; display: flex; align-items: center; gap: 14px; text-decoration: none; cursor: pointer; }
    .channel-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: rgba(217,119,6,0.08); color: var(--acc); flex-shrink: 0; }
    .channel-info { flex: 1; }
    .channel-info strong { font-size: 0.85rem; font-weight: 700; display: block; color: var(--text); }
    .channel-info span { font-size: 0.75rem; color: var(--muted); }
    .channel svg:last-child { color: var(--subt); }

    /* Form */
    .form-card { padding: 28px; }
    .form-title { font-size: 1rem; font-weight: 700; margin-bottom: 20px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
    .form-field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; }
    .form-field label { font-size: 0.75rem; font-weight: 600; color: var(--muted); }
    .form-field input, .form-field textarea {
      padding: 10px 14px; border-radius: 10px; border: 1px solid var(--bdr2);
      background: var(--white); font-family: var(--font); font-size: 0.85rem; color: var(--text);
      outline: none; transition: border-color 0.18s;
    }
    .form-field input:focus, .form-field textarea:focus { border-color: var(--acc); }
    .form-field textarea { resize: vertical; min-height: 90px; }
    .form-submit { width: 100%; background: linear-gradient(135deg, var(--acc), var(--acc2)); color: white; border: none; padding: 13px; border-radius: 11px; font-size: 0.9rem; font-weight: 700; cursor: pointer; font-family: var(--font); display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.22s; }
    .form-submit:hover { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(217,119,6,0.28); }
    .form-success { text-align: center; padding: 32px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
    .form-success-icon { width: 52px; height: 52px; border-radius: 50%; background: rgba(22,163,74,0.1); display: flex; align-items: center; justify-content: center; color: var(--green); }
    .form-success h4 { font-size: 1rem; font-weight: 700; }
    .form-success p { font-size: 0.83rem; color: var(--muted); }

    /* Footer */
    footer { background: var(--off); border-top: 1px solid var(--bdr2); padding: 32px 0; }
    .footer-inner { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; }
    .footer-logo { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 0.88rem; }
    .footer-logo-icon { width: 26px; height: 26px; background: linear-gradient(135deg, var(--acc), var(--acc3)); border-radius: 7px; display: flex; align-items: center; justify-content: center; color: white; }
    .footer-links { display: flex; gap: 18px; }
    .footer-links a { font-size: 0.78rem; color: var(--muted); text-decoration: none; transition: color 0.15s; }
    .footer-links a:hover { color: var(--text); }
    .footer-copy { font-size: 0.75rem; color: var(--subt); }

    /* Reveal */
    .rev { opacity: 0; transform: translateY(14px); transition: opacity .5s ease, transform .5s ease; }
    .rev.vis { opacity: 1; transform: translateY(0); }
    .rev-d1 { transition-delay: 0.1s; }
    .rev-d2 { transition-delay: 0.2s; }
    .rev-d3 { transition-delay: 0.3s; }

    /* Hero animations */
    @keyframes up { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    .anim-ep   { animation: up 0.6s 0.0s ease both; }
    .anim-h1   { animation: up 0.6s 0.1s ease both; }
    .anim-sub  { animation: up 0.6s 0.2s ease both; }
    .anim-ctas { animation: up 0.6s 0.3s ease both; }

    /* Dot pulse for generating */
    .dot-pulse { display: flex; gap: 3px; align-items: center; }
    .dot-pulse span { width: 4px; height: 4px; border-radius: 50%; background: var(--acc); animation: dotBounce 1.2s ease-in-out infinite; }
    .dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
    .dot-pulse span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotBounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }

    @media (max-width: 768px) {
      .hero-g, .two-col, .contact-grid { grid-template-columns: 1fr; gap: 32px; }
      .hero-visual-wrap { display: none; }
      .three-col, .quem-grid { grid-template-columns: 1fr; }
      .met-box { grid-template-columns: repeat(2,1fr); }
      .ad-grid { grid-template-columns: 1fr; }
      .form-row { grid-template-columns: 1fr; }
      .nav-links { display: none; }
      .footer-inner { flex-direction: column; align-items: flex-start; }
    }
  `}</style>
);

/* ─── Hero Visual ─── */
const HeroVisual = () => {
  const [step, setStep] = useState(0); // 0=form, 1=generating, 2=ready
  useEffect(() => {
    const t1 = setTimeout(() => setStep(1), 2200);
    const t2 = setTimeout(() => setStep(2), 4200);
    const t3 = setTimeout(() => setStep(0), 8000);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [step]);

  return (
    <div className="hero-visual-wrap">
      <div className="hero-glow" />
      <div className="hero-visual">
        <div className="wk-card">
          <div className="wk-header">
            <div className="wk-header-top">
              <span className="wk-badge">Treino A — Superior</span>
              <div className="dot-pulse">
                {step === 1 && <><span /><span /><span /></>}
                {step === 2 && <CheckCircle2 size={14} />}
                {step === 0 && <Zap size={14} />}
              </div>
            </div>
            <div className="wk-name">Carlos Mendes</div>
            <div className="wk-sub">Hipertrofia · Intermediário · 3×/semana</div>
          </div>

          {step === 0 && (
            <>
              <div className="wk-timer">
                <Clock size={11} style={{color:'var(--acc)'}} />
                <span>Gerado em 3 minutos — aguardando aprovação</span>
              </div>
              <div className="wk-exercises">
                {[
                  ["Supino Inclinado", "4×10 · 75kg · 90s descanso"],
                  ["Crucifixo Polia", "3×12 · 20kg · 60s descanso"],
                  ["Desenvolvimento", "4×10 · 55kg · 90s descanso"],
                ].map(([name, detail], i) => (
                  <div className="wk-ex" key={i}>
                    <div className="wk-ex-num">{i+1}</div>
                    <div className="wk-ex-info">
                      <div className="wk-ex-name">{name}</div>
                      <div className="wk-ex-detail">{detail}</div>
                    </div>
                    <div className="wk-ex-check">
                      <CheckCircle2 size={10} style={{color:'var(--green)'}} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="wk-footer">
                <button className="wk-btn-primary">✓ Aprovar treino</button>
                <button className="wk-btn-sec">Ajustar</button>
              </div>
            </>
          )}

          {step === 1 && (
            <div className="wk-generating">
              <div className="wk-gen-label">
                <div className="dot-pulse"><span /><span /><span /></div>
                Gerando treino personalizado
              </div>
              {["Analisando perfil do aluno...", "Selecionando exercícios...", "Calculando progressão..."].map((t, i) => (
                <div key={i}>
                  <div style={{fontSize:'0.72rem', color:'var(--muted)', marginBottom:'4px'}}>{t}</div>
                  <div className="wk-bar">
                    <div className="wk-bar-fill" style={{animationDelay:`${i*0.3}s`}} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {step === 2 && (
            <>
              <div className="wk-timer" style={{background:'rgba(22,163,74,0.06)', borderColor:'rgba(22,163,74,0.15)'}}>
                <CheckCircle2 size={11} style={{color:'var(--green)'}} />
                <span style={{color:'var(--green)', fontWeight:700}}>Treino pronto! Aprovado e enviado ao aluno</span>
              </div>
              <div className="wk-exercises">
                {[
                  ["Supino Inclinado", "4×10 · 75kg · 90s descanso"],
                  ["Crucifixo Polia", "3×12 · 20kg · 60s descanso"],
                  ["Desenvolvimento", "4×10 · 55kg · 90s descanso"],
                ].map(([name, detail], i) => (
                  <div className="wk-ex" key={i} style={{background:'rgba(22,163,74,0.04)', borderColor:'rgba(22,163,74,0.15)'}}>
                    <div className="wk-ex-num" style={{background:'linear-gradient(135deg,var(--green),#15803d)'}}>{i+1}</div>
                    <div className="wk-ex-info">
                      <div className="wk-ex-name">{name}</div>
                      <div className="wk-ex-detail">{detail}</div>
                    </div>
                    <div className="wk-ex-check"><CheckCircle2 size={10} style={{color:'var(--green)'}} /></div>
                  </div>
                ))}
              </div>
              <div className="wk-footer">
                <button className="wk-btn-primary" style={{background:'linear-gradient(135deg,var(--green),#15803d)'}}>✓ Enviado ao aluno</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

/* ─── Reveal Hook ─── */
const useReveal = () => {
  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('vis'); });
    }, { threshold: 0.1 });
    document.querySelectorAll('.rev').forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
};

/* ─── Main Component ─── */
export default function TreinoIA() {
  const [formState, setFormState] = useState({ nome:'', empresa:'', email:'', msg:'' });
  const [sent, setSent] = useState(false);
  useReveal();

  const handleSubmit = (e) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <>
      <FontLink />

      {/* Aurora */}
      <div className="aurora">
        <div className="ab ab1" />
        <div className="ab ab2" />
        <div className="ab ab3" />
        <div className="ab ab4" />
      </div>

      {/* Nav */}
      <nav className="nav-pill">
        <a href="#hero" className="nav-logo">
          <div className="nav-logo-icon"><Dumbbell size={14} /></div>
          TreinoIA
        </a>
        <div className="nav-links">
          <a href="#sobre">Sobre</a>
          <a href="#como">Como funciona</a>
          <a href="#quem">Para quem</a>
        </div>
        <button className="nav-cta" onClick={() => document.getElementById('contato')?.scrollIntoView({behavior:'smooth'})}>
          Falar com especialista
        </button>
      </nav>

      {/* Hero */}
      <section className="hero" id="hero">
        <div className="w">
          <div className="hero-g">
            <div>
              <div className="ep anim-ep">
                <Activity size={11} />
                Prescrição inteligente de treinos
              </div>
              <h1 className="anim-h1">
                Monte treinos <em>perfeitos</em><br />
                em minutos, não horas
              </h1>
              <p className="anim-sub">
                Você insere os dados do aluno — objetivo, nível e rotina. O sistema entrega um treino completo, personalizado e pronto para aprovar. Sem planilhas. Sem retrabalho.
              </p>
              <div className="ctas anim-ctas">
                <a href="#contato" className="bp">
                  Quero ver na prática <ArrowRight size={15} />
                </a>
                <a href="#como" className="bo">
                  Como funciona
                </a>
              </div>
            </div>
            <HeroVisual />
          </div>
        </div>
      </section>

      {/* Métricas */}
      <section style={{padding:'48px 0', background:'var(--off)', borderTop:'1px solid var(--bdr2)', borderBottom:'1px solid var(--bdr2)'}}>
        <div className="w">
          <div className="met-box">
            {[
              { num: "5min", label: "para gerar um treino completo" },
              { num: "10×", label: "mais alunos atendidos por semana" },
              { num: "90%", label: "redução no tempo de prescrição" },
              { num: "Zero", label: "retrabalho com ajustes manuais" },
            ].map((m, i) => (
              <div className="met-item g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                <div className="met-num">{m.num}</div>
                <div className="met-label">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sobre */}
      <section id="sobre">
        <div className="w">
          <div className="two-col">
            <div>
              <div className="sh rev"><Zap size={11} /> O que é</div>
              <h2 className="rev">Seu sistema de <em>prescrição</em><br />assistida de treinos</h2>
              <p className="rev" style={{color:'var(--muted)', fontSize:'0.95rem', lineHeight:1.7, marginBottom:24}}>
                Não é um app de treino para o aluno. É uma ferramenta para você, profissional — que transforma horas de montagem manual em minutos de revisão e aprovação.
              </p>
              <p className="rev" style={{color:'var(--muted)', fontSize:'0.95rem', lineHeight:1.7}}>
                Você mantém o controle total sobre cada decisão. O sistema cuida da parte repetitiva: estrutura, volumes, progressões e adaptações.
              </p>
            </div>
            <div className="sobre-cards">
              {[
                { icon: <Clock size={16} />, title: "Criação em minutos", desc: "Treinos completos com lógica de progressão gerados automaticamente com base no perfil real do aluno." },
                { icon: <Target size={16} />, title: "Personalização real", desc: "Objetivo, nível, limitações, equipamentos e rotina — tudo considerado na hora de montar o programa." },
                { icon: <BarChart3 size={16} />, title: "Acompanhamento contínuo", desc: "Evolução registrada e ajustes automáticos baseados no desempenho. Sem perder nenhum dado." },
              ].map((c, i) => (
                <div className="sobre-card g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                  <div className="sobre-icon">{c.icon}</div>
                  <div>
                    <h4>{c.title}</h4>
                    <p>{c.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section id="como" className="sec-alt">
        <div className="w">
          <div style={{textAlign:'center', marginBottom:48}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Zap size={11} /> Como funciona</div>
            <h2 className="rev">3 passos. <em>Treino pronto.</em></h2>
          </div>
          <div className="three-col">
            {[
              { num:"01", icon:<MessageSquare size={16}/>, title:"Insira os dados do aluno", desc:"Objetivo, nível de experiência, limitações físicas, equipamentos disponíveis e frequência semanal. Leva menos de 2 minutos." },
              { num:"02", icon:<Zap size={16}/>, title:"O sistema gera o treino", desc:"Em segundos, você recebe um plano completo com exercícios, séries, cargas e lógica de progressão — já adaptado ao contexto do aluno." },
              { num:"03", icon:<CheckCircle2 size={16}/>, title:"Revise, aprove e envie", desc:"Você confere, ajusta o que quiser e aprova com um clique. O treino vai direto para o aluno, pronto para executar." },
            ].map((s, i) => (
              <div className="step-card g rev" key={i} style={{transitionDelay:`${i*0.12}s`}}>
                <div className="step-num">{s.num}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Antes × Depois */}
      <section>
        <div className="w">
          <div style={{textAlign:'center', marginBottom:40}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Activity size={11} /> Antes × Depois</div>
            <h2 className="rev">O que <em>muda</em> na prática</h2>
          </div>
          <div className="ad-grid">
            <div className="ad-card ad-antes rev">
              <div className="ad-title"><XCircle size={14} /> Sem o sistema</div>
              {[
                "40 minutos para montar um treino do zero",
                "Revisar planilhas antigas para lembrar o que fez antes",
                "Risco de não adaptar corretamente ao aluno",
                "Acompanhamento de evolução superficial ou esquecido",
                "Limite de alunos por falta de tempo operacional",
              ].map((t, i) => (
                <div className="ad-item" key={i}>
                  <XCircle size={14} style={{color:'var(--red)', flexShrink:0, marginTop:2}} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
            <div className="ad-card ad-depois rev rev-d1">
              <div className="ad-title"><CheckCircle2 size={14} /> Com o sistema</div>
              {[
                "Treino completo em menos de 5 minutos",
                "Histórico do aluno acessível e considerado automaticamente",
                "Personalização real baseada nos dados reais do aluno",
                "Evolução registrada e ajustes automáticos no momento certo",
                "Escalar atendimento sem aumentar horas de trabalho",
              ].map((t, i) => (
                <div className="ad-item" key={i}>
                  <CheckCircle2 size={14} style={{color:'var(--acc)', flexShrink:0, marginTop:2}} />
                  <span>{t}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Para quem */}
      <section id="quem" className="sec-alt">
        <div className="w">
          <div style={{textAlign:'center', marginBottom:40}}>
            <div className="sh rev" style={{justifyContent:'center'}}><Users size={11} /> Para quem é</div>
            <h2 className="rev">Feito para quem <em>prescreve</em><br />treinos no dia a dia</h2>
          </div>
          <div className="quem-grid">
            {[
              { icon:<HeartPulse size={16}/>, title:"Personal trainer independente", desc:"Atenda mais alunos sem abrir mão da qualidade ou trabalhar o dobro de horas." },
              { icon:<Globe size={16}/>, title:"Consultoria online de treino", desc:"Escale sua base de alunos digitais sem que a criação de programas vire um gargalo." },
              { icon:<Building2 size={16}/>, title:"Academia pequeno/médio porte", desc:"Padronize a qualidade dos treinos de toda a equipe de professores com consistência." },
              { icon:<Dumbbell size={16}/>, title:"Studio de treino funcional", desc:"Gere programas específicos para o método do seu studio em fração do tempo atual." },
              { icon:<Users size={16}/>, title:"Profissional com muitos alunos", desc:"Se você atende 20, 30 ou mais alunos simultaneamente, esse sistema foi feito para você." },
              { icon:<TrendingUp size={16}/>, title:"Quem quer escalar o negócio", desc:"Transforme tempo gasto em operação em capacidade de crescimento e mais receita." },
            ].map((c, i) => (
              <div className="quem-card g rev" key={i} style={{transitionDelay:`${i*0.08}s`}}>
                <div className="quem-icon">{c.icon}</div>
                <div>
                  <h4>{c.title}</h4>
                  <p>{c.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* More solutions band */}
      <div className="band">
        <div className="w">
          <div className="band-inner">
            <div className="band-icon"><Layers size={18} /></div>
            <div className="band-text">
              <strong>Mais de 20 soluções de automação disponíveis</strong>
              <span>Atendimento, vendas, conteúdo, agendamento, CRM e muito mais — integrados ao seu negócio.</span>
            </div>
            <button className="band-btn">
              Ver todas as soluções <ExternalLink size={13} />
            </button>
          </div>
        </div>
      </div>

      {/* Contato */}
      <section id="contato">
        <div className="w">
          <div style={{marginBottom:40}}>
            <div className="sh rev"><MessageSquare size={11} /> Fale com a gente</div>
            <h2 className="rev">Quer isso no seu <em>negócio?</em></h2>
            <p className="rev" style={{color:'var(--muted)', maxWidth:420, fontSize:'0.95rem', lineHeight:1.65}}>
              Conta como funciona a sua operação e mostramos exatamente como o sistema pode se encaixar na sua realidade.
            </p>
          </div>
          <div className="contact-grid">
            <div>
              <div className="channel-list">
                {[
                  { icon:<MessageSquare size={16}/>, label:"WhatsApp", detail:"Resposta em até 1 hora · Seg–Sex" },
                  { icon:<Mail size={16}/>, label:"E-mail", detail:"contato@treinoia.com.br" },
                  { icon:<Phone size={16}/>, label:"Telefone", detail:"(11) 9 9999-0000 · Horário comercial" },
                ].map((c, i) => (
                  <div className="channel g rev" key={i} style={{transitionDelay:`${i*0.1}s`}}>
                    <div className="channel-icon">{c.icon}</div>
                    <div className="channel-info">
                      <strong>{c.label}</strong>
                      <span>{c.detail}</span>
                    </div>
                    <ChevronRight size={14} />
                  </div>
                ))}
              </div>
            </div>
            <div className="form-card g rev">
              {!sent ? (
                <>
                  <div className="form-title">Enviar mensagem</div>
                  <div className="form-row">
                    <div className="form-field">
                      <label>Nome</label>
                      <input placeholder="Seu nome" value={formState.nome} onChange={e=>setFormState(p=>({...p,nome:e.target.value}))} />
                    </div>
                    <div className="form-field">
                      <label>Empresa / Studio</label>
                      <input placeholder="Nome do seu negócio" value={formState.empresa} onChange={e=>setFormState(p=>({...p,empresa:e.target.value}))} />
                    </div>
                  </div>
                  <div className="form-field">
                    <label>E-mail</label>
                    <input type="email" placeholder="seu@email.com" value={formState.email} onChange={e=>setFormState(p=>({...p,email:e.target.value}))} />
                  </div>
                  <div className="form-field">
                    <label>Como podemos ajudar?</label>
                    <textarea placeholder="Conta um pouco sobre a sua operação e o que você precisa..." value={formState.msg} onChange={e=>setFormState(p=>({...p,msg:e.target.value}))} />
                  </div>
                  <button className="form-submit" onClick={handleSubmit}>
                    Enviar mensagem <ArrowRight size={15} />
                  </button>
                </>
              ) : (
                <div className="form-success">
                  <div className="form-success-icon"><Check size={24} /></div>
                  <h4>Mensagem enviada!</h4>
                  <p>Entraremos em contato em até 1 hora nos dias úteis. Obrigado!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer>
        <div className="w">
          <div className="footer-inner">
            <div className="footer-logo">
              <div className="footer-logo-icon"><Dumbbell size={13} /></div>
              TreinoIA
            </div>
            <div className="footer-links">
              <a href="#">Privacidade</a>
              <a href="#">Termos de uso</a>
              <a href="#">Cookies</a>
            </div>
            <div className="footer-copy">© 2025 TreinoIA · Todos os direitos reservados</div>
          </div>
        </div>
      </footer>
    </>
  );
}

// Lucide icon not imported inline
function Building2({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><path d="M3 9h6"/><path d="M3 15h6"/><path d="M13 9h5"/><path d="M13 15h5"/>
    </svg>
  );
}