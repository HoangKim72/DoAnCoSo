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
  <title>Phishing Checker Dashboard</title>
  <style>
    :root {
      --font-body: "Aptos", "Segoe UI Variable Text", "Segoe UI", sans-serif;
      --font-heading: "Bahnschrift SemiBold", "Trebuchet MS", sans-serif;
      --radius-xl: 30px;
      --radius-lg: 24px;
      --radius-md: 18px;
      --radius-sm: 14px;
      --shadow-strong: 0 28px 90px rgba(20, 28, 31, 0.16);
      --shadow-soft: 0 18px 40px rgba(20, 28, 31, 0.10);
      --transition: 180ms ease;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-body);
      background:
        radial-gradient(circle at 14% 12%, var(--orb-a), transparent 24%),
        radial-gradient(circle at 84% 10%, var(--orb-b), transparent 20%),
        radial-gradient(circle at 78% 92%, var(--orb-c), transparent 22%),
        linear-gradient(180deg, var(--bg-main) 0%, var(--bg-alt) 100%);
      color: var(--text-main);
      transition: background 240ms ease, color 240ms ease;
    }

    body[data-theme="light"] {
      --bg-main: #edf7ef;
      --bg-alt: #f7fbf7;
      --orb-a: rgba(116, 177, 132, 0.22);
      --orb-b: rgba(242, 190, 124, 0.18);
      --orb-c: rgba(103, 148, 195, 0.14);
      --text-main: #17241f;
      --text-soft: #5f7168;
      --line: rgba(36, 64, 50, 0.10);
      --line-strong: rgba(36, 64, 50, 0.18);
      --sidebar-bg: rgba(223, 241, 227, 0.86);
      --sidebar-border: rgba(78, 128, 93, 0.16);
      --panel-bg: rgba(255, 255, 255, 0.68);
      --panel-strong: rgba(255, 255, 255, 0.92);
      --panel-check: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(240, 249, 243, 0.90));
      --panel-reports: linear-gradient(145deg, rgba(250, 254, 251, 0.96), rgba(240, 248, 255, 0.90));
      --panel-stats: linear-gradient(145deg, rgba(246, 252, 248, 0.96), rgba(236, 247, 243, 0.92));
      --panel-settings: linear-gradient(145deg, rgba(252, 255, 252, 0.96), rgba(245, 249, 247, 0.92));
      --accent: #4f8f67;
      --accent-strong: #2f6a48;
      --accent-soft: rgba(79, 143, 103, 0.14);
      --accent-soft-strong: rgba(79, 143, 103, 0.22);
      --safe: #3f8a58;
      --safe-soft: rgba(63, 138, 88, 0.14);
      --warn: #bf8537;
      --warn-soft: rgba(191, 133, 55, 0.16);
      --danger: #c55b72;
      --danger-soft: rgba(197, 91, 114, 0.14);
      --purple: #6f66b8;
      --purple-soft: rgba(111, 102, 184, 0.14);
      --blue: #4b84b6;
      --blue-soft: rgba(75, 132, 182, 0.14);
      --card-fill: rgba(255, 255, 255, 0.88);
    }

    body[data-theme="dark"] {
      --bg-main: #110f1d;
      --bg-alt: #19142b;
      --orb-a: rgba(125, 87, 209, 0.20);
      --orb-b: rgba(58, 130, 188, 0.14);
      --orb-c: rgba(180, 79, 121, 0.12);
      --text-main: #f4f3ff;
      --text-soft: #b3b6ca;
      --line: rgba(255, 255, 255, 0.10);
      --line-strong: rgba(255, 255, 255, 0.16);
      --sidebar-bg: rgba(18, 15, 33, 0.88);
      --sidebar-border: rgba(135, 119, 201, 0.18);
      --panel-bg: rgba(23, 20, 39, 0.76);
      --panel-strong: rgba(25, 22, 42, 0.95);
      --panel-check: linear-gradient(145deg, rgba(73, 52, 116, 0.95), rgba(35, 29, 65, 0.95));
      --panel-reports: linear-gradient(145deg, rgba(28, 39, 78, 0.95), rgba(23, 26, 56, 0.95));
      --panel-stats: linear-gradient(145deg, rgba(19, 56, 63, 0.95), rgba(18, 34, 42, 0.95));
      --panel-settings: linear-gradient(145deg, rgba(63, 27, 56, 0.95), rgba(31, 18, 35, 0.95));
      --accent: #8fd59d;
      --accent-strong: #d3ffe1;
      --accent-soft: rgba(143, 213, 157, 0.16);
      --accent-soft-strong: rgba(143, 213, 157, 0.28);
      --safe: #76d58f;
      --safe-soft: rgba(118, 213, 143, 0.16);
      --warn: #f0c06c;
      --warn-soft: rgba(240, 192, 108, 0.18);
      --danger: #ff8da8;
      --danger-soft: rgba(255, 141, 168, 0.18);
      --purple: #b9a5ff;
      --purple-soft: rgba(185, 165, 255, 0.18);
      --blue: #85bfff;
      --blue-soft: rgba(133, 191, 255, 0.18);
      --card-fill: rgba(31, 27, 49, 0.92);
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    button,
    input,
    select,
    textarea {
      font: inherit;
    }

    code {
      font-family: "Consolas", "Cascadia Code", monospace;
      background: rgba(255, 255, 255, 0.18);
      padding: 2px 8px;
      border-radius: 10px;
      word-break: break-all;
    }

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(10, 9, 20, 0.44);
      opacity: 0;
      pointer-events: none;
      transition: opacity 220ms ease;
      z-index: 40;
    }

    .sidebar-backdrop.is-visible {
      opacity: 1;
      pointer-events: auto;
    }

    .app-shell {
      width: min(1480px, calc(100% - 28px));
      margin: 16px auto 32px;
      display: grid;
      grid-template-columns: 224px minmax(0, 1fr);
      gap: 20px;
      align-items: start;
    }

    .sidebar {
      position: sticky;
      top: 16px;
      min-height: calc(100vh - 32px);
      padding: 16px;
      border-radius: var(--radius-xl);
      background: var(--sidebar-bg);
      border: 1px solid var(--sidebar-border);
      backdrop-filter: blur(18px);
      box-shadow: var(--shadow-strong);
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 14px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 8px 4px;
    }

    .brand-mark {
      width: 46px;
      height: 46px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      background: linear-gradient(145deg, var(--accent-soft-strong), rgba(255, 255, 255, 0.18));
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: var(--accent-strong);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
    }

    .brand-kicker,
    .eyebrow,
    .section-kicker,
    .small-label {
      margin: 0;
      font-size: 12px;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      color: var(--text-soft);
    }

    .brand h1 {
      margin: 4px 0 0;
      font-family: var(--font-heading);
      font-size: 19px;
      letter-spacing: -0.02em;
    }

    .sidebar-intro {
      padding: 16px;
      border-radius: var(--radius-lg);
      background: linear-gradient(145deg, var(--accent-soft), rgba(255, 255, 255, 0.10));
      border: 1px solid var(--line);
      color: var(--text-main);
    }

    .sidebar-intro p {
      margin: 8px 0 0;
      color: var(--text-soft);
      line-height: 1.55;
      font-size: 14px;
    }

    .sidebar-nav {
      display: grid;
      gap: 10px;
      align-content: start;
    }

    .nav-link {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      border-radius: 16px;
      color: var(--text-soft);
      border: 1px solid transparent;
      transition: background var(--transition), transform var(--transition), color var(--transition), border-color var(--transition);
    }

    .nav-link:hover,
    .nav-link:focus-visible {
      background: var(--accent-soft);
      color: var(--text-main);
      border-color: var(--line);
      transform: translateX(2px);
      outline: none;
    }

    .nav-link.is-active {
      background: linear-gradient(145deg, var(--accent-soft-strong), rgba(255, 255, 255, 0.08));
      color: var(--accent-strong);
      border-color: rgba(255, 255, 255, 0.16);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }

    .nav-icon {
      width: 36px;
      height: 36px;
      flex-shrink: 0;
      display: grid;
      place-items: center;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid var(--line);
      color: currentColor;
    }

    .nav-text {
      display: grid;
      gap: 2px;
    }

    .nav-text strong {
      font-size: 15px;
      color: currentColor;
    }

    .nav-text span {
      display: none;
    }

    .sidebar-foot {
      display: grid;
      gap: 12px;
    }

    .status-card,
    .ghost-card {
      padding: 16px;
      border-radius: var(--radius-lg);
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }

    .status-grid {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .status-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 14px;
      color: var(--text-soft);
    }

    .status-row strong {
      color: var(--text-main);
      font-weight: 700;
    }

    .ghost-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 16px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-main);
      font-weight: 700;
      transition: background var(--transition), transform var(--transition);
    }

    .ghost-link:hover {
      background: var(--accent-soft);
      transform: translateY(-1px);
    }

    .main {
      min-width: 0;
      display: grid;
      gap: 24px;
    }

    .topbar {
      position: sticky;
      top: 16px;
      z-index: 20;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 18px;
      border-radius: var(--radius-xl);
      background: var(--panel-bg);
      border: 1px solid var(--line);
      backdrop-filter: blur(18px);
      box-shadow: var(--shadow-soft);
    }

    .topbar-left,
    .topbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .menu-button,
    .icon-button,
    .theme-toggle,
    .row-button,
    .secondary-button,
    .primary-button,
    .quick-button,
    .modal-close {
      border: none;
      cursor: pointer;
      transition: transform var(--transition), box-shadow var(--transition), background var(--transition), opacity var(--transition);
    }

    .icon-button,
    .menu-button {
      width: 46px;
      height: 46px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 16px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      color: var(--text-main);
      box-shadow: var(--shadow-soft);
    }

    .icon-button:hover,
    .menu-button:hover,
    .theme-toggle:hover,
    .row-button:hover,
    .secondary-button:hover,
    .primary-button:hover,
    .quick-button:hover,
    .modal-close:hover {
      transform: translateY(-1px);
    }

    .menu-button {
      display: none;
    }

    .theme-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 46px;
      height: 46px;
      padding: 0;
      border-radius: 16px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      color: var(--text-main);
      box-shadow: var(--shadow-soft);
    }

    .theme-icon {
      font-size: 20px;
      font-weight: 700;
    }

    .theme-toggle svg {
      width: 18px;
      height: 18px;
    }

    .topbar-title h2 {
      margin: 0;
      font-family: var(--font-heading);
      font-size: clamp(22px, 3vw, 30px);
      letter-spacing: -0.03em;
    }

    .topbar-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--panel-strong);
      color: var(--text-soft);
      font-size: 13px;
      font-weight: 700;
      box-shadow: var(--shadow-soft);
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(79, 143, 103, 0.14);
    }

    .page-section {
      padding: 24px;
      border-radius: var(--radius-xl);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-strong);
      backdrop-filter: blur(18px);
    }

    .section-check {
      background: var(--panel-check);
    }

    .section-reports {
      background: var(--panel-reports);
    }

    .section-stats {
      background: var(--panel-stats);
    }

    .section-settings {
      background: var(--panel-settings);
    }

    .section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .section-head h3 {
      margin: 8px 0 0;
      font-family: var(--font-heading);
      font-size: clamp(22px, 3vw, 28px);
      letter-spacing: -0.03em;
    }

    .section-note {
      margin: 10px 0 0;
      max-width: 760px;
      color: var(--text-soft);
      line-height: 1.65;
      font-size: 14px;
    }

    .section-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.10);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 700;
    }

    .section-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
      flex-wrap: wrap;
    }

    .split-checker {
      display: grid;
      grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1.1fr);
      gap: 20px;
    }

    .split-checker.manual-hidden {
      grid-template-columns: 1fr;
    }

    .split-checker.manual-hidden .form-card {
      display: none;
    }

    .panel {
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-soft);
      padding: 22px;
    }

    .intro-card {
      display: grid;
      gap: 18px;
      align-content: start;
      background:
        linear-gradient(145deg, var(--accent-soft), rgba(255, 255, 255, 0.08)),
        var(--panel-strong);
    }

    .intro-title {
      margin: 12px 0 0;
      font-family: var(--font-heading);
      font-size: clamp(28px, 4vw, 38px);
      line-height: 1.05;
      letter-spacing: -0.04em;
    }

    .intro-copy {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.7;
      font-size: 15px;
    }

    .feature-list {
      display: grid;
      gap: 12px;
    }

    .feature-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 12px 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .feature-dot {
      width: 12px;
      height: 12px;
      margin-top: 5px;
      border-radius: 999px;
      background: linear-gradient(145deg, var(--accent), var(--blue));
      flex-shrink: 0;
    }

    .feature-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 15px;
    }

    .feature-item span {
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.55;
    }

    .intro-mini-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .mini-stat {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid var(--line);
    }

    .mini-stat strong {
      display: block;
      margin-top: 8px;
      font-size: 24px;
      font-family: var(--font-heading);
      letter-spacing: -0.03em;
    }

    .mini-stat span {
      font-size: 13px;
      color: var(--text-soft);
    }

    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .quick-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.18);
      color: var(--text-main);
      font-weight: 700;
      border: 1px solid var(--line);
    }

    .quick-button:hover {
      background: var(--accent-soft);
    }

    .realtime-card {
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .panel-title-row {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }

    .panel-title-row h4 {
      margin: 6px 0 0;
      font-family: var(--font-heading);
      font-size: 24px;
      letter-spacing: -0.03em;
    }

    .risk-chart {
      height: 230px;
      padding: 16px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.04)),
        var(--card-fill);
      border: 1px solid var(--line);
      overflow: hidden;
    }

    .score-line-chart {
      width: 100%;
      height: 100%;
      display: block;
    }

    .chart-axis,
    .chart-grid {
      stroke: var(--line-strong);
      stroke-width: 1;
    }

    .chart-grid {
      opacity: 0.55;
    }

    .chart-line {
      fill: none;
      stroke: var(--danger);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .chart-area {
      fill: var(--danger-soft);
      opacity: 0.45;
    }

    .chart-point {
      fill: var(--panel-strong);
      stroke: var(--danger);
      stroke-width: 2;
    }

    .chart-label {
      fill: var(--text-soft);
      font-size: 12px;
      font-weight: 700;
    }

    .realtime-feed {
      max-height: 260px;
      overflow: auto;
      display: grid;
      gap: 10px;
      padding-right: 4px;
    }

    .feed-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .feed-value {
      min-width: 0;
      display: grid;
      gap: 4px;
    }

    .feed-value strong {
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      font-size: 14px;
    }

    .feed-value span {
      color: var(--text-soft);
      font-size: 12px;
    }

    .feed-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    .feed-check-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      padding: 0 12px;
      border-radius: 999px;
      border: 1px solid rgba(75, 132, 182, 0.24);
      background: var(--blue-soft);
      color: var(--blue);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      white-space: nowrap;
      transition: transform var(--transition), background var(--transition), color var(--transition);
    }

    .feed-check-button:hover,
    .feed-check-button:focus-visible {
      background: var(--blue);
      color: #ffffff;
      transform: translateY(-1px);
      outline: none;
    }

    .form-card {
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 190px minmax(0, 1fr);
      gap: 14px;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field label {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-soft);
    }

    .field input,
    .field select,
    .field textarea {
      width: 100%;
      min-height: 56px;
      padding: 0 16px;
      border-radius: 18px;
      border: 1px solid var(--line-strong);
      background: var(--card-fill);
      color: var(--text-main);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
      transition: border-color var(--transition), box-shadow var(--transition), background var(--transition);
    }

    .field textarea {
      height: 56px;
      padding: 16px;
      line-height: 1.5;
      resize: none;
      overflow: hidden;
      overflow-wrap: anywhere;
    }

    .field input::placeholder,
    .field textarea::placeholder {
      color: var(--text-soft);
    }

    .field input:focus,
    .field select:focus,
    .field textarea:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(79, 143, 103, 0.12);
    }

    .form-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .form-note {
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.6;
    }

    .primary-button,
    .secondary-button,
    .row-button,
    .modal-close {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border-radius: 18px;
      padding: 13px 18px;
      font-weight: 800;
    }

    .primary-button {
      background: linear-gradient(145deg, var(--accent), #71ad7e);
      color: #ffffff;
      box-shadow: 0 18px 36px rgba(79, 143, 103, 0.24);
    }

    .primary-button[disabled] {
      opacity: 0.72;
      cursor: wait;
    }

    .secondary-button,
    .row-button,
    .modal-close {
      background: rgba(255, 255, 255, 0.14);
      color: var(--text-main);
      border: 1px solid var(--line);
    }

    .validation-message {
      display: none;
      padding: 14px 16px;
      border-radius: 18px;
      font-size: 14px;
      line-height: 1.6;
      border: 1px solid transparent;
    }

    .validation-message.is-visible {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .validation-message.is-error {
      background: var(--danger-soft);
      border-color: rgba(197, 91, 114, 0.24);
      color: var(--danger);
    }

    .validation-message.is-info {
      background: var(--blue-soft);
      border-color: rgba(75, 132, 182, 0.24);
      color: var(--blue);
    }

    .result-panel {
      min-height: 288px;
      display: grid;
      align-items: stretch;
    }

    .state-card {
      width: 100%;
      height: 100%;
      padding: 22px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px dashed var(--line-strong);
      display: grid;
      gap: 16px;
      align-content: center;
    }

    .state-card h4 {
      margin: 0;
      font-family: var(--font-heading);
      font-size: 24px;
      letter-spacing: -0.03em;
    }

    .state-card p {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.7;
      font-size: 14px;
    }

    .result-shell {
      padding: 22px;
      border-radius: 24px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }

    .result-shell.is-danger {
      background: linear-gradient(145deg, var(--danger-soft), rgba(255, 255, 255, 0.06)), var(--panel-strong);
    }

    .result-shell.is-safe {
      background: linear-gradient(145deg, var(--safe-soft), rgba(255, 255, 255, 0.06)), var(--panel-strong);
    }

    .result-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
    }

    .result-top h4 {
      margin: 12px 0 10px;
      font-family: var(--font-heading);
      font-size: clamp(24px, 3vw, 30px);
      letter-spacing: -0.04em;
    }

    .result-summary {
      color: var(--text-soft);
      line-height: 1.65;
      font-size: 14px;
    }

    .score-card {
      min-width: 120px;
      padding: 14px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid var(--line);
      text-align: center;
      flex-shrink: 0;
    }

    .score-card strong {
      display: block;
      font-family: var(--font-heading);
      font-size: 30px;
      line-height: 1;
    }

    .score-card span {
      display: block;
      margin-top: 8px;
      color: var(--text-soft);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .result-side {
      display: flex;
      align-items: stretch;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
      flex-shrink: 0;
    }

    .result-open-button {
      min-width: 112px;
      min-height: 100%;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .badge-safe {
      background: var(--safe-soft);
      color: var(--safe);
      border-color: rgba(63, 138, 88, 0.18);
    }

    .badge-danger {
      background: var(--danger-soft);
      color: var(--danger);
      border-color: rgba(197, 91, 114, 0.18);
    }

    .badge-warning {
      background: var(--warn-soft);
      color: var(--warn);
      border-color: rgba(191, 133, 55, 0.18);
    }

    .badge-neutral {
      background: rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      border-color: var(--line);
    }

    .badge-purple {
      background: var(--purple-soft);
      color: var(--purple);
      border-color: rgba(111, 102, 184, 0.18);
    }

    .badge-blue {
      background: var(--blue-soft);
      color: var(--blue);
      border-color: rgba(75, 132, 182, 0.18);
    }

    .result-grid,
    .modal-grid,
    .stats-grid,
    .insights-grid,
    .settings-grid,
    .model-grid {
      display: grid;
      gap: 14px;
    }

    .result-grid,
    .modal-grid {
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      margin-top: 18px;
    }

    .result-item,
    .metric-card,
    .insight-card,
    .setting-card,
    .model-card,
    .modal-item {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .result-item span,
    .metric-card span,
    .insight-card span,
    .setting-card span,
    .model-card span,
    .modal-item span {
      display: block;
      margin-bottom: 8px;
      color: var(--text-soft);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .result-item strong,
    .metric-card strong,
    .insight-card strong,
    .setting-card strong,
    .model-card strong,
    .modal-item strong {
      font-size: 15px;
      line-height: 1.55;
    }

    .result-signals {
      margin-top: 18px;
      display: grid;
      gap: 10px;
    }

    .signal-item {
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
      line-height: 1.6;
      font-size: 14px;
    }

    .shimmer {
      position: relative;
      overflow: hidden;
    }

    .shimmer::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(110deg, transparent 0%, rgba(255, 255, 255, 0.18) 48%, transparent 100%);
      transform: translateX(-100%);
      animation: shimmer 1.4s linear infinite;
    }

    .loading-stack {
      display: grid;
      gap: 12px;
    }

    .loading-line {
      height: 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.12);
    }

    .loading-line.short {
      width: 38%;
    }

    .loading-line.medium {
      width: 64%;
    }

    .loading-line.large {
      width: 100%;
      height: 64px;
      border-radius: 22px;
    }

    .filter-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr)) 136px;
      gap: 12px;
      margin-bottom: 16px;
    }

    .field.search-field {
      grid-column: span 2;
    }

    .reports-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }

    .reports-meta p {
      margin: 0;
      color: var(--text-soft);
      font-size: 14px;
    }

    .table-card {
      position: relative;
      border-radius: var(--radius-lg);
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
      overflow: hidden;
    }

    .table-card.is-compact table {
      min-width: 0;
    }

    .compact-history-scroll {
      max-height: 520px;
      overflow: auto;
    }

    .table-card.is-loading::after,
    .stats-loading.is-loading::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(110deg, transparent 0%, rgba(255, 255, 255, 0.12) 48%, transparent 100%);
      transform: translateX(-100%);
      animation: shimmer 1.2s linear infinite;
      pointer-events: none;
    }

    .table-scroll {
      overflow: auto;
    }

    table {
      width: 100%;
      min-width: 900px;
      border-collapse: collapse;
    }

    thead th {
      padding: 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-soft);
      background: rgba(255, 255, 255, 0.08);
    }

    tbody td {
      padding: 16px;
      border-top: 1px solid var(--line);
      vertical-align: top;
      font-size: 13px;
      line-height: 1.55;
    }

    tbody tr {
      transition: background var(--transition);
    }

    tbody tr:hover {
      background: rgba(255, 255, 255, 0.08);
    }

    .cell-stack {
      display: grid;
      gap: 4px;
    }

    .cell-stack small {
      color: var(--text-soft);
    }

    .input-pill {
      display: inline-block;
      max-width: 330px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 9px 12px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
      font-family: "Consolas", "Cascadia Code", monospace;
      font-size: 13px;
    }

    .empty-state {
      padding: 24px;
      display: grid;
      gap: 12px;
      align-content: center;
      text-align: left;
    }

    .empty-state h4 {
      margin: 0;
      font-family: var(--font-heading);
      font-size: 24px;
      letter-spacing: -0.03em;
    }

    .empty-state p {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.65;
      font-size: 14px;
    }

    .hidden {
      display: none !important;
    }

    .stats-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
      gap: 20px;
    }

    .stats-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      position: relative;
    }

    .stat-card {
      padding: 20px;
      border-radius: 24px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
      position: relative;
      overflow: hidden;
    }

    .stat-card::after {
      content: "";
      position: absolute;
      right: -18px;
      bottom: -28px;
      width: 110px;
      height: 110px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255, 255, 255, 0.12), transparent 68%);
      pointer-events: none;
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      display: grid;
      place-items: center;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.12);
    }

    .stat-card strong {
      display: block;
      margin: 20px 0 8px;
      font-family: var(--font-heading);
      font-size: clamp(34px, 4vw, 44px);
      letter-spacing: -0.04em;
      line-height: 1;
    }

    .stat-card p {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.65;
      font-size: 14px;
    }

    .stat-card.safe {
      background: linear-gradient(145deg, var(--safe-soft), rgba(255, 255, 255, 0.08)), var(--panel-strong);
    }

    .stat-card.danger {
      background: linear-gradient(145deg, var(--danger-soft), rgba(255, 255, 255, 0.08)), var(--panel-strong);
    }

    .stat-card.blue {
      background: linear-gradient(145deg, var(--blue-soft), rgba(255, 255, 255, 0.08)), var(--panel-strong);
    }

    .stat-card.purple {
      background: linear-gradient(145deg, var(--purple-soft), rgba(255, 255, 255, 0.08)), var(--panel-strong);
    }

    .donut-panel {
      position: relative;
      display: grid;
      gap: 18px;
      align-content: start;
    }

    .donut-wrap {
      display: grid;
      place-items: center;
    }

    .donut-chart {
      --phishing-angle: 0deg;
      width: min(280px, 74vw);
      aspect-ratio: 1;
      border-radius: 50%;
      position: relative;
      background: conic-gradient(var(--danger) 0deg var(--phishing-angle), var(--safe) var(--phishing-angle) 360deg);
      box-shadow: inset 0 0 0 14px rgba(255, 255, 255, 0.06);
    }

    .donut-chart::after {
      content: "";
      position: absolute;
      inset: 28px;
      border-radius: 50%;
      background: var(--panel-strong);
      border: 1px solid var(--line);
    }

    .donut-core {
      position: absolute;
      inset: 0;
      z-index: 1;
      display: grid;
      place-items: center;
      text-align: center;
      padding: 24px;
    }

    .donut-core strong {
      display: block;
      font-family: var(--font-heading);
      font-size: 42px;
      line-height: 1;
    }

    .donut-core span {
      display: block;
      margin-top: 8px;
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.5;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .legend-list {
      display: grid;
      gap: 12px;
    }

    .legend-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
      font-size: 14px;
    }

    .legend-left {
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }

    .legend-swatch {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      flex-shrink: 0;
    }

    .legend-swatch.phishing {
      background: var(--danger);
    }

    .legend-swatch.benign {
      background: var(--safe);
    }

    .insights-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 20px;
    }

    .insight-card p {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.65;
      font-size: 14px;
    }

    .settings-grid {
      grid-template-columns: 220px minmax(0, 1fr);
    }

    .setting-card p,
    .model-card p {
      margin: 0;
      color: var(--text-soft);
      line-height: 1.7;
      font-size: 14px;
    }

    .setting-list {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }

    .setting-row {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .setting-row strong {
      display: block;
      margin-bottom: 4px;
      font-size: 14px;
    }

    .setting-row p {
      font-size: 13px;
      line-height: 1.6;
    }

    .model-grid {
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }

    .model-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }

    .metric-box {
      padding: 12px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .metric-box strong {
      display: block;
      margin-top: 6px;
      font-size: 18px;
      line-height: 1.4;
    }

    .detail-modal {
      position: fixed;
      inset: 0;
      z-index: 60;
      display: grid;
      place-items: center;
      padding: 18px;
      background: rgba(10, 9, 20, 0.54);
    }

    .detail-modal.hidden {
      display: none;
    }

    .modal-card {
      width: min(840px, 100%);
      max-height: min(90vh, 980px);
      overflow: auto;
      padding: 24px;
      border-radius: 32px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-strong);
    }

    .modal-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .modal-top h4 {
      margin: 8px 0 0;
      font-family: var(--font-heading);
      font-size: clamp(26px, 3vw, 32px);
      letter-spacing: -0.04em;
    }

    .modal-note {
      margin: 10px 0 0;
      color: var(--text-soft);
      line-height: 1.7;
      font-size: 14px;
    }

    .modal-wide {
      grid-column: 1 / -1;
    }

    .modal-input-code {
      display: block;
      padding: 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
      font-family: "Consolas", "Cascadia Code", monospace;
      font-size: 13px;
      line-height: 1.7;
      word-break: break-all;
    }

    .signal-grid {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }

    .signal-grid div {
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
      line-height: 1.6;
      font-size: 14px;
    }

    @keyframes shimmer {
      from {
        transform: translateX(-100%);
      }
      to {
        transform: translateX(100%);
      }
    }

    @media (max-width: 1240px) {
      .split-checker,
      .stats-layout,
      .settings-grid {
        grid-template-columns: 1fr;
      }

      .insights-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 1024px) {
      .app-shell {
        grid-template-columns: 1fr;
      }

      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: min(320px, 86vw);
        min-height: 100vh;
        border-radius: 0 28px 28px 0;
        transform: translateX(-104%);
        transition: transform 220ms ease;
        z-index: 50;
      }

      .app-shell.sidebar-open .sidebar {
        transform: translateX(0);
      }

      .menu-button {
        display: inline-flex;
      }
    }

    @media (max-width: 860px) {
      .topbar,
      .page-section {
        padding: 20px;
      }

      .form-grid,
      .filter-grid,
      .stats-grid {
        grid-template-columns: 1fr;
      }

      .field.search-field {
        grid-column: span 1;
      }

      .intro-mini-grid,
      .metric-grid {
        grid-template-columns: 1fr;
      }

      .topbar {
        top: 12px;
      }

      .topbar-right {
        width: 100%;
      }
    }

    @media (max-width: 720px) {
      .topbar-title h2 {
        font-size: 24px;
      }

      .section-head,
      .result-top,
      .modal-top,
      .reports-meta,
      .form-actions {
        flex-direction: column;
        align-items: stretch;
      }

      .primary-button,
      .secondary-button {
        width: 100%;
      }

      .result-side {
        width: 100%;
        justify-content: stretch;
      }

      .result-side .score-card,
      .result-open-button {
        flex: 1 1 160px;
      }

      .detail-modal {
        align-items: end;
        padding: 0;
      }

      .modal-card {
        width: 100%;
        max-height: 92vh;
        border-radius: 28px 28px 0 0;
      }
    }
  </style>
