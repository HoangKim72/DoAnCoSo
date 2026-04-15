from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from .inference import load_events, official_model_cards, predict_value, summarize_events


DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phishing Checker</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700&display=swap');

    :root {
      --bg-top: #f4f7f6;
      --bg-bottom: #edf1ef;
      --surface: rgba(255, 255, 255, 0.78);
      --surface-strong: rgba(255, 255, 255, 0.92);
      --surface-deep: #f8faf9;
      --ink: #1f2a33;
      --muted: #64707d;
      --line: rgba(31, 42, 51, 0.1);
      --teal: #1c7b77;
      --teal-soft: #d8f0ec;
      --sky: #dceaf8;
      --amber: #cb6d45;
      --amber-soft: #f6d8c4;
      --rose: #c45552;
      --rose-soft: #f5d7d6;
      --olive: #66804b;
      --olive-soft: #e4ecd7;
      --shadow: 0 24px 64px rgba(34, 53, 68, 0.12);
      --shadow-soft: 0 12px 28px rgba(34, 53, 68, 0.08);
      --radius-xl: 30px;
      --radius-lg: 24px;
      --radius-md: 18px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Aptos", "Segoe UI Variable Text", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 12%, rgba(28, 123, 119, 0.15), transparent 24%),
        radial-gradient(circle at 88% 10%, rgba(203, 109, 69, 0.14), transparent 26%),
        radial-gradient(circle at 78% 92%, rgba(102, 128, 75, 0.12), transparent 24%),
        linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
    }
    .shell {
      width: min(1200px, calc(100% - 24px));
      margin: 16px auto 34px;
      animation: reveal 0.5s ease;
    }
    .hero {
      position: relative;
      overflow: hidden;
      display: grid;
      gap: 14px;
      grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
      padding: 22px 24px;
      border-radius: var(--radius-xl);
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 250, 0.78)),
        rgba(255, 255, 255, 0.82);
      border: 1px solid rgba(255, 255, 255, 0.88);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }
    .hero::after {
      content: "";
      position: absolute;
      inset: auto -40px -70px auto;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(28, 123, 119, 0.18), transparent 64%);
      pointer-events: none;
    }
    .eyebrow {
      display: inline-block;
      padding: 7px 12px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--teal-soft), var(--sky));
      color: var(--teal);
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      font-size: 12px;
    }
    h1 {
      margin: 16px 0 10px;
      font-family: "Aptos Display", "Segoe UI Variable Display", "Segoe UI", sans-serif;
      font-size: clamp(26px, 3.2vw, 38px);
      line-height: 1.02;
      letter-spacing: -0.03em;
    }
    .lead {
      max-width: 780px;
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }
    .hero-rail {
      display: grid;
      gap: 10px;
      align-content: start;
    }
    .hero-block {
      padding: 12px 14px;
      border-radius: 18px;
      background: rgba(248, 251, 250, 0.92);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .hero-kicker {
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .hero-stat {
      margin-bottom: 4px;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.03em;
    }
    .hero-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    .hero-pill,
    .soft-pill,
    .note-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(31, 42, 51, 0.08);
    }
    .hero-pill::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--teal), #47a6a0);
      box-shadow: 0 0 0 4px rgba(28, 123, 119, 0.12);
    }
    .section {
      margin-top: 14px;
      padding: 20px;
      border-radius: var(--radius-lg);
      background: var(--surface);
      border: 1px solid rgba(255, 255, 255, 0.8);
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }
    .section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 18px;
    }
    .section h2 {
      margin: 0;
      font-size: 22px;
      font-family: "Aptos Display", "Segoe UI Variable Display", "Segoe UI", sans-serif;
      letter-spacing: -0.02em;
    }
    .section-note {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    .grid {
      display: grid;
      gap: 14px;
    }
    .stats {
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    }
    .models {
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }
    .card {
      padding: 16px;
      border-radius: 18px;
      background: var(--surface-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .stat-value {
      margin-bottom: 8px;
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }
    .stat-label,
    .hint,
    .muted {
      color: var(--muted);
    }
    .stat-label {
      font-size: 13px;
      line-height: 1.5;
    }
    .stat-meta {
      margin-top: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .model-chip,
    .risk-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 11px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .model-chip {
      background: linear-gradient(135deg, var(--teal-soft), var(--sky));
      color: var(--teal);
    }
    .risk-high { background: var(--rose-soft); color: var(--rose); }
    .risk-medium { background: #f5ead7; color: #9c642c; }
    .risk-low { background: #eef1d8; color: #6e7231; }
    .risk-minimal { background: var(--olive-soft); color: var(--olive); }
    form {
      display: grid;
      gap: 14px;
    }
    .form-row {
      display: grid;
      gap: 12px;
      grid-template-columns: 180px 1fr 180px;
    }
    .field {
      padding: 14px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.62);
      border: 1px solid rgba(31, 42, 51, 0.07);
    }
    label {
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      font-weight: 700;
    }
    input,
    select,
    button {
      width: 100%;
      border-radius: 16px;
      border: 1px solid var(--line);
      padding: 13px 14px;
      font: inherit;
    }
    input,
    select {
      background: rgba(255, 255, 255, 0.88);
      color: var(--ink);
    }
    input:focus,
    select:focus {
      outline: none;
      border-color: rgba(28, 123, 119, 0.42);
      box-shadow: 0 0 0 4px rgba(28, 123, 119, 0.12);
    }
    button {
      width: auto;
      min-width: 180px;
      cursor: pointer;
      background: linear-gradient(135deg, var(--amber) 0%, #ba5538 100%);
      color: white;
      font-weight: 800;
      border: none;
      box-shadow: 0 16px 30px rgba(186, 85, 56, 0.24);
      transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 20px 36px rgba(186, 85, 56, 0.26);
    }
    .form-actions {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .micro-meta {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 13px;
    }
    #result-panel {
      display: block;
      margin-top: 8px;
      padding: 18px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: var(--surface-strong);
      box-shadow: var(--shadow-soft);
    }
    .validation-message {
      display: none;
      padding: 12px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.55;
      border: 1px solid rgba(31, 42, 51, 0.08);
      background: rgba(28, 123, 119, 0.08);
      color: var(--ink);
    }
    .validation-message.is-error {
      display: block;
      border-color: rgba(196, 85, 82, 0.22);
      background: rgba(245, 215, 214, 0.72);
      color: var(--rose);
    }
    .validation-message.is-info {
      display: block;
    }
    .switch-kind {
      margin-left: 8px;
      padding: 6px 10px;
      border: none;
      border-radius: 999px;
      background: rgba(28, 123, 119, 0.12);
      color: var(--teal);
      font: inherit;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: none;
      min-width: 0;
    }
    .check-core {
      margin-bottom: 10px;
    }
    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 4px;
    }
    .quick-button,
    .tab-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 9px 12px;
      border-radius: 999px;
      background: rgba(28, 123, 119, 0.08);
      color: var(--teal);
      border: 1px solid rgba(28, 123, 119, 0.12);
      font-size: 12px;
      font-weight: 800;
      text-decoration: none;
      box-shadow: none;
      min-width: 0;
    }
    .quick-button:hover,
    .switch-kind:hover {
      box-shadow: none;
    }
    .section-nav {
      padding: 14px 20px;
    }
    .section-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .compact-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .compact-empty {
      margin-top: 12px;
    }
    .detail-toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 12px;
      background: rgba(28, 123, 119, 0.08);
      color: var(--teal);
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
      list-style: none;
    }
    details summary::-webkit-details-marker {
      display: none;
    }
    .detail-card {
      margin-top: 10px;
      display: grid;
      gap: 8px;
      padding: 14px;
      border-radius: 16px;
      background: rgba(248, 251, 250, 0.9);
      border: 1px solid var(--line);
    }
    .model-disclosure {
      padding: 0;
    }
    .model-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px;
      cursor: pointer;
      list-style: none;
    }
    .model-summary::-webkit-details-marker {
      display: none;
    }
    .history-link {
      white-space: nowrap;
    }
    .hidden {
      display: none !important;
    }
    .result-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 14px;
    }
    .result-title {
      margin: 10px 0 0;
      font-size: 24px;
      letter-spacing: -0.03em;
    }
    .result-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    }
    .result-item {
      padding: 14px;
      border-radius: 16px;
      background: var(--surface-deep);
      border: 1px solid var(--line);
    }
    .result-item span {
      display: block;
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }
    .inline-stack {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .table-wrap {
      overflow-x: auto;
      border-radius: 22px;
      border: 1px solid var(--line);
      background: var(--surface-strong);
      box-shadow: var(--shadow-soft);
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th,
    td {
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      font-size: 14px;
    }
    th {
      background: rgba(28, 123, 119, 0.08);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    tbody tr:hover {
      background: rgba(255, 255, 255, 0.46);
    }
    tr:last-child td {
      border-bottom: none;
    }
    .table-input {
      display: inline-block;
      max-width: 320px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .empty {
      padding: 22px;
      color: var(--muted);
    }
    code {
      font-family: "Consolas", "Cascadia Code", monospace;
      background: rgba(28, 123, 119, 0.08);
      padding: 3px 8px;
      border-radius: 10px;
      word-break: break-all;
    }
    h3 {
      margin: 12px 0 10px;
      font-size: 20px;
      letter-spacing: -0.02em;
    }
    .model-card {
      position: relative;
      overflow: hidden;
    }
    .model-card::after {
      content: "";
      position: absolute;
      inset: auto -22px -34px auto;
      width: 120px;
      height: 120px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(28, 123, 119, 0.12), transparent 68%);
      pointer-events: none;
    }
    .card-top,
    .table-note {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .metric-ribbon {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 16px;
    }
    .metric-box {
      padding: 12px;
      border-radius: 16px;
      background: rgba(248, 251, 250, 0.9);
      border: 1px solid var(--line);
    }
    .metric-label {
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .metric-box strong {
      font-size: 18px;
      letter-spacing: -0.03em;
    }
    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
    }
    .tiny {
      font-size: 12px;
      color: var(--muted);
    }
    .info-tip {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .info-tip.inline {
      vertical-align: middle;
    }
    .info-dot {
      width: 22px;
      height: 22px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: rgba(28, 123, 119, 0.1);
      color: var(--teal);
      border: 1px solid rgba(28, 123, 119, 0.18);
      font-size: 12px;
      font-weight: 800;
      cursor: help;
      user-select: none;
    }
    .tooltip {
      position: absolute;
      right: 0;
      top: calc(100% + 10px);
      min-width: 220px;
      max-width: min(320px, 72vw);
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(24, 33, 40, 0.96);
      color: #eef5f3;
      font-size: 13px;
      line-height: 1.6;
      box-shadow: 0 18px 34px rgba(18, 26, 34, 0.24);
      opacity: 0;
      transform: translateY(6px);
      pointer-events: none;
      transition: opacity 0.16s ease, transform 0.16s ease;
      z-index: 20;
      white-space: normal;
    }
    .tooltip strong {
      color: white;
    }
    .tooltip-wide {
      min-width: 260px;
      max-width: min(380px, 78vw);
    }
    .info-tip:hover .tooltip,
    .info-tip:focus-within .tooltip {
      opacity: 1;
      transform: translateY(0);
    }
    .signal-list {
      display: grid;
      gap: 6px;
      margin-top: 8px;
    }
    .signal-line {
      color: rgba(238, 245, 243, 0.9);
    }
    body {
      font-family: "Be Vietnam Pro", "Inter", "Segoe UI", sans-serif;
      color: #1f2937;
      background:
        radial-gradient(circle at 12% 14%, rgba(72, 101, 122, 0.09), transparent 24%),
        radial-gradient(circle at 84% 12%, rgba(170, 123, 66, 0.08), transparent 20%),
        linear-gradient(180deg, #faf7f1 0%, #f3efe8 100%);
    }
    .shell {
      width: min(980px, calc(100% - 28px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }
    .hero {
      display: block;
      padding: 8px 0 0;
      text-align: center;
      background: transparent;
      border: none;
      box-shadow: none;
      backdrop-filter: none;
    }
    .hero::after,
    .hero-meta,
    .hero-rail,
    .lead,
    .micro-meta,
    .section-note,
    .section-nav,
    #analytics,
    #official-models,
    .section-head .info-tip {
      display: none !important;
    }
    .eyebrow {
      padding: 8px 14px;
      background: rgba(255, 255, 255, 0.76);
      border: 1px solid rgba(72, 101, 122, 0.12);
      color: #48657a;
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.08em;
    }
    h1,
    .section h2,
    h3 {
      font-family: "Plus Jakarta Sans", "Be Vietnam Pro", sans-serif;
      letter-spacing: -0.03em;
    }
    h1 {
      margin-top: 14px;
      font-size: clamp(32px, 5vw, 46px);
      font-weight: 700;
    }
    .section h2,
    h3 {
      font-weight: 600;
    }
    .hero + .section {
      max-width: 760px;
      margin: 24px auto 0;
      padding: 24px;
      border-radius: 28px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(251, 249, 245, 0.92));
      border: 1px solid rgba(255, 255, 255, 0.92);
      box-shadow: 0 20px 60px rgba(31, 41, 55, 0.08);
    }
    .hero + .section .section-head {
      display: none;
    }
    .section {
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid rgba(255, 255, 255, 0.86);
      box-shadow: 0 12px 32px rgba(31, 41, 55, 0.06);
      backdrop-filter: blur(8px);
    }
    .form-row {
      grid-template-columns: 160px 1fr 156px;
      align-items: end;
      gap: 12px;
    }
    .field {
      padding: 0;
      background: transparent;
      border: none;
    }
    label {
      margin-bottom: 8px;
      color: #667085;
      font-size: 13px;
      font-weight: 500;
      line-height: 1.6;
    }
    input,
    select {
      height: 56px;
      padding: 0 16px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.98);
      border: 1px solid rgba(31, 41, 55, 0.08);
    }
    input::placeholder {
      color: #98a2b3;
    }
    input:focus,
    select:focus {
      border-color: rgba(72, 101, 122, 0.34);
      box-shadow: 0 0 0 4px rgba(72, 101, 122, 0.10);
    }
    button {
      min-width: 0;
      border-radius: 16px;
      font-weight: 600;
      transition: transform 180ms ease-out, box-shadow 180ms ease-out, opacity 180ms ease-out;
    }
    #submit-button {
      width: 100%;
      height: 56px;
      background: linear-gradient(180deg, #3e5c70 0%, #2f4b60 100%);
      box-shadow: 0 14px 28px rgba(47, 75, 96, 0.18);
    }
    #submit-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 18px 30px rgba(47, 75, 96, 0.22);
    }
    .validation-message {
      font-size: 13px;
      font-weight: 500;
    }
    .quick-menu {
      margin-top: 4px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(246, 243, 238, 0.88);
      border: 1px solid rgba(31, 41, 55, 0.05);
    }
    .quick-summary {
      cursor: pointer;
      list-style: none;
      color: #667085;
      font-size: 13px;
      font-weight: 500;
    }
    .quick-summary::-webkit-details-marker,
    .footer-summary::-webkit-details-marker {
      display: none;
    }
    .quick-actions {
      margin-top: 12px;
      gap: 8px;
    }
    .quick-button,
    .tab-link {
      padding: 9px 12px;
      background: rgba(255, 255, 255, 0.82);
      color: #48657a;
      border: 1px solid rgba(72, 101, 122, 0.12);
      font-size: 12px;
      font-weight: 500;
    }
    #result-panel {
      min-height: 168px;
      margin-top: 18px;
      padding: 22px;
      border-radius: 22px;
      border: 1px solid rgba(31, 41, 55, 0.06);
      background: rgba(247, 244, 239, 0.88);
      box-shadow: none;
      transition: border-color 180ms ease-out, box-shadow 180ms ease-out, background 180ms ease-out;
    }
    #result-panel .empty {
      padding: 40px 12px;
      text-align: center;
    }
    #recent-events {
      margin-top: 20px;
    }
    .footer-details {
      margin-top: 18px;
      padding: 18px 20px 20px;
    }
    .footer-summary {
      cursor: pointer;
      list-style: none;
      color: #667085;
      font-size: 13px;
      font-weight: 500;
    }
    .footer-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: 1fr 1fr;
      margin-top: 16px;
    }
    .footer-card,
    .mini-stat,
    .mini-model {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(31, 41, 55, 0.06);
    }
    .mini-stats,
    .mini-models {
      display: grid;
      gap: 10px;
    }
    .mini-stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .mini-stat strong {
      display: block;
      margin-top: 6px;
      font-size: 20px;
      letter-spacing: -0.03em;
    }
    .mini-model-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .mini-model-grid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      color: #667085;
      font-size: 13px;
      line-height: 1.6;
    }
    .result-main {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }
    .result-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }
    .result-value {
      margin: 0;
      font-size: clamp(22px, 4vw, 30px);
      line-height: 1.35;
      font-weight: 600;
      letter-spacing: -0.03em;
      word-break: break-word;
      color: #1f2937;
    }
    .score-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 36px;
      padding: 0 12px;
      border-radius: 999px;
      background: rgba(72, 101, 122, 0.10);
      color: #48657a;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .result-details-simple {
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid rgba(31, 41, 55, 0.08);
    }
    .result-details-simple summary,
    .row-details summary {
      cursor: pointer;
      list-style: none;
      color: #667085;
      font-size: 13px;
      font-weight: 500;
    }
    .result-details-simple summary::-webkit-details-marker,
    .row-details summary::-webkit-details-marker {
      display: none;
    }
    .result-detail-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-top: 14px;
    }
    .result-detail-grid .result-item {
      background: rgba(246, 243, 238, 0.9);
    }
    .result-loading {
      display: grid;
      gap: 12px;
    }
    .loading-block {
      height: 14px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(72, 101, 122, 0.08), rgba(72, 101, 122, 0.16), rgba(72, 101, 122, 0.08));
      background-size: 200% 100%;
      animation: shimmer 1.2s linear infinite;
    }
    .loading-block.big {
      height: 28px;
      width: 68%;
    }
    .loading-block.mid {
      width: 46%;
    }
    @keyframes reveal {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes shimmer {
      from { background-position: 200% 0; }
      to { background-position: -200% 0; }
    }
    @media (max-width: 980px) {
      .hero { grid-template-columns: 1fr; }
      .metric-ribbon { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 860px) {
      .form-row { grid-template-columns: 1fr; }
      button { width: 100%; }
      .quick-button, .tab-link, .switch-kind { width: auto; }
      .metric-ribbon { grid-template-columns: 1fr; }
      .section-head { flex-direction: column; align-items: stretch; }
      .hero + .section,
      .section,
      .footer-details { padding: 18px; }
      .footer-grid,
      .mini-model-grid,
      .mini-stats { grid-template-columns: 1fr; }
      .mini-model-top { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <span class="eyebrow">Phishing Checker</span>
        <h1>Check domain or URL</h1>
        <p class="lead">Check domain hoặc URL nhanh.</p>
        <div class="hero-meta">
          <span class="hero-pill">Check first</span>
          <span class="hero-pill">Result card ngay dưới form</span>
        </div>
      </div>
      <div class="hero-rail">
        <div class="hero-block">
          <div class="hero-kicker">Latest Event</div>
          <div class="hero-stat" id="latest-event">{{ summary.latest_event_at or "Chưa có" }}</div>
          <div class="muted">Mốc sự kiện mới nhất đang có trong runtime log.</div>
        </div>
        <div class="hero-block">
          <div class="hero-kicker">Traffic Mix</div>
          <div class="hero-stat" id="traffic-mix">{{ summary.domain_events }} / {{ summary.url_events }}</div>
          <div class="muted">Domain events / URL events</div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2>Check</h2>
          <p class="section-note"></p>
        </div>
        <span class="info-tip">
          <span class="info-dot">i</span>
          <span class="tooltip tooltip-wide">
            <strong>Form này làm gì?</strong><br>
            Khi bấm kiểm tra, dashboard gọi <code>POST /api/ingest</code>, chạy suy luận bằng model official và ghi kết quả vào event log để bạn thấy ngay ở bảng bên dưới.
          </span>
        </span>
      </div>
      <form id="ingest-form">
        <div class="form-row check-core">
          <div class="field">
            <label for="dataset_kind">Loại input</label>
            <select id="dataset_kind" name="dataset_kind">
              <option value="domain" selected>Domain</option>
              <option value="url">URL</option>
              <option value="auto">Auto detect</option>
            </select>
          </div>
          <div class="field">
            <label for="value">Giá trị cần kiểm tra</label>
            <input id="value" name="value" placeholder="example.com" required autocomplete="off">
          </div>
          <button id="submit-button" type="submit">Kiểm tra ngay</button>
        </div>
        <div id="validation-message" class="validation-message"></div>
        <details class="quick-menu">
          <summary class="quick-summary">Tùy chọn nhanh</summary>
          <div class="quick-actions">
            <button type="button" class="quick-button" data-quick="sample-domain">Sample domain</button>
            <button type="button" class="quick-button" data-quick="sample-url">Sample URL</button>
            <button type="button" class="quick-button" data-quick="reuse-last">Dùng lại lần trước</button>
            <button type="button" class="quick-button" data-quick="clear">Xóa</button>
          </div>
        </details>
        <input id="source" name="source" type="hidden" value="ids_browser_sensor">
      </form>
      <div id="result-panel" class="muted">
        <div class="empty">Kết quả sẽ hiện ở đây sau khi bạn kiểm tra.</div>
      </div>
    </section>

    <section class="section section-nav">
      <div class="section-tabs">
        <a class="tab-link" href="#recent-events">Recent Logs</a>
        <a class="tab-link" href="#analytics">Analytics</a>
        <a class="tab-link" href="#official-models">Official Models</a>
        <a class="tab-link history-link" href="{{ url_for('dashboard_events') }}">Xem tất cả log</a>
      </div>
    </section>

    <section class="section" id="analytics">
      <div class="section-head">
        <div>
          <h2>Tổng quan</h2>
          <p class="section-note">Thu gọn còn vài chỉ số chính để không cạnh tranh với khu vực check.</p>
        </div>
      </div>
      <div class="grid stats">
        <article class="card">
          <div class="stat-value" id="summary-total">{{ summary.total_events }}</div>
          <div class="stat-label">Tổng event gần đây trong runtime log</div>
        </article>
        <article class="card">
          <div class="stat-value" id="summary-phishing">{{ summary.phishing_events }}</div>
          <div class="stat-label">Số event bị gắn nhãn phishing</div>
        </article>
        <article class="card">
          <div class="stat-value" id="summary-high">{{ summary.high_risk_events }}</div>
          <div class="stat-label">Số cảnh báo đang ở mức high</div>
        </article>
      </div>
      <div class="compact-grid" style="margin-top: 12px;">
        <article class="card">
          <div class="stat-value" id="summary-benign">{{ summary.benign_events }}</div>
          <div class="stat-label">Số event đang được gắn nhãn benign</div>
        </article>
        <article class="card">
          <div class="stat-value" id="summary-split">{{ summary.domain_events }}/{{ summary.url_events }}</div>
          <div class="stat-label">Domain events / URL events</div>
        </article>
      </div>
    </section>

    <section class="section" id="recent-events">
      <div class="section-head">
        <div>
          <h2>Recent checks</h2>
          <p class="section-note"></p>
        </div>
        <a class="tab-link history-link" href="{{ url_for('dashboard_events') }}">View all</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Loại</th>
              <th>Input</th>
              <th>Risk</th>
              <th>Kết quả</th>
              <th>Chi tiết</th>
            </tr>
          </thead>
          <tbody id="recent-events-body">
            {% if recent_events %}
            {% for event in recent_events %}
            <tr>
              <td>{{ event.received_at }}</td>
              <td><span class="model-chip">{{ event.dataset_kind }}</span></td>
              <td><code class="table-input">{{ event.normalized_value }}</code></td>
              <td><span class="risk-chip risk-{{ event.risk_level }}">{{ event.risk_level }}</span></td>
              <td>{{ event.predicted_class }}</td>
              <td>
                <details>
                  <summary class="detail-toggle">Mở chi tiết</summary>
                  <div class="detail-card">
                    <div><span class="metric-label">Score</span>{% if event.score is not none %}{{ "%.4f"|format(event.score) }}{% else %}N/A{% endif %}</div>
                    <div><span class="metric-label">Observed</span>{{ event.observed_at or event.received_at }}</div>
                    <div><span class="metric-label">Source</span>{{ event.source }}</div>
                    <div><span class="metric-label">Sensor</span>{{ event.sensor_name or "N/A" }}</div>
                    <div><span class="metric-label">Event</span>{{ event.ids_event_type }}</div>
                    <div><span class="metric-label">Flow</span>{{ event.flow_summary or "N/A" }}</div>
                    <div><span class="metric-label">Decision</span>{{ event.decision_summary }}</div>
                    {% if event.override_reason %}
                    <div><span class="metric-label">Override</span>{{ event.override_match_value or event.override_reason }}</div>
                    {% endif %}
                    <div><span class="metric-label">Model</span>{{ event.model_name }}</div>
                    <div>
                      <span class="metric-label">Signals</span>
                      {% if event.signals %}
                      <div class="signal-list">
                        {% for signal in event.signals %}
                        <div class="signal-line">{{ signal }}</div>
                        {% endfor %}
                      </div>
                      {% else %}
                      <div class="signal-list">
                        <div class="signal-line">Không có tín hiệu nổi bật.</div>
                      </div>
                      {% endif %}
                    </div>
                  </div>
                </details>
              </td>
            </tr>
            {% endfor %}
            {% endif %}
          </tbody>
        </table>
      </div>
      <div id="recent-events-empty" class="empty compact-empty {% if recent_events %}hidden{% endif %}">Chưa có sự kiện nào. Hãy gửi thử một domain hoặc URL ở form phía trên.</div>
    </section>

    <details class="section footer-details">
      <summary class="footer-summary">Insights &amp; models</summary>
      <div class="footer-grid">
        <div class="footer-card">
          <h2>Overview</h2>
          <div class="mini-stats">
            <article class="mini-stat">
              <span class="metric-label">Total</span>
              <strong id="summary-total-mini">{{ summary.total_events }}</strong>
            </article>
            <article class="mini-stat">
              <span class="metric-label">Phishing</span>
              <strong id="summary-phishing-mini">{{ summary.phishing_events }}</strong>
            </article>
            <article class="mini-stat">
              <span class="metric-label">Benign</span>
              <strong id="summary-benign-mini">{{ summary.benign_events }}</strong>
            </article>
            <article class="mini-stat">
              <span class="metric-label">High</span>
              <strong id="summary-high-mini">{{ summary.high_risk_events }}</strong>
            </article>
            <article class="mini-stat">
              <span class="metric-label">Domain / URL</span>
              <strong id="summary-split-mini">{{ summary.domain_events }}/{{ summary.url_events }}</strong>
            </article>
            <article class="mini-stat">
              <span class="metric-label">Latest</span>
              <strong id="latest-event-mini">{{ summary.latest_event_at or "Chưa có" }}</strong>
            </article>
          </div>
        </div>
        <div class="footer-card">
          <h2>Official models</h2>
          <div class="mini-models">
            {% for card in model_cards %}
            <article class="mini-model">
              <div class="mini-model-top">
                <span class="model-chip">{{ card.dataset_kind }}</span>
                <strong>{{ card.model_name }}</strong>
              </div>
              <div class="mini-model-grid">
                <div><span class="metric-label">Rows</span>{{ "{:,}".format(card.rows) }}</div>
                <div><span class="metric-label">Val PR-AUC</span>{{ "%.4f"|format(card.validation_pr_auc) }}</div>
                <div><span class="metric-label">Test PR-AUC</span>{{ "%.4f"|format(card.test_pr_auc) }}</div>
                <div><span class="metric-label">Features</span>{{ card.feature_count }}</div>
              </div>
            </article>
            {% endfor %}
          </div>
        </div>
      </div>
    </details>

    <section class="section" id="official-models">
      <div class="section-head">
        <div>
          <h2>Official Models</h2>
          <p class="section-note">Thông tin model vẫn có sẵn cho người dùng kỹ thuật, nhưng được dồn xuống phần phụ và thu gọn theo dạng disclosure.</p>
        </div>
        <span class="info-tip">
          <span class="info-dot">i</span>
          <span class="tooltip tooltip-wide">
            <strong>Ý nghĩa các metric</strong><br>
            Val PR-AUC là chất lượng trên validation, Test PR-AUC và Test F1 là kết quả trên holdout test của cấu hình official đang được load.
          </span>
        </span>
      </div>
      <div class="grid models">
        {% for card in model_cards %}
        <details class="card model-disclosure">
          <summary class="model-summary">
            <div>
              <span class="model-chip">{{ card.dataset_kind }}</span>
              <h3>{{ card.model_name }}</h3>
            </div>
            <span class="tab-link">Mở chi tiết</span>
          </summary>
          <div style="padding: 0 16px 16px;">
            <div class="metric-ribbon">
              <div class="metric-box">
                <span class="metric-label">Rows</span>
                <strong>{{ "{:,}".format(card.rows) }}</strong>
              </div>
              <div class="metric-box">
                <span class="metric-label">Val PR-AUC</span>
                <strong>{{ "%.4f"|format(card.validation_pr_auc) }}</strong>
              </div>
              <div class="metric-box">
                <span class="metric-label">Test PR-AUC</span>
                <strong>{{ "%.4f"|format(card.test_pr_auc) }}</strong>
              </div>
            </div>
            <div class="detail-card">
              <div><span class="metric-label">Variant</span><code>{{ card.variant_name }}</code></div>
              <div><span class="metric-label">Dataset</span>Benign {{ "{:,}".format(card.benign) }} | Phishing {{ "{:,}".format(card.phishing) }}</div>
              <div><span class="metric-label">Feature Count</span>{{ card.feature_count }}</div>
              <div><span class="metric-label">Test F1</span>{{ "%.4f"|format(card.test_f1) }}</div>
            </div>
          </div>
        </details>
        {% endfor %}
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById("ingest-form");
    const datasetKindField = document.getElementById("dataset_kind");
    const valueField = document.getElementById("value");
    const sourceField = document.getElementById("source");
    const submitButton = document.getElementById("submit-button");
    const resultPanel = document.getElementById("result-panel");
    const validationMessage = document.getElementById("validation-message");
    const recentEventsBody = document.getElementById("recent-events-body");
    const recentEventsEmpty = document.getElementById("recent-events-empty");
    const placeholders = {
      domain: "example.com",
      url: "https://example.com/login",
      auto: "example.com hoặc https://example.com/login",
    };
    const samples = {
      domain: "cellphones.com.vn",
      url: "https://cellphones.com.vn/",
    };

    const escapeHtml = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

    const looksLikeUrl = (value) => value.includes("://");
    const looksLikeDomain = (value) => /^(?!-)(?:[a-zA-Z0-9-]{1,63}\\.)+[a-zA-Z]{2,63}$/.test(value.trim());

    const setPlaceholder = () => {
      valueField.placeholder = placeholders[datasetKindField.value] || placeholders.auto;
    };

    const clearValidation = () => {
      validationMessage.className = "validation-message";
      validationMessage.innerHTML = "";
    };

    const showValidation = (message, kind = "info", suggestionKind = "") => {
      validationMessage.className = `validation-message is-${kind}`;
      if (suggestionKind) {
        const buttonLabel = suggestionKind === "url" ? "Chuyển sang URL" : "Chuyển sang Domain";
        validationMessage.innerHTML = `${escapeHtml(message)} <button type="button" class="switch-kind" data-kind="${escapeHtml(suggestionKind)}">${buttonLabel}</button>`;
        return;
      }
      validationMessage.textContent = message;
    };

    const validateInput = () => {
      const kind = datasetKindField.value;
      const value = valueField.value.trim();
      if (!value) {
        return { ok: false, message: "Vui lòng nhập domain hoặc URL trước khi gửi kiểm tra.", kind: "error" };
      }
      if (kind === "domain") {
        if (looksLikeUrl(value)) {
          return { ok: false, message: "Input hiện trông giống URL đầy đủ hơn là domain thuần.", kind: "error", suggestionKind: "url" };
        }
        if (!looksLikeDomain(value)) {
          return { ok: false, message: "Domain chưa đúng định dạng. Ví dụ hợp lệ: example.com", kind: "error" };
        }
      }
      if (kind === "url") {
        if (!looksLikeUrl(value)) {
          if (looksLikeDomain(value)) {
            return { ok: false, message: "Bạn đang ở chế độ URL nhưng giá trị hiện giống domain hơn.", kind: "error", suggestionKind: "domain" };
          }
          return { ok: false, message: "URL chưa đúng định dạng. Ví dụ hợp lệ: https://example.com/login", kind: "error" };
        }
      }
      return { ok: true };
    };

    const renderSignals = (signals) => {
      if (!signals.length) {
        return '<div class="signal-line">Không có tín hiệu nổi bật.</div>';
      }
      return signals.map((signal) => `<div class="signal-line">${escapeHtml(signal)}</div>`).join("");
    };

    const renderLoading = () => {
      resultPanel.style.borderColor = "rgba(72, 101, 122, 0.14)";
      resultPanel.style.boxShadow = "0 10px 24px rgba(31, 41, 55, 0.05)";
      resultPanel.style.background = "rgba(255, 255, 255, 0.94)";
      resultPanel.innerHTML = `
        <div class="result-loading">
          <div class="loading-block mid"></div>
          <div class="loading-block big"></div>
          <div class="loading-block"></div>
          <div class="loading-block"></div>
        </div>
      `;
    };

    const renderResult = (data) => {
      const signals = Array.isArray(data.signals) ? data.signals : [];
      const scoreText = data.score === null || data.score === undefined ? "N/A" : Number(data.score).toFixed(4);
      const verdictRiskClass = String(data.predicted_class || "").toLowerCase() === "phishing" ? "high" : "minimal";
      resultPanel.innerHTML = `
        <div class="result-main">
          <div>
            <div class="result-badges">
              <span class="risk-chip risk-${verdictRiskClass}">${escapeHtml(String(data.predicted_class || "").toUpperCase())}</span>
              <span class="risk-chip risk-${escapeHtml(data.risk_level)}">${escapeHtml(data.risk_level)}</span>
            </div>
            <span class="metric-label">Input đã kiểm tra</span>
            <p class="result-value">${escapeHtml(data.normalized_value)}</p>
          </div>
          <span class="score-pill">Score ${scoreText}</span>
        </div>
        <details class="result-details-simple">
          <summary>Chi tiết</summary>
          <div class="result-detail-grid">
            <div class="result-item">
              <span>Loại</span>
              <strong>${escapeHtml(data.dataset_kind || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Checked at</span>
              <strong>${escapeHtml(data.received_at || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Observed</span>
              <strong>${escapeHtml(data.observed_at || data.received_at || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Source</span>
              <strong>${escapeHtml(data.source || "ids_browser_sensor")}</strong>
            </div>
            <div class="result-item">
              <span>Sensor</span>
              <strong>${escapeHtml(data.sensor_name || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Event</span>
              <strong>${escapeHtml(data.ids_event_type || "manual_check")}</strong>
            </div>
            <div class="result-item">
              <span>Flow</span>
              <strong>${escapeHtml(data.flow_summary || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Model</span>
              <strong>${escapeHtml(data.model_name || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Variant</span>
              <strong>${escapeHtml(data.variant_name || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Decision</span>
              <strong>${escapeHtml(data.decision_summary || data.decision_mode || "model")}</strong>
            </div>
            ${data.override_reason ? `
            <div class="result-item">
              <span>Override</span>
              <strong>${escapeHtml(data.override_match_value || data.override_reason)}</strong>
            </div>` : ``}
            <div class="result-item">
              <span>Khuyến nghị</span>
              <strong>${escapeHtml(data.recommendation || "Không có")}</strong>
            </div>
            <div class="result-item" style="grid-column: 1 / -1;">
              <span>Tín hiệu</span>
              <div class="signal-list">${renderSignals(signals)}</div>
            </div>
          </div>
        </details>
      `;
      resultPanel.style.borderColor = "rgba(31, 41, 55, 0.06)";
      resultPanel.style.boxShadow = "0 10px 24px rgba(31, 41, 55, 0.06)";
      resultPanel.style.background = "rgba(255, 255, 255, 0.94)";
    };

    const renderResultError = (message) => {
      resultPanel.innerHTML = `
        <div class="result-main">
          <div>
            <div class="result-badges">
              <span class="risk-chip risk-high">ERROR</span>
            </div>
            <p class="result-value">${escapeHtml(message)}</p>
          </div>
        </div>
      `;
      resultPanel.style.borderColor = "rgba(196, 85, 82, 0.35)";
      resultPanel.style.boxShadow = "0 10px 24px rgba(196, 85, 82, 0.08)";
      resultPanel.style.background = "rgba(255, 248, 247, 0.94)";
    };

    const eventRowHtml = (event) => {
      const score = event.score === null || event.score === undefined ? "N/A" : Number(event.score).toFixed(4);
      const signals = Array.isArray(event.signals) ? event.signals : [];
      return `
        <tr>
          <td>${escapeHtml(event.received_at)}</td>
          <td><span class="model-chip">${escapeHtml(event.dataset_kind)}</span></td>
          <td><code class="table-input">${escapeHtml(event.normalized_value)}</code></td>
          <td><span class="risk-chip risk-${escapeHtml(event.risk_level)}">${escapeHtml(event.risk_level)}</span></td>
          <td>${escapeHtml(event.predicted_class)}</td>
          <td>
            <details>
              <summary class="detail-toggle">Mở chi tiết</summary>
              <div class="detail-card">
                <div><span class="metric-label">Score</span>${score}</div>
                <div><span class="metric-label">Observed</span>${escapeHtml(event.observed_at || event.received_at || "N/A")}</div>
                <div><span class="metric-label">Source</span>${escapeHtml(event.source)}</div>
                <div><span class="metric-label">Sensor</span>${escapeHtml(event.sensor_name || "N/A")}</div>
                <div><span class="metric-label">Event</span>${escapeHtml(event.ids_event_type || "manual_check")}</div>
                <div><span class="metric-label">Flow</span>${escapeHtml(event.flow_summary || "N/A")}</div>
                <div><span class="metric-label">Decision</span>${escapeHtml(event.decision_summary || event.decision_mode || "model")}</div>
                ${event.override_reason ? `<div><span class="metric-label">Override</span>${escapeHtml(event.override_match_value || event.override_reason)}</div>` : ``}
                <div><span class="metric-label">Model</span>${escapeHtml(event.model_name)}</div>
                <div>
                  <span class="metric-label">Signals</span>
                  <div class="signal-list">${renderSignals(signals)}</div>
                </div>
              </div>
            </details>
          </td>
        </tr>
      `;
    };

    const updateSummary = (summary) => {
      document.getElementById("summary-total").textContent = summary.total_events ?? 0;
      document.getElementById("summary-phishing").textContent = summary.phishing_events ?? 0;
      document.getElementById("summary-high").textContent = summary.high_risk_events ?? 0;
      document.getElementById("summary-benign").textContent = summary.benign_events ?? 0;
      document.getElementById("summary-split").textContent = `${summary.domain_events ?? 0}/${summary.url_events ?? 0}`;
      document.getElementById("latest-event").textContent = summary.latest_event_at || "Chưa có";
      document.getElementById("traffic-mix").textContent = `${summary.domain_events ?? 0} / ${summary.url_events ?? 0}`;
      document.getElementById("summary-total-mini").textContent = summary.total_events ?? 0;
      document.getElementById("summary-phishing-mini").textContent = summary.phishing_events ?? 0;
      document.getElementById("summary-high-mini").textContent = summary.high_risk_events ?? 0;
      document.getElementById("summary-benign-mini").textContent = summary.benign_events ?? 0;
      document.getElementById("summary-split-mini").textContent = `${summary.domain_events ?? 0}/${summary.url_events ?? 0}`;
      document.getElementById("latest-event-mini").textContent = summary.latest_event_at || "Chưa có";
    };

    const refreshRecentEvents = async () => {
      const response = await fetch("/api/events?limit=100");
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      const events = Array.isArray(payload.events) ? payload.events.slice(0, 5) : [];
      recentEventsBody.innerHTML = events.map(eventRowHtml).join("");
      if (events.length > 0) {
        recentEventsEmpty.classList.add("hidden");
      } else {
        recentEventsEmpty.classList.remove("hidden");
      }
      updateSummary(payload.summary || {});
    };

    const storeLastCheck = () => {
      localStorage.setItem("ids:last_kind", datasetKindField.value);
      localStorage.setItem("ids:last_value", valueField.value.trim());
    };

    const restoreLastCheck = () => {
      const lastKind = localStorage.getItem("ids:last_kind");
      const lastValue = localStorage.getItem("ids:last_value");
      if (lastKind && ["domain", "url", "auto"].includes(lastKind)) {
        datasetKindField.value = lastKind;
      }
      if (lastValue) {
        valueField.value = lastValue;
      }
      setPlaceholder();
    };

    document.querySelectorAll("[data-quick]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.quick;
        if (action === "sample-domain") {
          datasetKindField.value = "domain";
          valueField.value = samples.domain;
        } else if (action === "sample-url") {
          datasetKindField.value = "url";
          valueField.value = samples.url;
        } else if (action === "reuse-last") {
          restoreLastCheck();
        } else if (action === "clear") {
          valueField.value = "";
        }
        setPlaceholder();
        clearValidation();
        valueField.focus();
      });
    });

    document.addEventListener("click", (event) => {
      const switchButton = event.target.closest(".switch-kind");
      if (!switchButton) {
        return;
      }
      datasetKindField.value = switchButton.dataset.kind || "auto";
      setPlaceholder();
      clearValidation();
      valueField.focus();
    });

    datasetKindField.addEventListener("change", () => {
      setPlaceholder();
      const state = validateInput();
      if (!state.ok) {
        showValidation(state.message, state.kind, state.suggestionKind || "");
      } else {
        clearValidation();
      }
    });

    valueField.addEventListener("input", () => {
      const state = validateInput();
      if (!state.ok) {
        showValidation(state.message, state.kind, state.suggestionKind || "");
      } else {
        clearValidation();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const state = validateInput();
      if (!state.ok) {
        showValidation(state.message, state.kind, state.suggestionKind || "");
        valueField.focus();
        return;
      }

      clearValidation();
      submitButton.disabled = true;
      renderLoading();

      try {
        const response = await fetch("/api/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dataset_kind: datasetKindField.value,
            value: valueField.value.trim(),
            source: sourceField.value,
          }),
        });
        const data = await response.json();
        if (!response.ok) {
          renderResultError(data.error || "Lỗi không xác định.");
          return;
        }
        renderResult(data);
        storeLastCheck();
        await refreshRecentEvents();
      } catch (error) {
        renderResultError("Không kết nối được tới dashboard API.");
      } finally {
        submitButton.disabled = false;
      }
    });

    restoreLastCheck();
    setPlaceholder();
  </script>
