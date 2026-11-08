"""Flask interface for the planet quiz."""

from flask import Flask, render_template_string, request

import calculator

app = Flask(__name__)

QUESTION_ENDPOINTS = {
    "temperature": ("Frozen", "Scorching"),
    "size": ("Tiny", "Huge"),
    "mass": ("Very light", "Very heavy"),
    "gravity": ("Floaty", "Crushing"),
    "brightness": ("Dim", "Blinding"),
    "distance": ("Nearby", "Very far"),
    "star_age": ("Newborn", "Ancient"),
    "metallicity": ("Metal-poor", "Metal-rich"),
    "neighbors": ("None", "Crowded"),
    "solidity": ("Gassy", "Solid rock"),
}

QUESTIONS = {
    "temperature": "How hot do you like it?",
    "size": "How big a planet do you want?",
    "mass": "How heavy a planet?",
    "gravity": "How strong should gravity be?",
    "brightness": "How bright should the sunlight be?",
    "distance": "How far from Earth?",
    "star_age": "How old should its star be?",
    "metallicity": "How metal-rich should its star system be?",
    "neighbors": "How many neighboring planets would you like?",
    "solidity": "What should the planet be made of?",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Planet Quiz</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #080d1b; color: #eef2ff; }
    .starfield { position: fixed; inset: 0; z-index: 0; overflow: hidden;
      pointer-events: none; background:
        radial-gradient(ellipse at 9% 40%, #4634742b, transparent 27%),
        radial-gradient(ellipse at 88% 73%, #26477c33, transparent 30%),
        radial-gradient(ellipse at 72% 15%, #713d7430, transparent 22%); }
    .starfield i { --star-color: #aebeff; position: absolute; width: 4px; height: 4px;
      background: var(--star-color);
      box-shadow: 4px 0 var(--star-color), 0 4px var(--star-color),
        4px 4px var(--star-color), 8px 4px var(--star-color),
        4px 8px var(--star-color); opacity: .7; image-rendering: pixelated;
      animation: twinkle var(--twinkle-duration, 3s) steps(2, end) infinite alternate;
      animation-delay: var(--twinkle-delay, 0s); }
    .starfield i:nth-child(3n) { transform: scale(.65); --star-color: #90b4ff;
      opacity: .48; animation-delay: -1s; }
    .starfield i:nth-child(4n) { transform: scale(.8); --star-color: #d3c7ff;
      opacity: .55; animation-delay: -2s; }
    .starfield i:nth-child(8n + 1) { --star-color: #ff9a9d; }
    .starfield i:nth-child(8n + 2) { --star-color: #a4e7b0; }
    .starfield i:nth-child(8n + 3) { --star-color: #ffe39a; }
    .starfield i:nth-child(8n + 4) { --star-color: #b7a5ff; }
    .starfield i:nth-child(8n + 5) { --star-color: #ffb8e3; }
    .starfield i:nth-child(8n + 6) { --star-color: #9de8e8; }
    .starfield i:nth-child(8n + 7) { --star-color: #fff3dc; }
    .starfield .cross-star { width: 3px; height: 3px;
      box-shadow: 0 -7px var(--star-color), 0 -3px var(--star-color),
      0 3px var(--star-color), 0 7px var(--star-color),
      -7px 0 var(--star-color), -3px 0 var(--star-color),
      3px 0 var(--star-color), 7px 0 var(--star-color); }
    .starfield .cross-star:nth-child(8n + 1) { --star-color: #ff9a9d; }
    .starfield .cross-star:nth-child(8n + 2) { --star-color: #a4e7b0; }
    .starfield .cross-star:nth-child(8n + 3) { --star-color: #ffe39a; }
    .starfield .cross-star:nth-child(8n + 4) { --star-color: #b7a5ff; }
    .starfield .cross-star:nth-child(8n + 5) { --star-color: #ffb8e3; }
    .starfield .cross-star:nth-child(8n + 6) { --star-color: #9de8e8; }
    .starfield .cross-star:nth-child(8n + 7) { --star-color: #fff3dc; }
    .starfield .tiny-star { width: 2px; height: 2px; box-shadow: none; }
    .starfield i:nth-of-type(5n + 1) { animation-name: star-glow; }
    .starfield i:nth-of-type(5n + 2) { animation-name: star-flicker; }
    .starfield i:nth-of-type(5n + 4) { animation-name: star-glow; }
    .starfield i:nth-of-type(5n) { animation-name: star-flicker; }
    .space-planet { position: absolute; width: 70px; height: 70px; left: 7%;
      top: 67%; border-radius: 50%; opacity: .5;
      background: radial-gradient(circle at 30% 28%, #c7d4ff, #6678b5 42%, #30375f 75%);
      box-shadow: inset -12px -8px 18px #090e1b99, 0 0 28px #8ca4ff33; }
    .space-planet::after { content: ""; position: absolute; width: 105px; height: 24px;
      left: -18px; top: 24px; border: 2px solid #b6baff88; border-radius: 50%;
      transform: rotate(-24deg); }
    .shooting-star { position: absolute; top: 18%; right: 15%; width: 90px; height: 2px;
      transform: rotate(-32deg); opacity: .48;
      background: linear-gradient(90deg, transparent, #9fbaff); }
    .shooting-star::after { content: ""; position: absolute; right: 0; top: -2px;
      width: 6px; height: 6px; background: #e4e9ff; box-shadow: 0 0 10px #9fbaff; }
    @keyframes twinkle { to { opacity: .2; } }
    @keyframes star-glow {
      0%, 100% { opacity: .35; filter: drop-shadow(0 0 1px var(--star-color)); }
      50% { opacity: 1; filter: drop-shadow(0 0 9px var(--star-color)); }
    }
    @keyframes star-flicker {
      0%, 18%, 22%, 58%, 62%, 100% { opacity: .75; }
      20%, 60% { opacity: .18; }
      80% { opacity: 1; }
    }
    main { position: relative; z-index: 1; max-width: 820px; margin: 0 auto; padding: 48px 20px; }
    .quiz-layout { display: block; }
    .quiz-content { min-width: 0; }
    h1 { margin: 0 0 8px; font-size: clamp(2rem, 7vw, 3.4rem); }
    .intro, .hint { color: #aab5d0; }
    form, .result { margin-top: 28px; }
    fieldset, .result { border: 1px solid #293451; border-radius: 14px; padding: 20px;
      background: #111a2bf5; box-shadow: 0 10px 30px #03071366;
      backdrop-filter: blur(8px); }
    fieldset { margin: 14px 0; }
    fieldset.needs-answer { border-color: #ff9a9d; box-shadow: 0 0 0 2px #ff9a9d33; }
    legend { padding: 0 8px; font-weight: 650; }
    .percentile-scale { padding: 8px 10px 0; }
    .percentile-slider { display: block; width: 100%; height: 30px; margin: 0;
      appearance: none; -webkit-appearance: none; background: transparent; cursor: pointer; }
    .percentile-slider::-webkit-slider-runnable-track { height: 4px; border-radius: 4px;
      background: linear-gradient(90deg, #64749a, #aebeff, #64749a); }
    .percentile-slider::-moz-range-track { height: 4px; border-radius: 4px;
      background: linear-gradient(90deg, #64749a, #aebeff, #64749a); }
    .percentile-slider::-webkit-slider-thumb { width: 18px; height: 18px; margin-top: -7px;
      appearance: none; -webkit-appearance: none; border: 3px solid #e8edff;
      border-radius: 50%; background: #8299ed; box-shadow: 0 0 12px #8ca4ff99; }
    .percentile-slider::-moz-range-thumb { width: 12px; height: 12px;
      border: 3px solid #e8edff; border-radius: 50%; background: #8299ed;
      box-shadow: 0 0 12px #8ca4ff99; }
    .percentile-slider:focus-visible { outline: 2px solid #ffe39a; outline-offset: 4px; }
    .scale-endpoints { display: flex; justify-content: space-between; gap: 12px;
      margin: 9px 2px 0; color: #c8d1f3; font-size: .88rem; font-weight: 650; }
    .percentile-values { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 3px; margin: 3px -8px 0; text-align: center; }
    .percentile-values span { overflow-wrap: anywhere; color: #9eabc9;
      font-size: clamp(.62rem, 1.8vw, .76rem); font-variant-numeric: tabular-nums; }
    .percentile-values span.active { color: #e2e8ff; font-weight: 700; }
    button { border: 0; border-radius: 10px; padding: 14px 22px; background: #8ca4ff;
      color: #10172a; font-weight: 700; font-size: 1rem; cursor: pointer; }
    .message { margin: 18px 0; padding: 14px; border-radius: 10px; background: #38252d; }
    .result { background: #10182b; }
    .score { color: #b7c5ff; }
    .planet-visual { position: relative; display: grid; place-items: center; min-height: 260px;
      margin: 22px 0; overflow: hidden; border-radius: 12px;
      background: radial-gradient(ellipse at 50% 110%, #243967, #090e1b 68%); }
    .planet-art { position: relative; width: min(52vw, 220px); aspect-ratio: 1;
      border-radius: 50%; overflow: hidden;
      background: radial-gradient(circle at 32% 28%, #f6d5aa 0 4%, #d89379 20%,
        #774d76 52%, #27365f 78%, #111a38 100%);
      box-shadow: inset -26px -18px 38px #080d1bbf, 0 0 55px #a97dbc55; }
    .planet-art::before, .planet-art::after { content: ""; position: absolute;
      width: 140%; height: 24%; left: -20%; border-radius: 50%;
      background: #e7c89c44; transform: rotate(-24deg); }
    .planet-art::before { top: 34%; }
    .planet-art::after { top: 62%; background: #aac3e333; }
    .planet-image { display: block; width: 100%; max-height: 420px; object-fit: cover; }
    .planet-image[hidden] { display: none; }
    .image-caption { margin: 10px 0 22px; color: #aab5d0; font-size: .9rem; }
    .galaxy-location { margin: 26px 0 24px; padding: 18px; border: 1px solid #293451;
      border-radius: 14px; background: #0c1425; }
    .galaxy-map { position: relative; width: min(100%, 620px); aspect-ratio: 2 / 1;
      margin: 8px auto; overflow: hidden; border-radius: 12px; background: #080d1b; }
    .galaxy-map img { display: block; width: 100%; height: 100%; object-fit: cover;
      object-position: center top; }
    .galaxy-marker { position: absolute; top: var(--marker-y); transform: translateY(-50%);
      display: flex; align-items: center; gap: 4px; max-width: 42%;
      padding: 3px 6px; border: 1px solid #ff9a9d77; border-radius: 7px;
      background: #080d1be8; color: #fff0f2; font-size: clamp(8px, 2.2vw, 11px);
      font-weight: 750; line-height: 1.2; white-space: normal; overflow-wrap: anywhere;
      box-shadow: 0 1px 8px #080d1b; }
    .galaxy-marker--right { left: calc(var(--marker-x) + 10px); text-align: left; }
    .galaxy-marker--left { right: calc(100% - var(--marker-x) + 10px);
      flex-direction: row-reverse; text-align: right; }
    .galaxy-marker::before { content: "×"; flex: 0 0 auto; color: #ff6f87;
      font-size: 20px; line-height: .8; text-shadow: 0 0 8px #ff6f87; }
    .galaxy-caption { margin: 0; color: #aab5d0; font-size: .9rem; text-align: center; }
    .galaxy-coordinates { color: #c8d1f3; text-align: center; font-variant-numeric: tabular-nums; }
    li { margin: 8px 0; }
    #result { scroll-margin-top: 20px; }
    .journey { position: fixed; z-index: 3; top: 50%; right: max(18px, calc((100vw - 1180px) / 2));
      width: 76px; height: 390px; transform: translateY(-50%); display: flex;
      flex-direction: column; align-items: center; color: #bbc8ef; }
    .journey-label { margin-bottom: 10px; font-size: .7rem; font-weight: 700;
      letter-spacing: .12em; text-transform: uppercase; }
    .journey-count { margin-top: 8px; font-size: .75rem; font-variant-numeric: tabular-nums; }
    .journey-track { position: relative; flex: 1; width: 100%; }
    .journey-line, .journey-fill { position: absolute; left: 50%; width: 3px;
      transform: translateX(-50%); border-radius: 4px; }
    .journey-line { top: 18%; bottom: 18%; background: #66749b66; }
    .journey-fill { bottom: 18%; height: var(--fill-height, 0%);
      background: linear-gradient(#a9bdff, #8b73dc); box-shadow: 0 0 10px #8ca4ff88; }
    .mystery-planet { position: absolute; top: 0; left: 50%; width: 48px; height: 48px;
      transform: translateX(-50%); display: grid; place-items: center; border-radius: 50%;
      border: 2px solid #aebeff; background: radial-gradient(circle at 32% 28%, #566b9d, #202947 75%);
      color: #fff; font-size: 1.7rem; font-weight: 800;
      box-shadow: 0 0 18px #8ca4ff55, inset -7px -5px 12px #080d1b99; }
    .mystery-planet::after { content: ""; position: absolute; inset: 8px -8px;
      border: 1px solid #c2caff88; border-radius: 50%; transform: rotate(-24deg); }
    .earth { position: absolute; bottom: 0; left: 50%; width: 44px; height: 44px;
      transform: translateX(-50%); overflow: hidden; border-radius: 50%;
      border: 2px solid #8cc9f5; background: #1768a1;
      box-shadow: inset -7px -5px 10px #08152d99, 0 0 14px #55a9e533; }
    .earth-frame { position: absolute; inset: 0; width: 100%; height: 100%;
      opacity: 0; animation: earth-turn 2.4s steps(1, end) infinite; }
    .earth-frame:nth-child(1) { animation-delay: 0s; }
    .earth-frame:nth-child(2) { animation-delay: -1.8s; }
    .earth-frame:nth-child(3) { animation-delay: -1.2s; }
    .earth-frame:nth-child(4) { animation-delay: -.6s; }
    @keyframes earth-turn {
      0%, 24.9% { opacity: 1; }
      25%, 100% { opacity: 0; }
    }
    .rocket { position: absolute; z-index: 1; left: 50%; width: 42px; height: 58px;
      bottom: calc(40px + var(--rocket-travel, 0%)); transform: translate(-50%, 50%);
      filter: drop-shadow(0 0 9px #b5c5ffbb);
      transition: bottom .7s cubic-bezier(.2,.8,.2,1), left .7s cubic-bezier(.2,.8,.2,1); }
    .rocket svg { display: block; width: 100%; height: 100%; overflow: visible; }
    .rocket-flame { transform-origin: 24px 54px;
      animation: flame-flicker .18s steps(2, end) infinite alternate; }
    .journey[data-answered="0"] .rocket-flame,
    .journey--found .rocket-flame { visibility: hidden; }
    .journey--found .rocket { bottom: calc(100% - 24px); left: calc(50% + 36px);
      transform: translate(-50%, 50%) rotate(18deg); }
    @keyframes flame-flicker { to { transform: scaleY(.72); opacity: .7; } }
    @media (max-width: 1000px) {
      main { margin-left: 12px; margin-right: 92px; }
      .journey { right: 8px; width: 68px; }
    }
    @media (max-width: 480px) { main { padding: 28px 14px; } fieldset { padding: 14px; } }
    @media (max-width: 600px) {
      .journey { top: 12px; right: 10px; width: auto; height: 56px; transform: none;
        flex-direction: row; gap: 8px; padding: 5px 8px; border: 1px solid #344263;
        border-radius: 14px; background: #10182bea; backdrop-filter: blur(8px); }
      .journey-label { display: none; }
      .journey-count { margin: 0; min-width: 35px; text-align: center; font-size: .68rem; }
      .journey-track { flex: none; width: 190px; height: 100%; }
      .journey-line, .journey-fill { top: 50%; left: 18%; width: 64%; height: 3px;
        transform: translateY(-50%); }
      .journey-fill { width: var(--fill-width, 0%); }
      .mystery-planet { top: 50%; left: auto; right: 0; width: 38px; height: 38px;
        transform: translateY(-50%); font-size: 1.3rem; }
      .earth { bottom: 50%; left: 0; width: 36px; height: 36px; transform: translateY(50%); }
      .rocket { bottom: auto; left: calc(14% + var(--rocket-travel, 0%));
        top: 50%; transform: translate(-50%, -50%); width: 36px; height: 50px; }
      .journey--found .rocket { bottom: auto; left: calc(100% - 48px); top: 50%;
        transform: translate(-50%, -50%) rotate(18deg); }
      main { margin: 0; padding: 82px 14px 28px; }
      h1 { font-size: clamp(1.85rem, 8vw, 2.5rem); }
    }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      .starfield i, .earth-frame { animation: none; }
      .earth-frame:first-child { opacity: 1; }
      .earth-frame:not(:first-child) { opacity: 0; }
      .rocket { transition: none; }
    }
  </style>
</head>
<body>
<div class="starfield" aria-hidden="true">
  <i style="left:4%;top:12%;--twinkle-duration:3.7s;--twinkle-delay:-1.1s"></i>
  <i style="left:13%;top:26%;--twinkle-duration:2.4s;--twinkle-delay:-.4s"></i>
  <i style="left:7%;top:43%;--twinkle-duration:5.1s;--twinkle-delay:-3.2s"></i>
  <i style="left:17%;top:57%;--twinkle-duration:2.8s;--twinkle-delay:-1.7s"></i>
  <i style="left:3%;top:73%;--twinkle-duration:4.4s;--twinkle-delay:-.9s"></i>
  <i style="left:12%;top:89%;--twinkle-duration:2.1s;--twinkle-delay:-1.4s"></i>
  <i style="left:24%;top:8%;--twinkle-duration:5.6s;--twinkle-delay:-4.6s"></i>
  <i style="left:78%;top:11%;--twinkle-duration:3.2s;--twinkle-delay:-2.3s"></i>
  <i style="left:91%;top:20%;--twinkle-duration:2.7s;--twinkle-delay:-.6s"></i>
  <i style="left:84%;top:35%;--twinkle-duration:4.9s;--twinkle-delay:-3.8s"></i>
  <i style="left:96%;top:49%;--twinkle-duration:2.2s;--twinkle-delay:-1.8s"></i>
  <i style="left:76%;top:61%;--twinkle-duration:5.3s;--twinkle-delay:-2.6s"></i>
  <i style="left:89%;top:78%;--twinkle-duration:3.5s;--twinkle-delay:-.3s"></i>
  <i style="left:80%;top:92%;--twinkle-duration:2.6s;--twinkle-delay:-2.1s"></i>
  <i style="left:68%;top:4%;--twinkle-duration:4.1s;--twinkle-delay:-3.4s"></i>
  <i style="left:31%;top:96%;--twinkle-duration:5.8s;--twinkle-delay:-1.6s"></i>
  <i class="cross-star" style="left:21%;top:36%;--twinkle-duration:4.8s;--twinkle-delay:-2.7s"></i>
  <i class="cross-star" style="left:94%;top:67%;--twinkle-duration:2.5s;--twinkle-delay:-.7s"></i>
  <i class="cross-star" style="left:6%;top:8%;--twinkle-duration:5.4s;--twinkle-delay:-4.1s"></i>
  <i class="tiny-star" style="left:10%;top:18%;--twinkle-duration:2s;--twinkle-delay:-1.2s"></i>
  <i class="tiny-star" style="left:19%;top:82%;--twinkle-duration:4.6s;--twinkle-delay:-3.7s"></i>
  <i class="tiny-star" style="left:73%;top:27%;--twinkle-duration:2.9s;--twinkle-delay:-.2s"></i>
  <i class="tiny-star" style="left:98%;top:88%;--twinkle-duration:5.7s;--twinkle-delay:-2.9s"></i>
  <i class="tiny-star" style="left:64%;top:94%;--twinkle-duration:3.3s;--twinkle-delay:-1.9s"></i>
  <span class="space-planet"></span><span class="shooting-star"></span>
</div>
<aside class="journey{% if result is not none %} journey--found{% endif %}"
  data-answered="{{ questions|length if result is not none else 0 }}" aria-label="Quiz progress">
  <span class="journey-label">Journey</span>
  <div class="journey-track" id="journey-track" role="progressbar"
    aria-label="Questions answered" aria-valuemin="0"
    aria-valuemax="{{ questions|length }}" aria-valuenow="0"
    style="--progress: 0">
    <span class="journey-line"></span>
    <span class="journey-fill"></span>
    <span class="mystery-planet" aria-label="Mystery planet">?</span>
    <span class="rocket" aria-hidden="true">
      <svg viewBox="0 0 48 64" role="presentation">
        <path d="M24 2C14 11 11 22 12 39h24C37 22 34 11 24 2Z" fill="#e6ebff" stroke="#99adf5" stroke-width="2"/>
        <path d="M12 30 4 41l8-2m24-9 8 11-8-2" fill="#899ce0" stroke="#99adf5" stroke-width="2" stroke-linejoin="round"/>
        <circle cx="24" cy="23" r="5" fill="#71cbe6" stroke="#5268a5" stroke-width="2"/>
        <path class="rocket-flame" d="M18 39h12l-6 21Z" fill="#ffb45e"/>
        <path d="m22 41 2 11 3-11Z" fill="#fff0a5"/>
        <path d="M18 33h12" stroke="#8594d0" stroke-width="2"/>
      </svg>
    </span>
    <span class="earth" role="img" aria-label="Rotating Earth">
      <svg class="earth-frame" viewBox="0 0 64 64" aria-hidden="true">
        <defs><radialGradient id="earth-ocean-a" cx="30%" cy="28%"><stop stop-color="#69d3ef"/><stop offset=".62" stop-color="#1975b5"/><stop offset="1" stop-color="#092b62"/></radialGradient><clipPath id="earth-clip-a"><circle cx="32" cy="32" r="31"/></clipPath></defs>
        <circle cx="32" cy="32" r="31" fill="url(#earth-ocean-a)"/>
        <g clip-path="url(#earth-clip-a)" fill="#68bd78" stroke="#b1e69a" stroke-width=".7">
          <path d="m9 13 8-5 5 3 2 6-4 3 2 5-5 4-2 8-5-2-2-8-4-4 2-6-3-3Z"/>
          <path d="m20 36 7 1 4 6-2 7-4 8-4-4-1-8-4-5Z"/>
          <path d="m36 13 7-4 8 3 3 6-5 3-2 6-6 1-3 5-4-3 2-7-4-4Z"/>
          <path d="m43 36 7 1 4 5-3 7-5 5-4-5-3-7Z"/>
        </g>
        <circle cx="32" cy="32" r="31" fill="none" stroke="#a9eaff" stroke-opacity=".8" stroke-width="1.5"/>
        <path d="M5 38c16 9 38 9 54 0" fill="none" stroke="#d7f6ff" stroke-opacity=".35" stroke-width="1"/>
      </svg>
      <svg class="earth-frame" viewBox="0 0 64 64" aria-hidden="true">
        <defs><radialGradient id="earth-ocean-b" cx="30%" cy="28%"><stop stop-color="#69d3ef"/><stop offset=".62" stop-color="#1975b5"/><stop offset="1" stop-color="#092b62"/></radialGradient><clipPath id="earth-clip-b"><circle cx="32" cy="32" r="31"/></clipPath></defs>
        <circle cx="32" cy="32" r="31" fill="url(#earth-ocean-b)"/>
        <g clip-path="url(#earth-clip-b)" fill="#68bd78" stroke="#b1e69a" stroke-width=".7">
          <path d="m2 14 8-4 6 3 3 6-4 4 1 5-6 3-2 8-5-2-2-8-4-4 3-6Z"/>
          <path d="m13 38 7-2 5 5 1 7-5 9-4-4-1-8-5-3Z"/>
          <path d="m29 11 8-3 7 4 4 6-5 4-1 6-7 1-3 5-5-3 2-7-4-5Z"/>
          <path d="m37 38 7-2 6 4 2 6-5 7-5 2-4-6-4-6Z"/>
        </g>
        <circle cx="32" cy="32" r="31" fill="none" stroke="#a9eaff" stroke-opacity=".8" stroke-width="1.5"/>
        <path d="M5 38c16 9 38 9 54 0" fill="none" stroke="#d7f6ff" stroke-opacity=".35" stroke-width="1"/>
      </svg>
      <svg class="earth-frame" viewBox="0 0 64 64" aria-hidden="true">
        <defs><radialGradient id="earth-ocean-c" cx="30%" cy="28%"><stop stop-color="#69d3ef"/><stop offset=".62" stop-color="#1975b5"/><stop offset="1" stop-color="#092b62"/></radialGradient><clipPath id="earth-clip-c"><circle cx="32" cy="32" r="31"/></clipPath></defs>
        <circle cx="32" cy="32" r="31" fill="url(#earth-ocean-c)"/>
        <g clip-path="url(#earth-clip-c)" fill="#68bd78" stroke="#b1e69a" stroke-width=".7">
          <path d="m-4 16 8-4 6 3 3 6-4 4 1 5-6 3-2 8-5-2-2-8-4-4 3-6Z"/>
          <path d="m2 38 7-2 5 5 1 7-5 9-4-4-1-8-5-3Z"/>
          <path d="m20 11 8-3 7 4 4 6-5 4-1 6-7 1-3 5-5-3 2-7-4-5Z"/>
          <path d="m28 38 7-2 6 4 2 6-5 7-5 2-4-6-4-6Z"/>
          <path d="m51 17 8-3 7 5-1 7-6 4-5-4Z"/>
        </g>
        <circle cx="32" cy="32" r="31" fill="none" stroke="#a9eaff" stroke-opacity=".8" stroke-width="1.5"/>
        <path d="M5 38c16 9 38 9 54 0" fill="none" stroke="#d7f6ff" stroke-opacity=".35" stroke-width="1"/>
      </svg>
      <svg class="earth-frame" viewBox="0 0 64 64" aria-hidden="true">
        <defs><radialGradient id="earth-ocean-d" cx="30%" cy="28%"><stop stop-color="#69d3ef"/><stop offset=".62" stop-color="#1975b5"/><stop offset="1" stop-color="#092b62"/></radialGradient><clipPath id="earth-clip-d"><circle cx="32" cy="32" r="31"/></clipPath></defs>
        <circle cx="32" cy="32" r="31" fill="url(#earth-ocean-d)"/>
        <g clip-path="url(#earth-clip-d)" fill="#68bd78" stroke="#b1e69a" stroke-width=".7">
          <path d="m-15 14 8-5 6 4 3 6-4 3 2 5-6 4-2 8-5-2-2-8-4-4 3-6Z"/>
          <path d="m-5 38 7-3 5 5 1 7-5 9-4-4-1-8-5-3Z"/>
          <path d="m10 11 8-3 7 4 4 6-5 4-1 6-7 1-3 5-5-3 2-7-4-5Z"/>
          <path d="m18 38 7-2 6 4 2 6-5 7-5 2-4-6-4-6Z"/>
          <path d="m42 17 8-3 7 5-1 7-6 4-5-4Z"/>
        </g>
        <circle cx="32" cy="32" r="31" fill="none" stroke="#a9eaff" stroke-opacity=".8" stroke-width="1.5"/>
        <path d="M5 38c16 9 38 9 54 0" fill="none" stroke="#d7f6ff" stroke-opacity=".35" stroke-width="1"/>
      </svg>
    </span>
  </div>
  <span class="journey-count" id="journey-count" aria-live="polite">
    0/{{ questions|length }}
  </span>
</aside>
<main>
<div class="quiz-layout">
<div class="quiz-content">
  <h1>Find your ideal planet</h1>
  <p class="intro">Choose what you like. We’ll match your answers with confirmed exoplanet data.</p>
  {% if message %}<p class="message" role="alert">{{ message }}</p>{% endif %}
  <form method="post" id="quiz-form" novalidate>
    <p class="message" id="validation-message" role="alert" hidden>
      Please answer this question before continuing.
    </p>
    {% for column, question in questions.items() %}
    <fieldset tabindex="-1">
      <legend>{{ question }}</legend>
      <div class="percentile-scale">
        <input class="percentile-slider" type="range" min="1" max="5" step="1"
          value="{{ answers.get(column, 3) if answers else 3 }}"
          {% if answers and answers.get(column) %}name="{{ column }}"{% endif %}
          aria-label="{{ question }}: {{ endpoints[column][0] }} to {{ endpoints[column][1] }}"
          data-selected="{{ 'true' if answers and answers.get(column) else 'false' }}"
          data-column="{{ column }}">
        <div class="scale-endpoints" aria-hidden="true">
          <span>{{ endpoints[column][0] }}</span><span>{{ endpoints[column][1] }}</span>
        </div>
      </div> 
    </fieldset>
    {% endfor %}
    <button type="submit">Find my planet</button>
  </form>
  {% if result is not none %}
  <section class="result" id="result" aria-live="polite">
    <h2>Your ideal planet is {{ result.planet }}!</h2>
    <p class="score">Match score: {{ "%.0f"|format(result.score) }}/100 ·
      Data available for {{ "%.0f"|format(result.coverage * 100) }}% of your answers</p>
    <div class="planet-visual" id="planet-visual">
      <div class="planet-art" role="img"
        aria-label="Conceptual artist-style illustration of {{ result.planet }}"></div>
      <img class="planet-image" id="planet-image" alt="" hidden>
    </div>
    <p class="image-caption" id="image-caption">
      Conceptual artist-style illustration; searching NASA for a matching artist's concept.
    </p>
    <section class="galaxy-location" aria-labelledby="galaxy-title">
      <h3 id="galaxy-title">Where in the galaxy?</h3>
      {% if galactic_position %}
      <div class="galaxy-map" role="img"
        aria-label="Milky Way all-sky map with {{ result.planet }} marked by its galactic coordinates">
        <img src="{{ url_for('static', filename='milky-way-nasa.jpg') }}"
          alt="Planck all-sky view of the Milky Way in multiple infrared and radio bands">
        <span class="galaxy-marker {{ 'galaxy-marker--right' if galactic_position.map_x < 120 else 'galaxy-marker--left' }}"
          style="--marker-x: {{ galactic_position.map_x / 240 * 100 }}%; --marker-y: {{ galactic_position.map_y / 120 * 100 }}%">
          {{ result.planet }}
        </span>
      </div>
      <p class="galaxy-coordinates">
        {{ galactic_position.galaxy }} · {{ "%.2f"|format(galactic_position.galactocentric_distance_kpc) }} kpc from its center
      </p>
      <p class="galaxy-caption">
        Approx. {{ "%.1f"|format(galactic_position.distance_pc) }} parsecs from the Sun
        · galactic coordinates (l={{ "%.1f"|format(galactic_position.longitude_deg) }}°,
        b={{ "%.1f"|format(galactic_position.latitude_deg) }}°).
        Marker shows its direction in the sky, not its distance from the Sun. NASA/ESA/JPL-Caltech
        · <a href="https://photojournal.jpl.nasa.gov/catalog/PIA18913" target="_blank" rel="noopener noreferrer">image details</a>.
      </p>
      {% else %}
      <p class="galaxy-caption">
        This planet is in the Milky Way, but its host star's position coordinates are not available.
      </p>
      {% endif %}
    </section>
    <h3>Planet details</h3>
    <ul>
      {% for item in details %}
      <li><strong>{{ item.label }}</strong>: {{ item.text }}</li>
      {% endfor %}
    </ul> 
  </section>
  {% endif %}
</div>
</div>
</main>
<script>
  const progressTrack = document.getElementById("journey-track");
  const progressCount = document.getElementById("journey-count");
  const quizForm = document.getElementById("quiz-form");
  const validationMessage = document.getElementById("validation-message");
  const totalQuestions = {{ questions|length }};
  quizForm.addEventListener("submit", event => {
    const unanswered = [...quizForm.querySelectorAll("fieldset")]
      .find(fieldset => !fieldset.querySelector(".percentile-slider").dataset.selected
        || fieldset.querySelector(".percentile-slider").dataset.selected !== "true");
    if (!unanswered) return;

    event.preventDefault();
    quizForm.querySelectorAll("fieldset.needs-answer")
      .forEach(fieldset => fieldset.classList.remove("needs-answer"));
    unanswered.classList.add("needs-answer");
    validationMessage.hidden = false;
    unanswered.scrollIntoView({ behavior: "smooth", block: "start" });
    unanswered.focus({ preventScroll: true });
  });
  const updateProgress = () => {
    const sliders = [...document.querySelectorAll(".percentile-slider")];
    const answered = sliders.filter(slider => slider.dataset.selected === "true").length;
    const progress = answered / totalQuestions;
    progressTrack.closest(".journey").dataset.answered = answered;
    progressTrack.style.setProperty("--progress", progress);
    progressTrack.style.setProperty("--fill-height", `${progress * 64}%`);
    progressTrack.style.setProperty("--fill-width", `${progress * 64}%`);
    progressTrack.style.setProperty("--rocket-travel", `${progress * 68}%`);
    progressTrack.setAttribute("aria-valuenow", answered);
    progressCount.textContent = `${answered}/${totalQuestions}`;
  };
  const activateSlider = slider => {
    slider.name = slider.dataset.column;
    slider.dataset.selected = "true";
    slider.closest("fieldset").classList.remove("needs-answer");
    validationMessage.hidden = true;
    updateProgress();
  };
  document.querySelectorAll(".percentile-slider").forEach(slider => {
    slider.addEventListener("input", () => activateSlider(slider));
    slider.addEventListener("pointerup", () => activateSlider(slider));
    slider.addEventListener("change", () => activateSlider(slider));
    slider.addEventListener("keydown", event => {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
        requestAnimationFrame(() => activateSlider(slider));
      }
    });
  });
  updateProgress();
</script>
{% if result is not none %}
<script>
  document.getElementById("result").scrollIntoView({ behavior: "smooth", block: "start" });

  const planetName = {{ result.planet|tojson }};
  const image = document.getElementById("planet-image");
  const fallbackArt = document.querySelector(".planet-art");
  const caption = document.getElementById("image-caption");
  const normalize = value => value.toLowerCase().replace(/[^a-z0-9]/g, "");

  fetch(`https://images-api.nasa.gov/search?q=${encodeURIComponent(planetName)}&media_type=image`)
    .then(response => {
      if (!response.ok) throw new Error(`NASA image search returned ${response.status}`);
      return response.json();
    })
    .then(data => {
      const target = normalize(planetName);
      const match = (data.collection?.items || []).find(item => {
        const metadata = item.data?.[0] || {};
        const searchableText = normalize(`${metadata.title || ""} ${metadata.description || ""}`);
        return target.length > 0 && searchableText.includes(target);
      });
      const preview = match?.links?.find(link => link.rel === "preview")?.href;
      if (!match || !preview) {
        caption.textContent = "No matching NASA illustration was found. Showing a conceptual artist-style illustration.";
        return;
      }

      const metadata = match.data[0];
      image.alt = `NASA image: ${metadata.title || planetName}`;
      image.onload = () => {
        fallbackArt.hidden = true;
        image.hidden = false;
        caption.textContent = `NASA image: ${metadata.title || planetName}. Exoplanet visuals are artist's concepts, not direct photographs.`;
      };
      image.onerror = () => {
        caption.textContent = "The NASA image could not be displayed. Showing a conceptual artist-style illustration.";
      };
      image.src = preview;
    })
    .catch(error => {
      console.error("Could not load a NASA image for the planet result.", error);
      caption.textContent = "NASA imagery could not be loaded. Showing a conceptual artist-style illustration.";
    });
</script>
{% endif %}
</body>
</html>"""





def _render(message=None, answers=None, result=None, details=None, galactic_position=None):
    return render_template_string(
        PAGE,
        questions=QUESTIONS,
        endpoints=QUESTION_ENDPOINTS,
        message=message,
        answers=answers or {},
        result=result,
        details=details or [],
        galactic_position=galactic_position,
    )


@app.route("/", methods=["GET", "POST"])
def quiz():
    if request.method == "GET":
        return _render()

    answers = {}
    for column in calculator.QUESTIONS:
        value = request.form.get(column)
        if value not in {"1", "2", "3", "4", "5"}:
            return _render("Please answer every question from 1 to 5.")
        answers[column] = int(value)

    table = calculator.load_planet_table()
    winner = calculator.pick_planet(answers, table)
    if winner is None:
        return _render(
            "No planet has enough data for this match. Please try again later.",
            answers=answers,
        )
    return _render(
        answers=answers,
        result=winner,
        details=calculator.get_planet_values(winner, table),
        galactic_position=calculator.get_galactic_position(winner, table),
    )