</head>
<body data-theme="dark">
  <div class="sidebar-backdrop" id="sidebar-backdrop"></div>
  <div class="app-shell" id="app-shell">
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l7 3v5c0 4.2-2.5 7.7-7 10-4.5-2.3-7-5.8-7-10V6l7-3z"></path>
            <path d="M9.5 12.3l1.8 1.8 3.5-4"></path>
          </svg>
        </div>
        <div>
          <p class="brand-kicker">IDS</p>
          <h1>Chống lừa đảo</h1>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="Điều hướng">
        <a class="nav-link is-active" href="#checker" data-nav="checker">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 14l-5 5"></path>
              <path d="M16.5 7.5a4.95 4.95 0 10-7 7l2 2a4.95 4.95 0 007-7l-2-2z"></path>
            </svg>
          </span>
          <span class="nav-text">
            <strong>Kiểm tra</strong>
          </span>
        </a>
        <a class="nav-link" href="#stats" data-nav="stats">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 19V9"></path>
              <path d="M12 19V5"></path>
              <path d="M19 19v-7"></path>
            </svg>
          </span>
          <span class="nav-text">
            <strong>Thống kê</strong>
          </span>
        </a>
        <a class="nav-link" href="#reports" data-nav="reports">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 5h16"></path>
              <path d="M4 12h16"></path>
              <path d="M4 19h10"></path>
            </svg>
          </span>
          <span class="nav-text">
            <strong>Báo cáo</strong>
          </span>
        </a>
        <a class="nav-link" href="#settings" data-nav="settings">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 15.5A3.5 3.5 0 1012 8.5a3.5 3.5 0 000 7z"></path>
              <path d="M19.4 15a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 01-2.8 2.8l-.1-.1a1.6 1.6 0 00-1.8-.3 1.6 1.6 0 00-1 1.5V21a2 2 0 01-4 0v-.2a1.6 1.6 0 00-1-1.5 1.6 1.6 0 00-1.8.3l-.1.1a2 2 0 01-2.8-2.8l.1-.1a1.6 1.6 0 00.3-1.8 1.6 1.6 0 00-1.5-1H3a2 2 0 010-4h.2a1.6 1.6 0 001.5-1 1.6 1.6 0 00-.3-1.8l-.1-.1a2 2 0 012.8-2.8l.1.1a1.6 1.6 0 001.8.3H9a1.6 1.6 0 001-1.5V3a2 2 0 014 0v.2a1.6 1.6 0 001 1.5h.1a1.6 1.6 0 001.8-.3l.1-.1a2 2 0 012.8 2.8l-.1.1a1.6 1.6 0 00-.3 1.8v.1a1.6 1.6 0 001.5 1H21a2 2 0 010 4h-.2a1.6 1.6 0 00-1.5 1z"></path>
            </svg>
          </span>
          <span class="nav-text">
            <strong>Cài đặt</strong>
          </span>
        </a>
      </nav>

      <div class="sidebar-foot">
        <div class="status-card">
          <p class="small-label">Trạng thái</p>
          <div class="status-grid">
            <div class="status-row">
              <span>Mới nhất</span>
              <strong id="sidebar-latest">{{ summary.latest_event_at or "Chưa có" }}</strong>
            </div>
            <div class="status-row">
              <span>Tổng lượt</span>
              <strong id="sidebar-total">{{ summary.total_events }}</strong>
            </div>
            <div class="status-row">
              <span>Mô hình</span>
              <strong>{{ model_cards|length }}</strong>
            </div>
          </div>
        </div>
        <a class="ghost-link" href="{{ url_for('dashboard_events') }}">Lịch sử đầy đủ</a>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="menu-button" id="menu-toggle" type="button" aria-label="Mở thanh điều hướng">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
              <path d="M4 7h16"></path>
              <path d="M4 12h16"></path>
              <path d="M4 17h16"></path>
            </svg>
          </button>
          <div class="topbar-title">
            <h2>Phishing Checker Dashboard</h2>
          </div>
        </div>
        <div class="topbar-right">
          <div class="topbar-chip">
            <span class="dot" aria-hidden="true"></span>
            <span id="runtime-status">Đang hoạt động</span>
          </div>
          <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Đổi giao diện sáng hoặc tối" aria-pressed="true">
            <span class="theme-icon" id="theme-icon" aria-hidden="true">☀</span>
            <span class="sr-only" id="theme-label">Giao diện tối</span>
          </button>
        </div>
      </header>

      <section class="page-section section-check" id="checker" data-section="checker">
        <div class="section-head">
          <div>
            <p class="section-kicker">Kiểm tra</p>
            <h3>URL / Domain</h3>
          </div>
          <div class="section-actions">
            <div class="section-badge">
              <span id="check-latest-badge">Đồng bộ: {{ summary.latest_event_at or "Chưa có" }}</span>
            </div>
            <button class="secondary-button" id="manual-toggle" type="button" aria-controls="manual-check-card" aria-expanded="true">
              Ẩn check tay
            </button>
          </div>
        </div>

        <div class="split-checker" id="checker-layout">
          <article class="panel realtime-card">
            <div class="panel-title-row">
              <div>
                <p class="small-label">IDS</p>
                <h4>Log thời gian thực</h4>
              </div>
              <span class="badge badge-neutral" id="realtime-count">0</span>
            </div>
            <div class="risk-chart" id="risk-chart" aria-label="Biểu đồ Score"></div>
            <div class="realtime-feed" id="realtime-feed"></div>
          </article>

          <article class="panel form-card" id="manual-check-card">
            <form id="ingest-form">
              <div class="form-grid">
                <div class="field">
                  <label for="dataset_kind">Loại kiểm tra</label>
                  <select id="dataset_kind" name="dataset_kind">
                    <option value="domain" selected>Domain</option>
                    <option value="url">URL</option>
                    <option value="auto">Tự động</option>
                  </select>
                </div>
                <div class="field">
                  <label for="value">Giá trị</label>
                  <textarea id="value" name="value" placeholder="example.com" autocomplete="off" rows="1" spellcheck="false" required></textarea>
                </div>
              </div>
              <input id="source" name="source" type="hidden" value="ids_browser_sensor">
              <div id="validation-message" class="validation-message" aria-live="polite"></div>
              <div class="form-actions">
                <p class="form-note"></p>
                <button class="primary-button" id="submit-button" type="submit">Kiểm tra</button>
              </div>
            </form>
            <div class="result-panel" id="result-panel" aria-live="polite"></div>
          </article>
        </div>
      </section>

      <section class="page-section section-reports" id="reports" data-section="reports">
        <div class="section-head">
          <div>
            <p class="section-kicker">Báo cáo</p>
            <h3>Lịch sử gần nhất</h3>
          </div>
          <a class="section-badge" href="{{ url_for('dashboard_events') }}">Xem thêm</a>
        </div>

        <div class="filter-grid hidden">
          <div class="field">
            <label for="filter-from">Từ ngày</label>
            <input id="filter-from" type="date">
          </div>
          <div class="field">
            <label for="filter-to">Đến ngày</label>
            <input id="filter-to" type="date">
          </div>
          <div class="field">
            <label for="filter-kind">Loại</label>
            <select id="filter-kind">
              <option value="">Tất cả</option>
              <option value="domain">Domain</option>
              <option value="url">URL</option>
            </select>
          </div>
          <div class="field">
            <label for="filter-result">Kết quả</label>
            <select id="filter-result">
              <option value="">Tất cả</option>
              <option value="phishing">Cảnh báo</option>
              <option value="benign">An toàn</option>
            </select>
          </div>
          <div class="field search-field">
            <label for="filter-search">Tìm nhanh</label>
            <input id="filter-search" type="search" placeholder="Tìm theo giá trị, nguồn, cảm biến...">
          </div>
          <button class="secondary-button" id="reset-filters" type="button">Đặt lại</button>
        </div>

        <div class="reports-meta">
          <p id="reports-meta-text">10 dòng mới nhất.</p>
          <div class="badge-row" id="reports-active-filters"></div>
        </div>

        <div class="table-card is-compact" id="reports-card">
          <div class="compact-history-scroll">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Thời gian</th>
                  <th>Giá trị</th>
                  <th>Risk</th>
                  <th>Kết quả</th>
                </tr>
              </thead>
              <tbody id="reports-body"></tbody>
            </table>
          </div>
          <div class="empty-state hidden" id="reports-empty">
            <h4>Chưa có lịch sử</h4>
            <p>Hãy gửi một domain hoặc URL để tạo bản ghi đầu tiên.</p>
          </div>
        </div>
      </section>

      <section class="page-section section-stats" id="stats" data-section="stats">
        <div class="section-head">
          <div>
            <p class="section-kicker">Thống kê</p>
            <h3>Tổng quan vận hành</h3>
          </div>
          <div class="section-badge" id="stats-headline">0 lượt</div>
        </div>

        <div class="stats-layout">
          <div class="stats-grid stats-loading" id="stats-grid">
            <article class="stat-card safe">
              <div class="stat-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10 14l-5 5"></path>
                  <path d="M16.5 7.5a4.95 4.95 0 10-7 7l2 2a4.95 4.95 0 007-7l-2-2z"></path>
                </svg>
              </div>
              <strong id="stat-url">0</strong>
              <p>URL</p>
            </article>
            <article class="stat-card blue">
              <div class="stat-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 4v16"></path>
                  <path d="M4 12h16"></path>
                  <circle cx="12" cy="12" r="8"></circle>
                </svg>
              </div>
              <strong id="stat-domain">0</strong>
              <p>Domain</p>
            </article>
            <article class="stat-card danger">
              <div class="stat-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 9v4"></path>
                  <path d="M12 17h.01"></path>
                  <path d="M10.29 3.86L1.82 18a2 2 0 001.72 3h16.92a2 2 0 001.72-3L13.71 3.86a2 2 0 00-3.42 0z"></path>
                </svg>
              </div>
              <strong id="stat-phishing">0</strong>
              <p>Cảnh báo</p>
            </article>
            <article class="stat-card purple">
              <div class="stat-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 6L9 17l-5-5"></path>
                </svg>
              </div>
              <strong id="stat-benign">0</strong>
              <p>An toàn</p>
            </article>
          </div>

          <article class="panel donut-panel stats-loading" id="donut-panel">
            <div class="donut-wrap" id="donut-wrap">
              <div class="donut-chart" id="donut-chart">
                <div class="donut-core">
                  <strong id="donut-total">0</strong>
                  <span>Tổng lượt</span>
                </div>
              </div>
            </div>
            <div class="legend-list">
              <div class="legend-row">
                <div class="legend-left">
                  <span class="legend-swatch phishing"></span>
                  <strong>Cảnh báo</strong>
                </div>
                <span id="legend-phishing">0 (0%)</span>
              </div>
              <div class="legend-row">
                <div class="legend-left">
                  <span class="legend-swatch benign"></span>
                  <strong>An toàn</strong>
                </div>
                <span id="legend-benign">0 (0%)</span>
              </div>
            </div>
          </article>
        </div>

        <div class="insights-grid" id="insights-grid">
          <article class="insight-card">
            <span>Tỉ lệ cảnh báo</span>
            <strong id="insight-share">0%</strong>
            <p id="insight-share-copy">Chưa có dữ liệu.</p>
          </article>
          <article class="insight-card">
            <span>Nguồn vào</span>
            <strong id="insight-kind-lead">Cân bằng</strong>
            <p id="insight-kind-copy">URL / Domain.</p>
          </article>
          <article class="insight-card">
            <span>Mới nhất</span>
            <strong id="insight-latest">Chưa có</strong>
            <p id="insight-latest-copy">Log vận hành.</p>
          </article>
        </div>
      </section>

      <section class="page-section section-settings" id="settings" data-section="settings">
        <div class="section-head">
          <div>
            <p class="section-kicker">Cài đặt</p>
            <h3>Mô hình đang dùng</h3>
          </div>
          <div class="section-badge" id="theme-status-badge">Giao diện: Tối</div>
        </div>

        <div class="settings-grid">
          <article class="setting-card">
            <span>Trạng thái</span>
            <strong id="setting-theme-mode">Giao diện tối</strong>
            <div class="setting-list">
              <div class="setting-row">
                <div class="feature-dot" aria-hidden="true"></div>
                <div>
                  <strong>Vận hành</strong>
                  <p id="setting-runtime-copy">{{ summary.total_events }} lượt kiểm tra</p>
                </div>
              </div>
              <div class="setting-row">
                <div class="feature-dot" aria-hidden="true"></div>
                <div>
                  <strong>API</strong>
                  <p>/api/ingest</p>
                </div>
              </div>
            </div>
          </article>

          <div class="model-grid">
            {% for card in model_cards %}
            <article class="model-card">
              <div class="model-top">
                <div>
                  <span>Mô hình {{ card.dataset_kind }}</span>
                  <strong>{{ card.model_name }}</strong>
                </div>
                <span class="badge {% if card.dataset_kind == 'url' %}badge-blue{% else %}badge-purple{% endif %}">{{ card.dataset_kind }}</span>
              </div>
              <div class="metric-grid">
                <div class="metric-box">
                  <span>Dòng dữ liệu</span>
                  <strong>{{ "{:,}".format(card.rows) }}</strong>
                </div>
                <div class="metric-box">
                  <span>Số đặc trưng</span>
                  <strong>{{ card.feature_count }}</strong>
                </div>
                <div class="metric-box">
                  <span>PR-AUC val</span>
                  <strong>{{ "%.4f"|format(card.validation_pr_auc) }}</strong>
                </div>
                <div class="metric-box">
                  <span>PR-AUC test</span>
                  <strong>{{ "%.4f"|format(card.test_pr_auc) }}</strong>
                </div>
              </div>
            </article>
            {% endfor %}
          </div>
        </div>
      </section>
    </main>
  </div>

  <div class="detail-modal hidden" id="detail-modal" aria-hidden="true">
    <div class="modal-card">
      <div class="modal-top">
        <div>
          <p class="small-label">Chi tiết</p>
          <h4 id="modal-title">Chi tiết sự kiện</h4>
          <p class="modal-note" id="modal-note">Thông tin chi tiết của một lần kiểm tra sẽ hiển thị tại đây.</p>
        </div>
        <button class="modal-close" id="modal-close" type="button">Đóng</button>
      </div>
      <div class="badge-row" id="modal-badges"></div>
      <div class="modal-grid" id="modal-grid"></div>
      <div class="modal-wide" style="margin-top: 16px;">
        <span class="small-label">Giá trị đầy đủ</span>
        <code class="modal-input-code" id="modal-input-code"></code>
      </div>
      <div class="modal-wide" style="margin-top: 16px;">
        <span class="small-label">Tín hiệu</span>
        <div class="signal-grid" id="modal-signals"></div>
      </div>
    </div>
  </div>

  <script>
    const INITIAL_EVENTS = {{ events|tojson }};
    const INITIAL_SUMMARY = {{ summary|tojson }};
    const MODEL_CARDS = {{ model_cards|tojson }};

    const appShell = document.getElementById("app-shell");
    const sidebarBackdrop = document.getElementById("sidebar-backdrop");
    const menuToggle = document.getElementById("menu-toggle");
    const themeToggle = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const themeLabel = document.getElementById("theme-label");
    const themeStatusBadge = document.getElementById("theme-status-badge");
    const settingThemeMode = document.getElementById("setting-theme-mode");
    const runtimeStatus = document.getElementById("runtime-status");
    const sidebarLatest = document.getElementById("sidebar-latest");
    const sidebarTotal = document.getElementById("sidebar-total");
    const checkLatestBadge = document.getElementById("check-latest-badge");
    const statsHeadline = document.getElementById("stats-headline");
    const settingRuntimeCopy = document.getElementById("setting-runtime-copy");
    const riskChart = document.getElementById("risk-chart");
    const realtimeFeed = document.getElementById("realtime-feed");
    const realtimeCount = document.getElementById("realtime-count");
    const checkerLayout = document.getElementById("checker-layout");
    const manualPanel = document.getElementById("manual-check-card");
    const manualToggleButton = document.getElementById("manual-toggle");

    const form = document.getElementById("ingest-form");
    const datasetKindField = document.getElementById("dataset_kind");
    const valueField = document.getElementById("value");
    const sourceField = document.getElementById("source");
    const submitButton = document.getElementById("submit-button");
    const validationMessage = document.getElementById("validation-message");
    const resultPanel = document.getElementById("result-panel");

    const filterFrom = document.getElementById("filter-from");
    const filterTo = document.getElementById("filter-to");
    const filterKind = document.getElementById("filter-kind");
    const filterResult = document.getElementById("filter-result");
    const filterSearch = document.getElementById("filter-search");
    const resetFiltersButton = document.getElementById("reset-filters");
    const reportsMetaText = document.getElementById("reports-meta-text");
    const reportsActiveFilters = document.getElementById("reports-active-filters");
    const reportsBody = document.getElementById("reports-body");
    const reportsEmpty = document.getElementById("reports-empty");
    const reportsCard = document.getElementById("reports-card");

    const statsGrid = document.getElementById("stats-grid");
    const donutPanel = document.getElementById("donut-panel");
    const donutChart = document.getElementById("donut-chart");
    const donutTotal = document.getElementById("donut-total");
    const legendPhishing = document.getElementById("legend-phishing");
    const legendBenign = document.getElementById("legend-benign");
    const insightShare = document.getElementById("insight-share");
    const insightShareCopy = document.getElementById("insight-share-copy");
    const insightKindLead = document.getElementById("insight-kind-lead");
    const insightKindCopy = document.getElementById("insight-kind-copy");
    const insightLatest = document.getElementById("insight-latest");
    const insightLatestCopy = document.getElementById("insight-latest-copy");

    const statUrl = document.getElementById("stat-url");
    const statDomain = document.getElementById("stat-domain");
    const statPhishing = document.getElementById("stat-phishing");
    const statBenign = document.getElementById("stat-benign");

    const detailModal = document.getElementById("detail-modal");
    const modalClose = document.getElementById("modal-close");
    const modalTitle = document.getElementById("modal-title");
    const modalNote = document.getElementById("modal-note");
    const modalBadges = document.getElementById("modal-badges");
    const modalGrid = document.getElementById("modal-grid");
    const modalInputCode = document.getElementById("modal-input-code");
    const modalSignals = document.getElementById("modal-signals");

    const placeholders = {
      domain: "example.com",
      url: "https://example.com/login",
      auto: "example.com hoặc https://example.com/login",
    };

    const samples = {
      domain: "cellphones.com.vn",
      url: "https://cellphones.com.vn/",
    };

    let dashboardEvents = Array.isArray(INITIAL_EVENTS) ? [...INITIAL_EVENTS] : [];
    let filteredEvents = [...dashboardEvents];
    let currentSummary = INITIAL_SUMMARY || {};
    let eventIndex = new Map();
    let isRefreshingEvents = false;

    const escapeHtml = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

    const formatNumber = (value) => new Intl.NumberFormat("vi-VN").format(Number(value || 0));

    const formatDateTime = (value) => {
      if (!value) {
        return "Chưa có";
      }
      const date = new Date(value);
      if (Number.isNaN(date.valueOf())) {
        return String(value);
      }
      return new Intl.DateTimeFormat("vi-VN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    };

    const dateKeyFromValue = (value) => {
      if (!value) {
        return "";
      }
      const date = new Date(value);
      if (Number.isNaN(date.valueOf())) {
        return "";
      }
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };

    const looksLikeUrl = (value) => value.includes("://");
    const looksLikeDomain = (value) => /^(?!-)(?:[a-zA-Z0-9-]{1,63}\\.)+[a-zA-Z]{2,63}$/.test(value.trim());
    const buildOpenHref = (value) => {
      const text = String(value || "").trim();
      const lowerText = text.toLowerCase();
      if (lowerText.startsWith("http://") || lowerText.startsWith("https://")) {
        return text;
      }
      if (looksLikeDomain(text)) {
        return `https://${text}`;
      }
      return "";
    };

    const kindLabel = (kind) => kind === "url" ? "URL" : "Domain";
    const riskLabel = (risk) => ({
      high: "HIGH",
      medium: "MEDIUM",
      low: "LOW",
      minimal: "MINIMAL",
    }[String(risk || "minimal")] || String(risk || "minimal").toUpperCase());
    const verdictLabel = (result) => String(result || "") === "phishing" ? "CẢNH BÁO" : "AN TOÀN";

    const badgeClassForRisk = (risk) => {
      if (risk === "high") {
        return "badge-danger";
      }
      if (risk === "medium") {
        return "badge-warning";
      }
      if (risk === "low") {
        return "badge-blue";
      }
      return "badge-safe";
    };

    const badgeClassForVerdict = (verdict) => verdict === "phishing" ? "badge-danger" : "badge-safe";
    const badgeClassForKind = (kind) => kind === "url" ? "badge-blue" : "badge-purple";
    const isRealtimeIdsEvent = (event) => String(event.ids_event_type || "manual_check") !== "manual_check";

    const scoreText = (score) => {
      if (score === null || score === undefined || Number.isNaN(Number(score))) {
        return "N/A";
      }
      return Number(score).toFixed(4);
    };

    const setPlaceholder = () => {
      valueField.placeholder = placeholders[datasetKindField.value] || placeholders.auto;
    };

    const autoResizeValueField = () => {
      valueField.style.height = "auto";
      valueField.style.height = `${Math.max(56, valueField.scrollHeight)}px`;
    };

    const setManualCheckVisible = (isVisible, { persist = true } = {}) => {
      checkerLayout.classList.toggle("manual-hidden", !isVisible);
      manualPanel.hidden = !isVisible;
      manualToggleButton.textContent = isVisible ? "Ẩn check tay" : "Hiện check tay";
      manualToggleButton.setAttribute("aria-expanded", String(isVisible));
      if (persist) {
        localStorage.setItem("phishing_checker:manual_visible", isVisible ? "1" : "0");
      }
      if (isVisible) {
        autoResizeValueField();
      }
    };

    const loadManualCheckVisibility = () => {
      setManualCheckVisible(localStorage.getItem("phishing_checker:manual_visible") !== "0", { persist: false });
    };

    const clearValidation = () => {
      validationMessage.className = "validation-message";
      validationMessage.innerHTML = "";
    };

    const showValidation = (message, kind = "error", suggestionKind = "") => {
      validationMessage.className = `validation-message is-visible is-${kind}`;
      if (suggestionKind) {
        const switchLabel = suggestionKind === "url" ? "Chuyển sang URL" : "Chuyển sang Domain";
        validationMessage.innerHTML = `
          <span>${escapeHtml(message)}</span>
          <button class="secondary-button" type="button" data-kind-switch="${escapeHtml(suggestionKind)}">${switchLabel}</button>
        `;
        return;
      }
      validationMessage.textContent = message;
    };

    const validateInput = () => {
      const kind = datasetKindField.value;
      const value = valueField.value.trim();
      if (!value) {
        return { ok: false, message: "Vui lòng nhập domain hoặc URL trước khi kiểm tra.", kind: "error" };
      }
      if (kind === "domain") {
        if (looksLikeUrl(value)) {
          return {
            ok: false,
            message: "Giá trị này giống URL đầy đủ hơn là domain thuần.",
            kind: "error",
            suggestionKind: "url",
          };
        }
        if (!looksLikeDomain(value)) {
          return { ok: false, message: "Domain chưa đúng định dạng. Ví dụ hợp lệ: example.com", kind: "error" };
        }
      }
      if (kind === "url") {
        if (!looksLikeUrl(value)) {
          if (looksLikeDomain(value)) {
            return {
              ok: false,
              message: "Giá trị hiện trông giống domain. Bạn có thể chuyển sang chế độ Domain.",
              kind: "error",
              suggestionKind: "domain",
            };
          }
          return { ok: false, message: "URL chưa đúng định dạng. Ví dụ hợp lệ: https://example.com/login", kind: "error" };
        }
      }
      return { ok: true };
    };

    const resultEmptyHtml = () => `
      <div class="state-card">
        <h4>Chưa có kết quả</h4>
        <p>Nhập domain hoặc URL để kiểm tra.</p>
      </div>
    `;

    const resultLoadingHtml = () => `
      <div class="state-card shimmer">
        <div class="loading-stack">
          <div class="loading-line short"></div>
          <div class="loading-line medium"></div>
          <div class="loading-line large"></div>
          <div class="loading-line"></div>
          <div class="loading-line medium"></div>
        </div>
      </div>
    `;

    const resultErrorHtml = (message) => `
      <div class="result-shell is-danger">
        <div class="badge-row">
          <span class="badge badge-danger">LỖI</span>
        </div>
        <div class="result-top">
          <div>
            <h4>Không thể kiểm tra</h4>
            <p class="result-summary">${escapeHtml(message)}</p>
          </div>
        </div>
      </div>
    `;

    const renderSignals = (signals) => {
      if (!Array.isArray(signals) || signals.length === 0) {
        return '<div class="signal-item">Không có tín hiệu nổi bật.</div>';
      }
      return signals.map((signal) => `<div class="signal-item">${escapeHtml(signal)}</div>`).join("");
    };

    const renderResult = (event) => {
      const isPhishing = String(event.predicted_class || "") === "phishing";
      const resultTone = isPhishing ? "is-danger" : "is-safe";
      const note = event.recommendation || "";
      const inspectedValue = event.normalized_value || event.raw_value || "";
      const openHref = buildOpenHref(inspectedValue);
      resultPanel.innerHTML = `
        <div class="result-shell ${resultTone}">
          <div class="result-top">
            <div>
              <div class="badge-row">
                <span class="badge ${badgeClassForVerdict(event.predicted_class)}">${escapeHtml(verdictLabel(event.predicted_class))}</span>
                <span class="badge ${badgeClassForRisk(event.risk_level)}">${escapeHtml(riskLabel(event.risk_level))}</span>
                <span class="badge ${badgeClassForKind(event.dataset_kind)}">${escapeHtml(kindLabel(event.dataset_kind))}</span>
              </div>
              <h4>${isPhishing ? "Phát hiện lừa đảo" : "Chưa phát hiện lừa đảo"}</h4>
              ${note ? `<p class="result-summary">${escapeHtml(note)}</p>` : ""}
            </div>
            <div class="result-side">
              <div class="score-card">
                <strong>${escapeHtml(scoreText(event.score))}</strong>
                <span>Score</span>
              </div>
              ${openHref ? `
                <a class="secondary-button result-open-button" href="${escapeHtml(openHref)}" target="_blank" rel="noopener noreferrer" aria-label="Mở ${escapeHtml(inspectedValue)} trong tab mới">
                  Kiểm tra
                </a>
              ` : ""}
            </div>
          </div>
          <div class="result-grid">
            <div class="result-item">
              <span>Giá trị</span>
              <strong>${escapeHtml(event.normalized_value || event.raw_value || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Thời gian</span>
              <strong>${escapeHtml(formatDateTime(event.received_at))}</strong>
            </div>
            <div class="result-item">
              <span>Nguồn</span>
              <strong>${escapeHtml(event.source || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Mô hình</span>
              <strong>${escapeHtml(event.model_name || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Cảm biến</span>
              <strong>${escapeHtml(event.sensor_name || "N/A")}</strong>
            </div>
            <div class="result-item">
              <span>Quyết định</span>
              <strong>${escapeHtml(event.decision_summary || event.decision_mode || "mô hình")}</strong>
            </div>
          </div>
          <div class="result-signals">
            ${renderSignals(event.signals)}
          </div>
        </div>
      `;
    };

    const summarizeClientEvents = (events) => {
      const total = events.length;
      const phishing = events.filter((event) => event.predicted_class === "phishing").length;
      const benign = total - phishing;
      const url = events.filter((event) => event.dataset_kind === "url").length;
      const domain = events.filter((event) => event.dataset_kind === "domain").length;
      const high = events.filter((event) => event.risk_level === "high").length;
      const latest = events[0]?.received_at || currentSummary.latest_event_at || null;
      return {
        total_events: total,
        phishing_events: phishing,
        benign_events: benign,
        url_events: url,
        domain_events: domain,
        high_risk_events: high,
        latest_event_at: latest,
      };
    };

    const updateEventIndex = () => {
      eventIndex = new Map(dashboardEvents.map((event) => [String(event.event_id), event]));
    };

    const scoreValue = (event) => {
      const score = Number(event.score);
      if (!Number.isNaN(score)) {
        return Math.max(0, Math.min(1, score));
      }
      return {
        high: 0.95,
        medium: 0.70,
        low: 0.45,
        minimal: 0.18,
      }[event.risk_level] || 0.18;
    };

    const renderScoreLineChart = (events) => {
      if (events.length === 0) {
        return '<div class="empty-state"><h4>Chưa có URL</h4><p>Biểu đồ sẽ hiện sau khi bridge gửi URL đầu tiên.</p></div>';
      }

      const width = 620;
      const height = 220;
      const left = 46;
      const right = 18;
      const top = 18;
      const bottom = 38;
      const plotWidth = width - left - right;
      const plotHeight = height - top - bottom;
      const xForIndex = (index) => {
        if (events.length === 1) {
          return left + plotWidth / 2;
        }
        return left + (index / (events.length - 1)) * plotWidth;
      };
      const yForScore = (score) => top + (1 - score) * plotHeight;
      const points = events.map((event, index) => {
        const x = xForIndex(index);
        const y = yForScore(scoreValue(event));
        return { x, y, event, score: scoreValue(event) };
      });
      const pointText = points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
      const areaText = [
        `${points[0].x.toFixed(1)},${(top + plotHeight).toFixed(1)}`,
        pointText,
        `${points[points.length - 1].x.toFixed(1)},${(top + plotHeight).toFixed(1)}`,
      ].join(" ");
      const gridRows = [0, 0.5, 1].map((score) => {
        const y = yForScore(score);
        return `
          <line class="chart-grid" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line>
          <text class="chart-label" x="8" y="${y + 4}">${score.toFixed(1)}</text>
        `;
      }).join("");
      const dots = points.map((point, index) => {
        const modelScore = Number(point.event.model_score_before_override);
        const modelScoreText = Number.isNaN(modelScore) ? "" : ` | Model trước override ${modelScore.toFixed(4)}`;
        const title = `URL ${index + 1} | Score ${point.score.toFixed(4)}${modelScoreText} | ${riskLabel(point.event.risk_level)}`;
        return `<circle class="chart-point" cx="${point.x}" cy="${point.y}" r="4"><title>${escapeHtml(title)}</title></circle>`;
      }).join("");
      const lastLabel = String(events.length);
      return `
        <svg class="score-line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Score theo số lượng URL kiểm tra">
          ${gridRows}
          <line class="chart-axis" x1="${left}" y1="${top}" x2="${left}" y2="${top + plotHeight}"></line>
          <line class="chart-axis" x1="${left}" y1="${top + plotHeight}" x2="${width - right}" y2="${top + plotHeight}"></line>
          <polygon class="chart-area" points="${areaText}"></polygon>
          <polyline class="chart-line" points="${pointText}"></polyline>
          ${dots}
          <text class="chart-label" x="${left}" y="${height - 10}">1</text>
          <text class="chart-label" x="${width - right - 10}" y="${height - 10}">${escapeHtml(lastLabel)}</text>
          <text class="chart-label" x="${width / 2 - 34}" y="${height - 10}">Số URL</text>
          <text class="chart-label" x="8" y="14">Score</text>
        </svg>
      `;
    };

    const renderRealtime = () => {
      const realtimeEvents = dashboardEvents.filter(isRealtimeIdsEvent);
      const latestEvents = realtimeEvents.slice(0, 20);
      const urlEvents = realtimeEvents
        .filter((event) => event.dataset_kind === "url")
        .slice(0, 20)
        .reverse();
      realtimeCount.textContent = `${formatNumber(urlEvents.length)} URL gần nhất`;
      if (latestEvents.length === 0) {
        riskChart.innerHTML = renderScoreLineChart([]);
        realtimeFeed.innerHTML = '<div class="empty-state"><h4>Chưa có log</h4><p>Chạy bridge để nạp file IDS.</p></div>';
        return;
      }

      riskChart.innerHTML = renderScoreLineChart(urlEvents);

      realtimeFeed.innerHTML = latestEvents.slice(0, 8).map((event) => {
        const checkedValue = event.normalized_value || event.raw_value || "";
        const openHref = buildOpenHref(checkedValue);
        const checkButton = openHref ? `
          <a class="feed-check-button" href="${escapeHtml(openHref)}" target="_blank" rel="noopener noreferrer" aria-label="Mở ${escapeHtml(checkedValue)} trong tab mới">
            Check
          </a>
        ` : "";
        return `
          <div class="feed-row">
            <div class="feed-value">
              <strong title="${escapeHtml(checkedValue)}">${escapeHtml(checkedValue || "N/A")}</strong>
              <span>${escapeHtml(formatDateTime(event.received_at))} · ${escapeHtml(event.ids_event_type || "thủ công")}</span>
            </div>
            <div class="feed-actions">
              <span class="badge ${badgeClassForRisk(event.risk_level)}">${escapeHtml(riskLabel(event.risk_level))}</span>
              ${checkButton}
            </div>
          </div>
        `;
      }).join("");
    };

    const setDashboardLoading = (isLoading) => {
      reportsCard.classList.toggle("is-loading", isLoading);
      statsGrid.classList.toggle("is-loading", isLoading);
      donutPanel.classList.toggle("is-loading", isLoading);
      runtimeStatus.textContent = isLoading ? "Đang đồng bộ" : "Đang hoạt động";
    };

    const updateTopSummary = (summary) => {
      sidebarLatest.textContent = summary.latest_event_at ? formatDateTime(summary.latest_event_at) : "Chưa có";
      sidebarTotal.textContent = formatNumber(summary.total_events || 0);
      checkLatestBadge.textContent = `Đồng bộ: ${summary.latest_event_at ? formatDateTime(summary.latest_event_at) : "Chưa có"}`;
      statsHeadline.textContent = `${formatNumber(summary.total_events || 0)} lượt | ${formatNumber(summary.high_risk_events || 0)} risk cao`;
      settingRuntimeCopy.textContent = `${formatNumber(summary.total_events || 0)} lượt kiểm tra`;
    };

    const renderReportsFilterChips = () => {
      const active = [];
      if (filterFrom.value) {
        active.push(`Từ: ${filterFrom.value}`);
      }
      if (filterTo.value) {
        active.push(`Đến: ${filterTo.value}`);
      }
      if (filterKind.value) {
        active.push(`Loại: ${kindLabel(filterKind.value)}`);
      }
      if (filterResult.value) {
        active.push(`Kết quả: ${verdictLabel(filterResult.value)}`);
      }
      if (filterSearch.value.trim()) {
        active.push(`Tìm: ${filterSearch.value.trim()}`);
      }
      reportsActiveFilters.innerHTML = active.map((item) => `<span class="badge badge-neutral">${escapeHtml(item)}</span>`).join("");
    };

    const filterEvents = () => {
      const from = filterFrom.value;
      const to = filterTo.value;
      const kind = filterKind.value;
      const result = filterResult.value;
      const keyword = filterSearch.value.trim().toLowerCase();

      filteredEvents = dashboardEvents.filter((event) => {
        const eventDate = dateKeyFromValue(event.received_at);
        if (from && (!eventDate || eventDate < from)) {
          return false;
        }
        if (to && (!eventDate || eventDate > to)) {
          return false;
        }
        if (kind && event.dataset_kind !== kind) {
          return false;
        }
        if (result && event.predicted_class !== result) {
          return false;
        }
        if (keyword) {
          const haystack = [
            event.normalized_value,
            event.raw_value,
            event.source,
            event.sensor_name,
            event.ids_event_type,
            event.flow_summary,
            event.predicted_class,
            event.risk_level,
          ].join(" ").toLowerCase();
          if (!haystack.includes(keyword)) {
            return false;
          }
        }
        return true;
      });
    };

    const reportRowHtml = (event) => `
      <tr>
        <td>
          <div class="cell-stack">
            <strong>${escapeHtml(formatDateTime(event.received_at))}</strong>
            <small>${escapeHtml(event.observed_at || event.received_at || "N/A")}</small>
          </div>
        </td>
        <td><span class="input-pill" title="${escapeHtml(event.normalized_value || event.raw_value || "")}">${escapeHtml(event.normalized_value || event.raw_value || "N/A")}</span></td>
        <td><span class="badge ${badgeClassForRisk(event.risk_level)}">${escapeHtml(riskLabel(event.risk_level))}</span></td>
        <td><span class="badge ${badgeClassForVerdict(event.predicted_class)}">${escapeHtml(verdictLabel(event.predicted_class))}</span></td>
      </tr>
    `;

    const renderReports = () => {
      renderReportsFilterChips();
      const recentEvents = filteredEvents.slice(0, 10);
      reportsMetaText.textContent = `${formatNumber(recentEvents.length)} dòng mới nhất / ${formatNumber(dashboardEvents.length)} tổng.`;
      if (filteredEvents.length === 0) {
        reportsBody.innerHTML = "";
        reportsEmpty.classList.remove("hidden");
        return;
      }
      reportsEmpty.classList.add("hidden");
      reportsBody.innerHTML = recentEvents.map(reportRowHtml).join("");
    };

    const updateStats = () => {
      const summary = summarizeClientEvents(dashboardEvents);
      currentSummary = summary;
      statUrl.textContent = formatNumber(summary.url_events);
      statDomain.textContent = formatNumber(summary.domain_events);
      statPhishing.textContent = formatNumber(summary.phishing_events);
      statBenign.textContent = formatNumber(summary.benign_events);
      donutTotal.textContent = formatNumber(summary.total_events);

      const total = summary.total_events || 0;
      const phishingPct = total ? Math.round((summary.phishing_events / total) * 100) : 0;
      const benignPct = total ? 100 - phishingPct : 0;
      donutChart.style.setProperty("--phishing-angle", `${Math.max(0, Math.min(360, phishingPct * 3.6))}deg`);
      legendPhishing.textContent = `${formatNumber(summary.phishing_events)} (${phishingPct}%)`;
      legendBenign.textContent = `${formatNumber(summary.benign_events)} (${benignPct}%)`;

      insightShare.textContent = `${phishingPct}%`;
      insightShareCopy.textContent = total
        ? `${formatNumber(summary.phishing_events)} / ${formatNumber(total)} lượt.`
        : "Chưa có dữ liệu.";

      if (!total) {
        insightKindLead.textContent = "Chưa có dữ liệu";
        insightKindCopy.textContent = "URL / Domain.";
      } else if (summary.url_events > summary.domain_events) {
        insightKindLead.textContent = "URL";
        insightKindCopy.textContent = `${formatNumber(summary.url_events)} URL / ${formatNumber(summary.domain_events)} domain.`;
      } else if (summary.domain_events > summary.url_events) {
        insightKindLead.textContent = "Domain";
        insightKindCopy.textContent = `${formatNumber(summary.domain_events)} domain / ${formatNumber(summary.url_events)} URL.`;
      } else {
        insightKindLead.textContent = "Cân bằng";
        insightKindCopy.textContent = `${formatNumber(summary.url_events)} URL / ${formatNumber(summary.domain_events)} domain.`;
      }

      insightLatest.textContent = summary.latest_event_at ? formatDateTime(summary.latest_event_at) : "Chưa có";
      insightLatestCopy.textContent = summary.latest_event_at
        ? "Đã đồng bộ."
        : "Chưa có log.";

      updateTopSummary(summary);
    };

    const openDetailModal = (eventId) => {
      const event = eventIndex.get(String(eventId));
      if (!event) {
        return;
      }
      modalTitle.textContent = event.predicted_class === "phishing" ? "Chi tiết cảnh báo" : "Chi tiết an toàn";
      modalNote.textContent = event.recommendation || "Không có ghi chú.";
      modalBadges.innerHTML = `
        <span class="badge ${badgeClassForVerdict(event.predicted_class)}">${escapeHtml(verdictLabel(event.predicted_class))}</span>
        <span class="badge ${badgeClassForRisk(event.risk_level)}">${escapeHtml(riskLabel(event.risk_level))}</span>
        <span class="badge ${badgeClassForKind(event.dataset_kind)}">${escapeHtml(kindLabel(event.dataset_kind))}</span>
      `;
      modalGrid.innerHTML = `
        <div class="modal-item">
          <span>Thời gian</span>
          <strong>${escapeHtml(formatDateTime(event.received_at))}</strong>
        </div>
        <div class="modal-item">
          <span>Ghi nhận</span>
          <strong>${escapeHtml(event.observed_at || event.received_at || "N/A")}</strong>
        </div>
        <div class="modal-item">
          <span>Score</span>
          <strong>${escapeHtml(scoreText(event.score))}</strong>
        </div>
        <div class="modal-item">
          <span>Nguồn</span>
          <strong>${escapeHtml(event.source || "N/A")}</strong>
        </div>
        <div class="modal-item">
          <span>Cảm biến</span>
          <strong>${escapeHtml(event.sensor_name || "N/A")}</strong>
        </div>
        <div class="modal-item">
          <span>Sự kiện</span>
          <strong>${escapeHtml(event.ids_event_type || "kiểm tra thủ công")}</strong>
        </div>
        <div class="modal-item">
          <span>Luồng</span>
          <strong>${escapeHtml(event.flow_summary || "N/A")}</strong>
        </div>
        <div class="modal-item">
          <span>Quyết định</span>
          <strong>${escapeHtml(event.decision_summary || event.decision_mode || "mô hình")}</strong>
        </div>
        <div class="modal-item">
          <span>Mô hình</span>
          <strong>${escapeHtml(event.model_name || "N/A")}</strong>
        </div>
        <div class="modal-item">
          <span>Biến thể</span>
          <strong>${escapeHtml(event.variant_name || "N/A")}</strong>
        </div>
        ${event.override_reason ? `
          <div class="modal-item modal-wide">
            <span>Ghi đè</span>
            <strong>${escapeHtml(event.override_match_value || event.override_reason)}</strong>
          </div>
        ` : ""}
      `;
      modalInputCode.textContent = event.raw_value || event.normalized_value || "N/A";
      if (Array.isArray(event.signals) && event.signals.length > 0) {
        modalSignals.innerHTML = event.signals.map((signal) => `<div>${escapeHtml(signal)}</div>`).join("");
      } else {
        modalSignals.innerHTML = "<div>Không có tín hiệu nổi bật.</div>";
      }
      detailModal.classList.remove("hidden");
      detailModal.setAttribute("aria-hidden", "false");
    };

    const closeDetailModal = () => {
      detailModal.classList.add("hidden");
      detailModal.setAttribute("aria-hidden", "true");
    };

    const renderDashboard = () => {
      updateEventIndex();
      filterEvents();
      renderRealtime();
      renderReports();
      updateStats();
    };

    const persistLastCheck = () => {
      localStorage.setItem("phishing_checker:last_kind", datasetKindField.value);
      localStorage.setItem("phishing_checker:last_value", valueField.value.trim());
    };

    const restoreLastCheck = () => {
      const lastKind = localStorage.getItem("phishing_checker:last_kind");
      const lastValue = localStorage.getItem("phishing_checker:last_value");
      if (lastKind && ["domain", "url", "auto"].includes(lastKind)) {
        datasetKindField.value = lastKind;
      }
      if (lastValue) {
        valueField.value = lastValue;
      }
      setPlaceholder();
      autoResizeValueField();
    };

    const applyTheme = (theme) => {
      const resolvedTheme = theme === "dark" ? "dark" : "light";
      document.body.dataset.theme = resolvedTheme;
      localStorage.setItem("phishing_checker:theme", resolvedTheme);
      const label = resolvedTheme === "dark" ? "Giao diện tối" : "Giao diện sáng";
      themeIcon.textContent = resolvedTheme === "dark" ? "☀" : "☾";
      themeLabel.textContent = label;
      settingThemeMode.textContent = label;
      themeStatusBadge.textContent = `Giao diện: ${resolvedTheme === "dark" ? "Tối" : "Sáng"}`;
      themeToggle.setAttribute("aria-pressed", resolvedTheme === "dark" ? "true" : "false");
    };

    const loadTheme = () => {
      const storedTheme = localStorage.getItem("phishing_checker:theme");
      if (storedTheme) {
        applyTheme(storedTheme);
        return;
      }
      applyTheme("dark");
    };

    const setSidebarOpen = (isOpen) => {
      appShell.classList.toggle("sidebar-open", isOpen);
      sidebarBackdrop.classList.toggle("is-visible", isOpen);
    };

    const refreshEvents = async ({ silent = false } = {}) => {
      if (isRefreshingEvents) {
        return;
      }
      isRefreshingEvents = true;
      if (!silent) {
        setDashboardLoading(true);
      }
      try {
        const response = await fetch("/api/events?limit=200");
        if (!response.ok) {
          throw new Error("Không tải được log vận hành.");
        }
        const payload = await response.json();
        const nextEvents = Array.isArray(payload.events) ? payload.events : [];
        const currentHead = dashboardEvents[0]?.event_id || "";
        const nextHead = nextEvents[0]?.event_id || "";
        const hasChanged = currentHead !== nextHead || dashboardEvents.length !== nextEvents.length;
        dashboardEvents = nextEvents;
        currentSummary = payload.summary || summarizeClientEvents(dashboardEvents);
        if (hasChanged) {
          renderDashboard();
        } else {
          updateTopSummary(currentSummary);
        }
        runtimeStatus.textContent = "Đang hoạt động";
      } catch (error) {
        runtimeStatus.textContent = "Đang hoạt động";
      } finally {
        if (!silent) {
          setDashboardLoading(false);
        }
        isRefreshingEvents = false;
      }
    };

    const installScrollSpy = () => {
      const navLinks = [...document.querySelectorAll("[data-nav]")];
      const sections = [...document.querySelectorAll("[data-section]")];
      const setActive = (name) => {
        navLinks.forEach((link) => {
          link.classList.toggle("is-active", link.dataset.nav === name);
        });
      };
      const observer = new IntersectionObserver((entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) {
          setActive(visible.target.dataset.section);
        }
      }, {
        threshold: [0.2, 0.45, 0.7],
        rootMargin: "-20% 0px -45% 0px",
      });
      sections.forEach((section) => observer.observe(section));
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const validation = validateInput();
      if (!validation.ok) {
        showValidation(validation.message, validation.kind, validation.suggestionKind || "");
        valueField.focus();
        return;
      }

      clearValidation();
      submitButton.disabled = true;
      resultPanel.innerHTML = resultLoadingHtml();
      resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });

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
        const payload = await response.json();
        if (!response.ok) {
          resultPanel.innerHTML = resultErrorHtml(payload.error || "Lỗi không xác định.");
          return;
        }

        renderResult(payload);
        persistLastCheck();
        await refreshEvents({ silent: true });
      } catch (error) {
        resultPanel.innerHTML = resultErrorHtml("Không kết nối được tới API.");
      } finally {
        submitButton.disabled = false;
      }
    });

    datasetKindField.addEventListener("change", () => {
      setPlaceholder();
      const validation = validateInput();
      if (!validation.ok) {
        showValidation(validation.message, validation.kind, validation.suggestionKind || "");
      } else {
        clearValidation();
      }
    });

    valueField.addEventListener("input", () => {
      autoResizeValueField();
      const validation = validateInput();
      if (!validation.ok && valueField.value.trim()) {
        showValidation(validation.message, validation.kind, validation.suggestionKind || "");
      } else {
        clearValidation();
      }
    });

    valueField.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

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
          valueField.focus();
          return;
        } else if (action === "clear") {
          valueField.value = "";
        }
        setPlaceholder();
        autoResizeValueField();
        clearValidation();
        valueField.focus();
      });
    });

    validationMessage.addEventListener("click", (event) => {
      const switchButton = event.target.closest("[data-kind-switch]");
      if (!switchButton) {
        return;
      }
      datasetKindField.value = switchButton.dataset.kindSwitch || "auto";
      setPlaceholder();
      autoResizeValueField();
      clearValidation();
      valueField.focus();
    });

    manualToggleButton.addEventListener("click", () => {
      const nextVisible = manualToggleButton.getAttribute("aria-expanded") !== "true";
      setManualCheckVisible(nextVisible);
    });

    [filterFrom, filterTo, filterKind, filterResult].forEach((field) => {
      field.addEventListener("change", renderDashboard);
    });
    filterSearch.addEventListener("input", renderDashboard);
    resetFiltersButton.addEventListener("click", () => {
      filterFrom.value = "";
      filterTo.value = "";
      filterKind.value = "";
      filterResult.value = "";
      filterSearch.value = "";
      renderDashboard();
    });

    reportsBody.addEventListener("click", (event) => {
      const button = event.target.closest("[data-open-detail]");
      if (!button) {
        return;
      }
      openDetailModal(button.dataset.openDetail);
    });

    modalClose.addEventListener("click", closeDetailModal);
    detailModal.addEventListener("click", (event) => {
      if (event.target === detailModal) {
        closeDetailModal();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeDetailModal();
        setSidebarOpen(false);
      }
    });

    themeToggle.addEventListener("click", () => {
      applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
    });

    menuToggle.addEventListener("click", () => {
      setSidebarOpen(!appShell.classList.contains("sidebar-open"));
    });

    sidebarBackdrop.addEventListener("click", () => {
      setSidebarOpen(false);
    });

    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 1024) {
          setSidebarOpen(false);
        }
      });
    });

    loadTheme();
    restoreLastCheck();
    setPlaceholder();
    loadManualCheckVisibility();
    autoResizeValueField();
    resultPanel.innerHTML = resultEmptyHtml();
    renderDashboard();
    refreshEvents({ silent: true });
    window.setInterval(() => refreshEvents({ silent: true }), 1000);
    installScrollSpy();
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
  <title>Lịch sử kiểm tra</title>
  <style>
    :root {
      --font-body: "Aptos", "Segoe UI Variable Text", "Segoe UI", sans-serif;
      --font-heading: "Bahnschrift SemiBold", "Trebuchet MS", sans-serif;
      --radius-xl: 28px;
      --radius-lg: 22px;
      --shadow: 0 28px 80px rgba(18, 25, 35, 0.16);
      --shadow-soft: 0 16px 36px rgba(18, 25, 35, 0.10);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: var(--font-body);
      background:
        radial-gradient(circle at 14% 12%, var(--orb-a), transparent 22%),
        radial-gradient(circle at 82% 10%, var(--orb-b), transparent 20%),
        linear-gradient(180deg, var(--bg-main) 0%, var(--bg-alt) 100%);
      color: var(--text-main);
      transition: background 220ms ease, color 220ms ease;
    }

    body[data-theme="light"] {
      --bg-main: #eef7f1;
      --bg-alt: #f7fbf8;
      --orb-a: rgba(116, 177, 132, 0.20);
      --orb-b: rgba(75, 132, 182, 0.12);
      --text-main: #17241f;
      --text-soft: #5f7168;
      --line: rgba(36, 64, 50, 0.10);
      --panel: rgba(255, 255, 255, 0.88);
      --panel-strong: rgba(255, 255, 255, 0.96);
      --accent: #4f8f67;
      --accent-soft: rgba(79, 143, 103, 0.14);
      --safe: #3f8a58;
      --safe-soft: rgba(63, 138, 88, 0.14);
      --warn: #bf8537;
      --warn-soft: rgba(191, 133, 55, 0.16);
      --danger: #c55b72;
      --danger-soft: rgba(197, 91, 114, 0.14);
      --purple: #6f66b8;
      --purple-soft: rgba(111, 102, 184, 0.14);
      --blue: #4b84b6;
      --blue-soft: rgba(75, 132, 182, 0.14);
    }

    body[data-theme="dark"] {
      --bg-main: #110f1d;
      --bg-alt: #19142b;
      --orb-a: rgba(125, 87, 209, 0.18);
      --orb-b: rgba(58, 130, 188, 0.14);
      --text-main: #f4f3ff;
      --text-soft: #b3b6ca;
      --line: rgba(255, 255, 255, 0.10);
      --panel: rgba(24, 20, 39, 0.86);
      --panel-strong: rgba(25, 22, 42, 0.96);
      --accent: #8fd59d;
      --accent-soft: rgba(143, 213, 157, 0.16);
      --safe: #76d58f;
      --safe-soft: rgba(118, 213, 143, 0.16);
      --warn: #f0c06c;
      --warn-soft: rgba(240, 192, 108, 0.18);
      --danger: #ff8da8;
      --danger-soft: rgba(255, 141, 168, 0.18);
      --purple: #b9a5ff;
      --purple-soft: rgba(185, 165, 255, 0.18);
      --blue: #85bfff;
      --blue-soft: rgba(133, 191, 255, 0.18);
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    button,
    input,
    select {
      font: inherit;
    }

    .history-shell {
      width: min(1380px, calc(100% - 28px));
      margin: 18px auto 32px;
      display: grid;
      gap: 22px;
    }

    .topbar,
    .panel {
      padding: 20px 22px;
      border-radius: var(--radius-xl);
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
      backdrop-filter: blur(18px);
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      position: sticky;
      top: 16px;
      z-index: 10;
    }

    .topbar-left,
    .topbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .back-link,
    .theme-toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 11px 14px;
      border-radius: 999px;
      background: var(--panel-strong);
      border: 1px solid var(--line);
      color: var(--text-main);
      font-weight: 700;
      box-shadow: var(--shadow-soft);
      cursor: pointer;
    }

    .eyebrow {
      margin: 0;
      font-size: 12px;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      color: var(--text-soft);
    }

    .topbar h1 {
      margin: 4px 0 0;
      font-family: var(--font-heading);
      font-size: clamp(24px, 3vw, 32px);
      letter-spacing: -0.03em;
    }

    .top-chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--panel-strong);
      color: var(--text-soft);
      font-size: 13px;
      font-weight: 700;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(79, 143, 103, 0.12);
    }

    .hero {
      padding: 24px;
      border-radius: var(--radius-xl);
      background: linear-gradient(145deg, var(--accent-soft), rgba(255, 255, 255, 0.08)), var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }

    .hero h2 {
      margin: 10px 0 8px;
      font-family: var(--font-heading);
      font-size: clamp(28px, 4vw, 40px);
      letter-spacing: -0.04em;
    }

    .hero p {
      margin: 0;
      max-width: 880px;
      color: var(--text-soft);
      line-height: 1.7;
      font-size: 15px;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-top: 18px;
    }

    .summary-card {
      padding: 16px;
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.10);
      border: 1px solid var(--line);
    }

    .summary-card span {
      display: block;
      color: var(--text-soft);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .summary-card strong {
      display: block;
      margin-top: 8px;
      font-family: var(--font-heading);
      font-size: 30px;
      letter-spacing: -0.03em;
    }

    .controls {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 200px;
      gap: 12px;
      align-items: end;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field label {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-soft);
    }

    .field input,
    .field select {
      width: 100%;
      min-height: 54px;
      padding: 0 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: var(--panel-strong);
      color: var(--text-main);
    }

    .field input:focus,
    .field select:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 4px rgba(79, 143, 103, 0.12);
    }

    .table-shell {
      overflow: auto;
      border-radius: var(--radius-lg);
      background: var(--panel-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }

    table {
      width: 100%;
      min-width: 1080px;
      border-collapse: collapse;
    }

    thead th {
      padding: 15px 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-soft);
      background: rgba(255, 255, 255, 0.08);
    }

    tbody td {
      padding: 15px 16px;
      border-top: 1px solid var(--line);
      vertical-align: top;
      line-height: 1.55;
      font-size: 14px;
    }

    tbody tr {
      transition: background 180ms ease;
    }

    tbody tr:hover {
      background: rgba(255, 255, 255, 0.08);
    }

    .truncate {
      display: inline-block;
      max-width: 340px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-family: "Consolas", "Cascadia Code", monospace;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .badge-safe {
      background: var(--safe-soft);
      color: var(--safe);
      border-color: rgba(63, 138, 88, 0.18);
    }

    .badge-danger {
      background: var(--danger-soft);
      color: var(--danger);
      border-color: rgba(197, 91, 114, 0.18);
    }

    .badge-warning {
      background: var(--warn-soft);
      color: var(--warn);
      border-color: rgba(191, 133, 55, 0.18);
    }

    .badge-purple {
      background: var(--purple-soft);
      color: var(--purple);
      border-color: rgba(111, 102, 184, 0.18);
    }

    .badge-blue {
      background: var(--blue-soft);
      color: var(--blue);
      border-color: rgba(75, 132, 182, 0.18);
    }

    .muted {
      color: var(--text-soft);
      font-size: 13px;
    }

    .hidden {
      display: none !important;
    }

    .empty {
      padding: 22px;
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.10);
      border: 1px dashed var(--line);
      color: var(--text-soft);
      line-height: 1.7;
    }

    @media (max-width: 1000px) {
      .summary-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .controls {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .history-shell {
        width: calc(100% - 20px);
        margin: 10px auto 24px;
      }

      .topbar,
      .panel,
      .hero {
        padding: 18px;
      }

      .topbar {
        top: 10px;
        flex-direction: column;
        align-items: stretch;
      }

      .summary-grid {
        grid-template-columns: 1fr;
      }

      .theme-toggle,
      .back-link {
        width: 100%;
        justify-content: center;
      }
    }
  </style>
</head>
<body data-theme="dark">
  <main class="history-shell">
    <header class="topbar">
      <div class="topbar-left">
        <a class="back-link" href="{{ url_for('dashboard') }}">Quay lại bảng điều khiển</a>
        <button class="theme-toggle" id="theme-toggle" type="button">Sáng</button>
      </div>
      <div class="topbar-right">
        <div>
          <p class="eyebrow">Lịch sử</p>
          <h1>Log kiểm tra</h1>
        </div>
        <div class="top-chip">
          <span class="dot" aria-hidden="true"></span>
          <span>{{ summary.total_events }} lượt</span>
        </div>
      </div>
    </header>

    <section class="hero">
      <p class="eyebrow">Báo cáo</p>
      <h2>Toàn bộ log kiểm tra</h2>
      <div class="summary-grid">
        <article class="summary-card">
          <span>Tổng lượt</span>
          <strong>{{ summary.total_events }}</strong>
        </article>
        <article class="summary-card">
          <span>Cảnh báo</span>
          <strong>{{ summary.phishing_events }}</strong>
        </article>
        <article class="summary-card">
          <span>An toàn</span>
          <strong>{{ summary.benign_events }}</strong>
        </article>
        <article class="summary-card">
          <span>Mới nhất</span>
          <strong style="font-size: 22px;">{{ summary.latest_event_at or "Chưa có" }}</strong>
        </article>
      </div>
    </section>

    <section class="panel">
      <div class="controls">
        <div class="field">
          <label for="history-search">Tìm nhanh</label>
          <input id="history-search" type="search" placeholder="Tìm theo giá trị, nguồn, cảm biến...">
        </div>
        <div class="field">
          <label for="history-result">Kết quả</label>
          <select id="history-result">
            <option value="">Tất cả</option>
            <option value="phishing">Cảnh báo</option>
            <option value="benign">An toàn</option>
          </select>
        </div>
      </div>
    </section>

    <section class="panel">
      {% if events %}
      <div class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Loại</th>
              <th>Giá trị</th>
              <th>Risk</th>
              <th>Kết quả</th>
              <th>Ngữ cảnh</th>
              <th>Quyết định</th>
              <th>Mô hình</th>
            </tr>
          </thead>
          <tbody id="history-body">
            {% for event in events %}
            <tr data-result="{{ event.predicted_class }}" data-search="{{ (event.normalized_value ~ ' ' ~ event.source ~ ' ' ~ (event.sensor_name or '') ~ ' ' ~ event.ids_event_type ~ ' ' ~ (event.flow_summary or ''))|lower }}">
              <td>
                <div>{{ event.received_at }}</div>
                <div class="muted">{{ event.observed_at or event.received_at }}</div>
              </td>
              <td>
                <span class="badge {% if event.dataset_kind == 'url' %}badge-blue{% else %}badge-purple{% endif %}">
                  {{ event.dataset_kind }}
                </span>
              </td>
              <td><code class="truncate">{{ event.normalized_value }}</code></td>
              <td>
                <span class="badge {% if event.risk_level == 'high' %}badge-danger{% elif event.risk_level == 'medium' %}badge-warning{% elif event.risk_level == 'low' %}badge-blue{% else %}badge-safe{% endif %}">
                  {% if event.risk_level == 'high' %}HIGH{% elif event.risk_level == 'medium' %}MEDIUM{% elif event.risk_level == 'low' %}LOW{% else %}MINIMAL{% endif %}
                </span>
              </td>
              <td>
                <span class="badge {% if event.predicted_class == 'phishing' %}badge-danger{% else %}badge-safe{% endif %}">
                  {% if event.predicted_class == 'phishing' %}CẢNH BÁO{% else %}AN TOÀN{% endif %}
                </span>
              </td>
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
      <div class="empty hidden" id="history-empty">Không có dòng nào phù hợp với bộ lọc hiện tại.</div>
      {% else %}
      <div class="empty">Chưa có log. Hãy gửi thử một domain hoặc URL rồi mở lại trang này.</div>
      {% endif %}
    </section>
  </main>

  <script>
    const themeToggle = document.getElementById("theme-toggle");
    const historySearch = document.getElementById("history-search");
    const historyResult = document.getElementById("history-result");
    const historyBody = document.getElementById("history-body");
    const historyEmpty = document.getElementById("history-empty");

    const applyTheme = (theme) => {
      const resolvedTheme = theme === "dark" ? "dark" : "light";
      document.body.dataset.theme = resolvedTheme;
      localStorage.setItem("phishing_checker:theme", resolvedTheme);
      if (themeToggle) {
        themeToggle.textContent = resolvedTheme === "dark" ? "Sáng" : "Tối";
      }
    };

    const loadTheme = () => {
      const storedTheme = localStorage.getItem("phishing_checker:theme");
      if (storedTheme) {
        applyTheme(storedTheme);
        return;
      }
      applyTheme("dark");
    };

    const applyFilters = () => {
      if (!historyBody) {
        return;
      }
      const keyword = historySearch.value.trim().toLowerCase();
      const result = historyResult.value;
      let visibleCount = 0;
      [...historyBody.querySelectorAll("tr")].forEach((row) => {
        const matchesResult = !result || row.dataset.result === result;
        const matchesSearch = !keyword || (row.dataset.search || "").includes(keyword);
        const visible = matchesResult && matchesSearch;
        row.classList.toggle("hidden", !visible);
        if (visible) {
          visibleCount += 1;
        }
      });
      if (historyEmpty) {
        historyEmpty.classList.toggle("hidden", visibleCount !== 0);
      }
    };

    loadTheme();

    if (themeToggle) {
      themeToggle.addEventListener("click", () => {
        applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
      });
    }

    if (historySearch) {
      historySearch.addEventListener("input", applyFilters);
    }

    if (historyResult) {
      historyResult.addEventListener("change", applyFilters);
    }
  </script>
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
        "mô hình + danh sách an toàn"
        if decorated.get("decision_mode") == "model_plus_curated_benign_override"
        else "mô hình"
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
        events = decorate_events(load_events(limit=200))
        summary = summarize_events(events)
        return render_template_string(
            DASHBOARD_TEMPLATE,
            events=events,
            summary=summary,
            model_cards=official_model_cards(),
        )

    @app.get("/dashboard/events")
    def dashboard_events():
        events = decorate_events(load_events(limit=500))
        return render_template_string(
            EVENT_HISTORY_TEMPLATE,
            events=events,
            summary=summarize_events(events),
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