</body>
</html>
"""


EVENT_HISTORY_TEMPLATE = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Check History</title>
  <style>
    :root{--bg:#f4efe6;--surface:#fffdf9;--muted:#62707c;--ink:#1f2933;--teal:#176f68;--teal-soft:#d9ece8;--amber-soft:#f6dfca;--rose:#b9524b;--rose-soft:#f3d7d4;--olive-soft:#dde7d5;--line:rgba(31,41,51,.1);--shadow:0 18px 48px rgba(31,41,51,.11)}
    *{box-sizing:border-box}body{margin:0;font-family:"Aptos","Segoe UI Variable Text","Segoe UI",sans-serif;color:var(--ink);background:linear-gradient(180deg,var(--bg),#ebe3d5)}code{font-family:"Cascadia Code","Consolas",monospace;background:rgba(23,111,104,.08);padding:3px 8px;border-radius:10px;word-break:break-all}
    .history{width:min(1220px,calc(100% - 28px));margin:18px auto 36px;padding:22px;background:rgba(255,253,249,.94);border:1px solid rgba(255,255,255,.86);box-shadow:var(--shadow);border-radius:28px}.back{display:inline-flex;align-items:center;gap:8px;margin-bottom:14px;color:var(--teal);font-size:13px;font-weight:800;text-decoration:none}h1{margin:0 0 8px;font-family:"Aptos Display","Segoe UI Variable Display","Segoe UI",sans-serif;font-size:clamp(28px,3.2vw,40px);letter-spacing:-.03em}p{margin:0 0 18px;color:var(--muted);line-height:1.6}.table-wrap{overflow-x:auto;border-radius:20px;border:1px solid var(--line);background:#fff}table{width:100%;border-collapse:collapse}th,td{padding:14px 16px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}th{background:rgba(23,111,104,.06);color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}tr:last-child td{border-bottom:none}.chip,.risk{display:inline-flex;align-items:center;gap:8px;padding:7px 11px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.chip{background:linear-gradient(135deg,var(--teal-soft),rgba(255,255,255,.9));color:#124f4b}.chip.url{background:linear-gradient(135deg,var(--amber-soft),rgba(255,255,255,.92));color:#8d4c1f}.risk.high{background:var(--rose-soft);color:var(--rose)}.risk.medium{background:#f5ead7;color:#9c642c}.risk.low{background:var(--olive-soft);color:#5f7138}.risk.minimal{background:rgba(23,111,104,.12);color:var(--teal)}.truncate{display:inline-block;max-width:360px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.empty{padding:18px;border-radius:16px;background:#f7f2ea;color:var(--muted)}
  </style>
</head>
<body>
  <main class="history">
    <a class="back" href="{{ url_for('dashboard') }}">← Quay lại checker</a>
    <h1>Check History</h1>
    <p>Xem lại toàn bộ log chi tiết mà không làm trang chính bị quá dài.</p>
    {% if events %}
    <div class="table-wrap">
      <table>
        <thead><tr><th>Thời gian</th><th>Observed</th><th>Loại</th><th>Input</th><th>Score</th><th>Risk</th><th>Kết quả</th><th>Context</th><th>Decision</th><th>Model</th></tr></thead>
        <tbody>
          {% for event in events %}
          <tr>
            <td>{{ event.received_at }}</td>
            <td>{{ event.observed_at or event.received_at }}</td>
            <td><span class="chip {% if event.dataset_kind == 'url' %}url{% endif %}">{{ event.dataset_kind }}</span></td>
            <td><code class="truncate">{{ event.normalized_value }}</code></td>
            <td>{% if event.score is not none %}{{ "%.4f"|format(event.score) }}{% else %}N/A{% endif %}</td>
            <td><span class="risk {{ event.risk_level }}">{{ event.risk_level }}</span></td>
            <td>{{ event.predicted_class }}</td>
            <td>
              <div>{{ event.source }}</div>
              {% if event.sensor_name %}<div class="muted">{{ event.sensor_name }}</div>{% endif %}
              <div class="muted">{{ event.ids_event_type }}</div>
              {% if event.flow_summary %}<div class="muted">{{ event.flow_summary }}</div>{% endif %}
            </td>
            <td>
              <div>{{ event.decision_summary }}</div>
              {% if event.override_reason %}<div class="muted">{{ event.override_match_value or event.override_reason }}</div>{% endif %}
            </td>
            <td>{{ event.model_name }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty">Chưa có event nào trong runtime log.</div>
    {% endif %}
  </main>
</body>
</html>
"""


