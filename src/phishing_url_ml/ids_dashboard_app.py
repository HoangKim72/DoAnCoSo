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
  <title>IDS Phishing Dashboard</title>
  <style>
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
      width: min(1260px, calc(100% - 28px));
      margin: 20px auto 44px;
      animation: reveal 0.5s ease;
    }
    .hero {
      position: relative;
      overflow: hidden;
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.3fr) minmax(260px, 0.7fr);
      padding: 30px;
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
      font-size: clamp(32px, 4vw, 48px);
      line-height: 1.02;
      letter-spacing: -0.03em;
    }
    .lead {
      max-width: 720px;
      margin: 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.7;
    }
    .hero-rail {
      display: grid;
      gap: 12px;
      align-content: start;
    }
    .hero-block {
      padding: 16px 18px;
      border-radius: 22px;
      background: rgba(248, 251, 250, 0.92);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .hero-kicker {
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .hero-stat {
      margin-bottom: 4px;
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.03em;
    }
    .hero-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
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
      margin-top: 18px;
      padding: 24px;
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
      gap: 16px;
    }
    .stats {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
    .models {
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    }
    .card {
      padding: 18px;
      border-radius: 22px;
      background: var(--surface-strong);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .stat-value {
      margin-bottom: 8px;
      font-size: 34px;
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
      min-width: 240px;
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
      display: none;
      margin-top: 10px;
      padding: 18px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: var(--surface-strong);
      box-shadow: var(--shadow-soft);
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
    @keyframes reveal {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (max-width: 980px) {
      .hero { grid-template-columns: 1fr; }
      .metric-ribbon { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 860px) {
      .form-row { grid-template-columns: 1fr; }
      .form-actions { flex-direction: column; align-items: stretch; }
      button { width: 100%; }
      .metric-ribbon { grid-template-columns: 1fr; }
      .section-head { flex-direction: column; align-items: stretch; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <span class="eyebrow">IDS + Dashboard</span>
        <h1>Phishing Detection Console</h1>
        <p class="lead">
          Giao diện giám sát dành cho nhánh IDS của dự án, tập trung vào kiểm tra nhanh, xem cảnh báo mới và theo dõi 2 model official theo thời gian thực.
        </p>
        <div class="hero-meta">
          <span class="hero-pill">Live event log</span>
          <span class="hero-pill">Official domain + URL models</span>
        </div>
      </div>
      <div class="hero-rail">
        <div class="hero-block">
          <div class="hero-kicker">Latest Event</div>
          <div class="hero-stat">{{ summary.latest_event_at or "Chưa có" }}</div>
          <div class="muted">Mốc sự kiện mới nhất đang có trong runtime log.</div>
        </div>
        <div class="hero-block">
          <div class="hero-kicker">Traffic Mix</div>
          <div class="hero-stat">{{ summary.domain_events }}/{{ summary.url_events }}</div>
          <div class="muted">Domain events / URL events</div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2>Tổng quan</h2>
          <p class="section-note">4 chỉ số ngắn gọn để nhìn nhanh hoạt động gần đây của dashboard.</p>
        </div>
        <span class="info-tip">
          <span class="info-dot">i</span>
          <span class="tooltip tooltip-wide">
            <strong>Các số này được tính từ đâu?</strong><br>
            Dashboard đọc trực tiếp từ <code>data/runtime/ids_events.jsonl</code> và tổng hợp số sự kiện, số lần bị gắn nhãn phishing, số cảnh báo high và tỉ lệ domain/url.
          </span>
        </span>
      </div>
      <div class="grid stats">
        <article class="card">
          <div class="stat-value">{{ summary.total_events }}</div>
          <div class="stat-label">Tổng sự kiện đã ghi</div>
          <div class="stat-meta">
            <span class="soft-pill">Runtime</span>
          </div>
        </article>
        <article class="card">
          <div class="stat-value">{{ summary.phishing_events }}</div>
          <div class="stat-label">Sự kiện bị gắn nhãn phishing</div>
          <div class="stat-meta">
            <span class="soft-pill">Predicted phishing</span>
          </div>
        </article>
        <article class="card">
          <div class="stat-value">{{ summary.high_risk_events }}</div>
          <div class="stat-label">Cảnh báo mức high</div>
          <div class="stat-meta">
            <span class="soft-pill">Risk high</span>
          </div>
        </article>
        <article class="card">
          <div class="stat-value">{{ summary.domain_events }}/{{ summary.url_events }}</div>
          <div class="stat-label">Domain events / URL events</div>
          <div class="stat-meta">
            <span class="soft-pill">Traffic split</span>
          </div>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2>Manual Check</h2>
          <p class="section-note">Nhập domain hoặc URL để mô phỏng luồng dữ liệu đi vào IDS.</p>
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
        <div class="form-row">
          <div class="field">
            <label for="dataset_kind">Loại input</label>
            <select id="dataset_kind" name="dataset_kind">
              <option value="domain" selected>Domain</option>
              <option value="url">URL</option>
              <option value="auto">Auto detect</option>
            </select>
          </div>
          <div class="field">
            <label for="value">Domain hoặc URL</label>
            <input id="value" name="value" placeholder="ví dụ: secure-paypal-check.com hoặc https://example.com/login" required>
          </div>
          <div class="field">
            <label for="source">Nguồn sự kiện</label>
            <input id="source" name="source" value="ids_browser_sensor">
          </div>
        </div>
        <div class="form-actions">
          <button type="submit">Check và ghi vào dashboard</button>
          <div class="micro-meta">
            <span class="soft-pill">POST /api/ingest</span>
            <span class="info-tip inline">
              <span class="info-dot">i</span>
              <span class="tooltip tooltip-wide">
                <strong>Payload tối thiểu</strong><br>
                <code>{"value":"...", "dataset_kind":"domain"}</code>
              </span>
            </span>
          </div>
        </div>
      </form>
      <div id="result-panel"></div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2>Official Models</h2>
          <p class="section-note">Card tóm tắt nhanh cấu hình đang được dashboard sử dụng.</p>
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
        <article class="card model-card">
          <div class="card-top">
            <span class="model-chip">{{ card.dataset_kind }}</span>
            <span class="info-tip inline">
              <span class="info-dot">i</span>
              <span class="tooltip tooltip-wide">
                <strong>Variant</strong><br>
                <code>{{ card.variant_name }}</code><br><br>
                <strong>Dataset</strong><br>
                Rows: {{ "{:,}".format(card.rows) }}<br>
                Benign: {{ "{:,}".format(card.benign) }}<br>
                Phishing: {{ "{:,}".format(card.phishing) }}<br>
                Features: {{ card.feature_count }}
              </span>
            </span>
          </div>
          <h3>{{ card.model_name }}</h3>
          <div class="metric-ribbon">
            <div class="metric-box">
              <span class="metric-label">Val PR-AUC</span>
              <strong>{{ "%.4f"|format(card.validation_pr_auc) }}</strong>
            </div>
            <div class="metric-box">
              <span class="metric-label">Test PR-AUC</span>
              <strong>{{ "%.4f"|format(card.test_pr_auc) }}</strong>
            </div>
            <div class="metric-box">
              <span class="metric-label">Test F1</span>
              <strong>{{ "%.4f"|format(card.test_f1) }}</strong>
            </div>
          </div>
          <div class="card-footer">
            <span class="tiny">Variant</span>
            <code>{{ card.variant_name }}</code>
          </div>
        </article>
        {% endfor %}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2>Recent IDS Events</h2>
          <p class="section-note">Log gần đây được rút gọn để tập trung vào input, score và mức rủi ro.</p>
        </div>
        <span class="info-tip">
          <span class="info-dot">i</span>
          <span class="tooltip tooltip-wide">
            <strong>Thông tin ẩn trong bảng</strong><br>
            Mỗi dòng có icon <strong>i</strong> để xem thêm model đã dùng, source event và các tín hiệu nổi bật thay vì hiển thị dài trực tiếp trên bảng.
          </span>
        </span>
      </div>
      <div class="table-wrap">
        {% if events %}
        <table>
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Loại</th>
              <th>Input</th>
              <th>Điểm</th>
              <th>Risk</th>
              <th>Kết quả</th>
              <th>Chi tiết</th>
            </tr>
          </thead>
          <tbody>
            {% for event in events %}
            <tr>
              <td>{{ event.received_at }}</td>
              <td><span class="model-chip">{{ event.dataset_kind }}</span></td>
              <td><code class="table-input">{{ event.normalized_value }}</code></td>
              <td>{{ "%.4f"|format(event.score) }}</td>
              <td><span class="risk-chip risk-{{ event.risk_level }}">{{ event.risk_level }}</span></td>
              <td>{{ event.predicted_class }}</td>
              <td>
                <div class="table-note">
                  <span class="note-chip">{{ event.source }}</span>
                  <span class="info-tip inline">
                    <span class="info-dot">i</span>
                    <span class="tooltip tooltip-wide">
                      <strong>Model</strong><br>
                      {{ event.model_name }}<br><br>
                      <strong>Signals</strong>
                      {% if event.signals %}
                      <div class="signal-list">
                        {% for signal in event.signals %}
                        <div class="signal-line">• {{ signal }}</div>
                        {% endfor %}
                      </div>
                      {% else %}
                      <div class="signal-list">
                        <div class="signal-line">Không có tín hiệu nổi bật.</div>
                      </div>
                      {% endif %}
                    </span>
                  </span>
                </div>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
        <div class="empty">Chưa có sự kiện nào. Hãy gửi thử một domain hoặc URL ở form phía trên.</div>
        {% endif %}
      </div>
    </section>
  </main>

  <script>
    const form = document.getElementById("ingest-form");
    const resultPanel = document.getElementById("result-panel");
    const escapeHtml = (value) => String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

    const tooltipHtml = (content, extraClass = "") => `
      <span class="info-tip inline">
        <span class="info-dot">i</span>
        <span class="tooltip ${extraClass}">${content}</span>
      </span>
    `;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = {
        dataset_kind: document.getElementById("dataset_kind").value,
        value: document.getElementById("value").value,
        source: document.getElementById("source").value,
      };

      const response = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      resultPanel.style.display = "block";

      if (!response.ok) {
        resultPanel.innerHTML = `<strong>Lỗi:</strong> ${escapeHtml(data.error)}`;
        resultPanel.style.borderColor = "rgba(196, 85, 82, 0.35)";
        return;
      }

      resultPanel.style.borderColor = "rgba(28, 123, 119, 0.24)";
      const recommendationTip = tooltipHtml(
        `<strong>Khuyến nghị</strong><br>${escapeHtml(data.recommendation)}`,
        "tooltip-wide"
      );
      const signals = Array.isArray(data.signals) ? data.signals : [];
      const signalsTip = tooltipHtml(
        signals.length
          ? `<strong>Tín hiệu nổi bật</strong><div class="signal-list">${signals.map((signal) => `<div class="signal-line">• ${escapeHtml(signal)}</div>`).join("")}</div>`
          : `<strong>Tín hiệu nổi bật</strong><div class="signal-list"><div class="signal-line">Không có tín hiệu nổi bật.</div></div>`,
        "tooltip-wide"
      );

      resultPanel.innerHTML = `
        <div class="result-top">
          <div>
            <div class="risk-chip risk-${escapeHtml(data.risk_level)}">${escapeHtml(data.risk_level)}</div>
            <h3 class="result-title">${escapeHtml(data.predicted_class.toUpperCase())} - score ${Number(data.score).toFixed(4)}</h3>
          </div>
          <div class="inline-stack">${recommendationTip}</div>
        </div>
        <div class="result-grid">
          <div class="result-item">
            <span>Normalized</span>
            <code>${escapeHtml(data.normalized_value)}</code>
          </div>
          <div class="result-item">
            <span>Model</span>
            <strong>${escapeHtml(data.model_name)}</strong>
          </div>
          <div class="result-item">
            <span>Variant</span>
            <strong>${escapeHtml(data.variant_name)}</strong>
          </div>
          <div class="result-item">
            <span>Tín hiệu</span>
            <div class="inline-stack">
              <strong>${signals.length}</strong>
              ${signalsTip}
            </div>
          </div>
        </div>
      `;
      window.setTimeout(() => window.location.reload(), 900);
    });
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
        events = load_events(limit=100)
        summary = summarize_events(events)
        return render_template_string(
            DASHBOARD_TEMPLATE,
            events=events,
            summary=summary,
            model_cards=official_model_cards(),
        )

    @app.get("/api/events")
    def api_events():
        try:
            limit = int(request.args.get("limit", 100))
        except ValueError:
            return error_response("`limit` must be an integer.")
        events = load_events(limit=max(1, min(limit, 500)))
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
        return jsonify(result)

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
        return jsonify(result), 201

    return app