def error_response(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


def parse_request_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return request.form.to_dict(flat=True)


def _clean_metadata_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_endpoint(ip_value: Any, port_value: Any) -> str:
    ip_text = _clean_metadata_value(ip_value)
    port_text = _clean_metadata_value(port_value)
    if not ip_text:
        return ""
    if port_text:
        return f"{ip_text}:{port_text}"
    return ip_text


def decorate_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    sensor_name = (
        _clean_metadata_value(metadata.get("sensor_name"))
        or _clean_metadata_value(metadata.get("parser_format"))
    )
    ids_event_type = (
        _clean_metadata_value(metadata.get("ids_event_type"))
        or _clean_metadata_value(metadata.get("parser_format"))
        or "manual_check"
    )
    observed_at = (
        _clean_metadata_value(metadata.get("observed_at"))
        or _clean_metadata_value(metadata.get("timestamp"))
    )
    flow_summary = " -> ".join(
        part
        for part in [
            _compact_endpoint(metadata.get("src_ip"), metadata.get("src_port")),
            _compact_endpoint(metadata.get("dest_ip"), metadata.get("dest_port")),
        ]
        if part
    )

    decorated = dict(event)
    decorated["metadata"] = metadata
    decorated["sensor_name"] = sensor_name
    decorated["ids_event_type"] = ids_event_type
    decorated["observed_at"] = observed_at
    decorated["flow_summary"] = flow_summary
    decorated["context_summary"] = " | ".join(
        part for part in [sensor_name or decorated.get("source", ""), ids_event_type, flow_summary] if part
    )
    decorated["decision_summary"] = (
        "model + curated benign override"
        if decorated.get("decision_mode") == "model_plus_curated_benign_override"
        else "model"
    )
    return decorated


def decorate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [decorate_event(event) for event in events]


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def root():
        return redirect(url_for("dashboard"))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "models": official_model_cards()})

    @app.get("/dashboard")
    def dashboard():
        events = decorate_events(load_events(limit=100))
        summary = summarize_events(events)
        return render_template_string(
            DASHBOARD_TEMPLATE,
            recent_events=events[:5],
            summary=summary,
            model_cards=official_model_cards(),
        )

    @app.get("/dashboard/events")
    def dashboard_events():
        return render_template_string(
            EVENT_HISTORY_TEMPLATE,
            events=decorate_events(load_events(limit=500)),
        )

    @app.get("/api/events")
    def api_events():
        try:
            limit = int(request.args.get("limit", 100))
        except ValueError:
            return error_response("`limit` must be an integer.")
        events = decorate_events(load_events(limit=max(1, min(limit, 500))))
        return jsonify({"events": events, "summary": summarize_events(events)})

    @app.post("/api/predict")
    def api_predict():
        payload = parse_request_payload()
        value = str(payload.get("value", "")).strip()
        if not value:
            return error_response("`value` is required.")
        requested_kind = str(payload.get("dataset_kind", "auto")).strip().lower() or "auto"
        if requested_kind not in {"auto", "domain", "url"}:
            return error_response("`dataset_kind` must be one of: auto, domain, url.")
        source = str(payload.get("source", "ids_sensor")).strip() or "ids_sensor"
        try:
            result = predict_value(
                value=value,
                dataset_kind=requested_kind,
                source=source,
                persist=False,
            )
        except Exception as exc:  # pragma: no cover - exercised in manual flow
            return error_response(str(exc), 400)
        return jsonify(decorate_event(result))

    @app.post("/api/ingest")
    def api_ingest():
        payload = parse_request_payload()
        value = str(payload.get("value", "")).strip()
        if not value:
            return error_response("`value` is required.")
        requested_kind = str(payload.get("dataset_kind", "auto")).strip().lower() or "auto"
        if requested_kind not in {"auto", "domain", "url"}:
            return error_response("`dataset_kind` must be one of: auto, domain, url.")
        source = str(payload.get("source", "ids_sensor")).strip() or "ids_sensor"
        metadata = payload.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}
        try:
            result = predict_value(
                value=value,
                dataset_kind=requested_kind,
                source=source,
                persist=True,
                metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover - exercised in manual flow
            return error_response(str(exc), 400)
        return jsonify(decorate_event(result)), 201

    return app
