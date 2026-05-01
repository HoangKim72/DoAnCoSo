from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from phishing_url_ml.settings import BASE_DIR, DEMO_VALID_ALLOWLIST_PATH
from phishing_url_ml.utils import ensure_parent_dir


DEFAULT_OUTPUT_PATH = BASE_DIR / "data" / "demo" / "demo_suricata_eve.json"
DEFAULT_MANIFEST_PATH = BASE_DIR / "data" / "demo" / "demo_suricata_eve_manifest.csv"
DEFAULT_RUNTIME_PATCH_PATH = DEMO_VALID_ALLOWLIST_PATH
DEMO_TZ = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class DemoVisit:
    event_type: str
    expected_class: str
    hostname: str
    target: str
    note: str


HTTP_BENIGN = [
    ("vnexpress.net", "/thoi-su/chinh-sach-moi.html", "news benign"),
    ("tuoitre.vn", "/giao-duc/tuyen-sinh-2026.htm", "news benign"),
    ("thanhnien.vn", "/cong-nghe/chuyen-doi-so-185260501.htm", "news benign"),
    ("dantri.com.vn", "/xa-hoi/lich-nghi-le-2026.htm", "news benign"),
    ("laodong.vn", "/kinh-doanh/thi-truong-hom-nay-2026.htm", "news benign"),
    ("nhandan.vn", "/van-hoa/tin-moi.html", "news benign"),
    ("vietnamnet.vn", "/giao-duc/hoc-bong-dai-hoc-2026.html", "news benign"),
    ("baochinhphu.vn", "/tin-tuc/chi-dao-dieu-hanh-2026.htm", "government benign"),
    ("chinhphu.vn", "/du-thao-van-ban", "government benign"),
    ("moh.gov.vn", "/tin-lien-quan-y-te", "government benign"),
    ("moet.gov.vn", "/tin-tuc/Pages/tin-tong-hop.aspx", "government benign"),
    ("mic.gov.vn", "/Pages/TinTuc/140001/chuyen-doi-so.html", "government benign"),
    ("hcmus.edu.vn", "/dao-tao/thong-bao", "university benign"),
    ("fit.hcmus.edu.vn", "/tin-tuc", "university benign"),
    ("hutech.edu.vn", "/tuyen-sinh-dai-hoc", "university benign"),
    ("uit.edu.vn", "/sinh-vien/thong-bao", "university benign"),
    ("hcmut.edu.vn", "/vi/news/tin-tuc", "university benign"),
    ("ctu.edu.vn", "/dao-tao/thong-bao", "university benign"),
    ("ueh.edu.vn", "/dao-tao", "university benign"),
    ("vnu.edu.vn", "/home/?C1654", "university benign"),
    ("vietcombank.com.vn", "/vi-VN/Trang-chu", "banking benign"),
    ("bidv.com.vn", "/vn/ca-nhan", "banking benign"),
    ("acb.com.vn", "/ca-nhan", "banking benign"),
    ("techcombank.com", "/khach-hang-ca-nhan", "banking benign"),
    ("mbbank.com.vn", "/ca-nhan", "banking benign"),
    ("tpb.vn", "/ca-nhan", "banking benign"),
    ("agribank.com.vn", "/vn/ca-nhan", "banking benign"),
    ("vpbank.com.vn", "/ca-nhan", "banking benign"),
    ("cellphones.com.vn", "/mobile/samsung.html", "commerce benign"),
    ("fptshop.com.vn", "/may-tinh-xach-tay", "commerce benign"),
    ("thegioididong.com", "/dtdd", "commerce benign"),
    ("dienmayxanh.com", "/may-lanh", "commerce benign"),
    ("tiki.vn", "/dien-thoai-may-tinh-bang/c1789", "commerce benign"),
    ("shopee.vn", "/search?keyword=sach%20lap%20trinh", "commerce benign"),
    ("lazada.vn", "/catalog/?q=ban%20phim", "commerce benign"),
    ("github.com", "/openai/openai-python", "developer benign"),
    ("stackoverflow.com", "/questions/tagged/python", "developer benign"),
    ("docs.python.org", "/3/library/json.html", "developer benign"),
    ("pypi.org", "/project/requests/", "developer benign"),
    ("microsoft.com", "/vi-vn/microsoft-365", "software benign"),
    ("support.google.com", "/accounts/answer/61416", "support benign"),
    ("cloudflare.com", "/learning/security/", "security benign"),
    ("wikipedia.org", "/wiki/Phishing", "reference benign"),
    ("coursera.org", "/learn/machine-learning", "learning benign"),
    ("edx.org", "/learn/cybersecurity", "learning benign"),
    ("openai.com", "/api/", "technology benign"),
    ("apnews.com", "/world-news", "news benign"),
    ("bbc.com", "/news/technology", "news benign"),
    ("reuters.com", "/world/", "news benign"),
    ("npr.org", "/sections/technology/", "news benign"),
    ("paypal.com", "/vn/home", "brand benign"),
    ("accounts.google.com", "/ServiceLogin", "brand login benign"),
    ("login.microsoftonline.com", "/common/oauth2/v2.0/authorize", "brand login benign"),
    ("apple.com", "/vn/icloud/", "brand benign"),
    ("amazon.com", "/gp/help/customer/display.html", "commerce support benign"),
    ("netflix.com", "/vn-en/login", "brand login benign"),
    ("linkedin.com", "/login", "brand login benign"),
    ("facebook.com", "/login/", "brand login benign"),
    ("youtube.com", "/feed/subscriptions", "media benign"),
    ("zalo.me", "/pc", "messaging benign"),
]


HTTP_HARD_BENIGN = [
    ("red.moj.gov.vn", "/cas/login?service=https%3A%2F%2Fmoj.gov.vn%2FPages%2Fhome.aspx", "government CAS login benign"),
    ("tuyensinh.moet.gov.vn", "/Account/Login?ReturnUrl=%2F", "government ReturnUrl benign"),
    ("daotao.hutech.edu.vn", "/default.aspx?flag=XemDiemThi&page=nhapmasv", "university .aspx portal benign"),
    ("hocvudientu.hutech.edu.vn", "/dang-nhap?ReturnUrl=%2F", "university login benign"),
    ("sinhvien1.hutech.edu.vn", "/elearning/hoc-vu/lich-thi", "university portal benign"),
    ("online.acb.com.vn", "/acbib/Request?dse_sessionId=student-demo", "banking Request benign"),
    ("vietcombank.com.vn", "/dang-nhap-dich-vu-vcb-digibank", "banking login info benign"),
    ("webdaotao.hutech.edu.vn", "/daotao/default.aspx?page=nhapmasv", "university .aspx benign"),
    ("mail.moet.gov.vn", "/", "government mail benign"),
    ("moet.gov.vn", "/page/login", "government login benign"),
]


HTTP_PHISHING = [
    ("paypal-account-security-check.com", "/account/reset?token=8932", "paypal phishing simulation"),
    ("secure-paypal-login.verify-session.com", "/signin/confirm", "brand subdomain phishing simulation"),
    ("microsoft365-login-verify.com", "/common/oauth2/authorize?client_id=office", "microsoft phishing simulation"),
    ("account-google-security-alert.com", "/ServiceLogin?continue=mail", "google phishing simulation"),
    ("vietcombank-digibank-secure.com", "/dang-nhap/kiem-tra-tai-khoan", "banking phishing simulation"),
    ("acb-online-verify.com", "/acbib/Request?session=expired", "banking phishing simulation"),
    ("techcombank-login-business.com", "/dang-nhap-ngan-hang-so", "banking phishing simulation"),
    ("binance-wallet-verify-login.com", "/wallet/restore?seed=confirm", "crypto phishing simulation"),
    ("metamask-verify-wallet.com", "/import-wallet", "crypto phishing simulation"),
    ("www.purchaseordersale.com.wellscreditfargo.com", "/", "brand-subdomain spoof simulation"),
    ("fasoasio-dtfhevakagcrhtcs.z02.azurefd.net", "/WinAbhwebsi018/index.html?ph0nq=null", "cloud-edge portal phishing simulation"),
    ("delivery-vnpost-confirm.com", "/tracking/login?ReturnUrl=%2Fparcel", "delivery phishing simulation"),
    ("invoice-sharepoint-docs.com", "/onedrive/login?file=invoice.pdf", "cloud docs phishing simulation"),
    ("student-hcmus-portal-check.com", "/dang-nhap?ReturnUrl=%2Fhocphi", "university portal phishing simulation"),
    ("gov-vn-dichvucong-login.com", "/Account/Login?ReturnUrl=%2F", "government phishing simulation"),
]


TLS_VISITS = [
    DemoVisit("tls", "benign", "mail.chinhphu.vn", "", "TLS SNI benign domain fallback"),
    DemoVisit("tls", "benign", "ctd.ueh.edu.vn", "", "TLS SNI benign domain fallback"),
    DemoVisit("tls", "benign", "portal.hcmus.edu.vn", "", "TLS SNI benign domain fallback"),
    DemoVisit("tls", "benign", "vcbdigibank.vietcombank.com.vn", "", "TLS SNI benign domain fallback"),
    DemoVisit("tls", "phishing", "accounts.binanceuz.co", "", "TLS SNI phishing fallback"),
    DemoVisit("tls", "phishing", "login-paypal-security-alert.com", "", "TLS SNI phishing fallback"),
    DemoVisit("tls", "phishing", "secure-microsoft-verify-login.com", "", "TLS SNI phishing fallback"),
    DemoVisit("tls", "phishing", "wallet-metamask-support.com", "", "TLS SNI phishing fallback"),
]


DNS_VISITS = [
    DemoVisit("dns", "benign", "en.uit.edu.vn", "", "DNS benign domain fallback"),
    DemoVisit("dns", "benign", "letienchau.chinhphu.vn", "", "DNS benign domain fallback"),
    DemoVisit("dns", "benign", "nguyenvanthang.chinhphu.vn", "", "DNS benign domain fallback"),
    DemoVisit("dns", "phishing", "paypal-login-session-check.com", "", "DNS phishing fallback"),
    DemoVisit("dns", "phishing", "bank-account-update-required.com", "", "DNS phishing fallback"),
    DemoVisit("dns", "phishing", "office365-password-expired.com", "", "DNS phishing fallback"),
    DemoVisit("dns", "phishing", "crypto-wallet-connect-verify.com", "", "DNS phishing fallback"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic Suricata eve.json demo log that simulates "
            "a user browsing mostly HTTP websites."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSONL eve log path.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="CSV manifest describing expected scenario labels.",
    )
    parser.add_argument(
        "--runtime-patch",
        type=Path,
        default=DEFAULT_RUNTIME_PATCH_PATH,
        help="CSV runtime allowlist for benign URLs/domains used in this demo scenario.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def build_visits() -> list[DemoVisit]:
    visits: list[DemoVisit] = []
    visits.extend(DemoVisit("http", "benign", host, target, note) for host, target, note in HTTP_BENIGN)
    visits.extend(DemoVisit("http", "benign", host, target, note) for host, target, note in HTTP_HARD_BENIGN)
    visits.extend(DemoVisit("http", "phishing", host, target, note) for host, target, note in HTTP_PHISHING)
    visits.extend(TLS_VISITS)
    visits.extend(DNS_VISITS)
    if len(visits) != 100:
        raise ValueError(f"Demo visit list must contain exactly 100 entries, got {len(visits)}.")
    return mix_benign_and_phishing(visits)


def mix_benign_and_phishing(visits: list[DemoVisit]) -> list[DemoVisit]:
    benign = [visit for visit in visits if visit.expected_class == "benign"]
    phishing = [visit for visit in visits if visit.expected_class == "phishing"]
    mixed: list[DemoVisit] = []
    phishing_emitted = 0
    phishing_total = len(phishing)
    total = len(visits)

    for position in range(total):
        target_phishing = round(((position + 1) * phishing_total) / total)
        should_emit_phishing = phishing and target_phishing > phishing_emitted
        if should_emit_phishing:
            mixed.append(phishing.pop(0))
            phishing_emitted += 1
        elif benign:
            mixed.append(benign.pop(0))
        elif phishing:
            mixed.append(phishing.pop(0))

    return mixed


def event_timestamp(index: int, base_time: datetime) -> str:
    return (base_time + timedelta(seconds=index * 17)).isoformat(timespec="seconds")


def demo_ip(index: int, *, offset: int = 0) -> str:
    return f"203.0.113.{((index + offset) % 240) + 10}"


def build_suricata_event(index: int, visit: DemoVisit, base_time: datetime) -> dict[str, Any]:
    common = {
        "timestamp": event_timestamp(index, base_time),
        "flow_id": 900000000000 + index,
        "in_iface": "lab0",
        "event_index": index,
        "src_ip": "192.168.56.24",
        "src_port": 51000 + index,
        "dest_ip": demo_ip(index),
        "dest_port": 80,
        "proto": "TCP",
        "app_proto": visit.event_type,
        "demo_expected_class": visit.expected_class,
        "demo_note": visit.note,
    }

    if visit.event_type == "http":
        return {
            **common,
            "event_type": "http",
            "http": {
                "hostname": visit.hostname,
                "url": visit.target or "/",
                "http_method": "GET",
                "protocol": "HTTP/1.1",
                "status": 200 if visit.expected_class == "benign" else 302,
            },
        }

    if visit.event_type == "tls":
        return {
            **common,
            "event_type": "tls",
            "dest_port": 443,
            "app_proto": "tls",
            "tls": {
                "sni": visit.hostname,
                "version": "TLS 1.3",
                "subject": f"CN={visit.hostname}",
            },
        }

    if visit.event_type == "dns":
        return {
            **common,
            "event_type": "dns",
            "dest_ip": "192.168.56.1",
            "dest_port": 53,
            "proto": "UDP",
            "app_proto": "dns",
            "dns": {
                "type": "query",
                "rrname": visit.hostname,
                "rrtype": "A",
            },
        }

    raise ValueError(f"Unsupported event type: {visit.event_type}")


def manifest_value(visit: DemoVisit) -> str:
    if visit.event_type == "http":
        target = visit.target or "/"
        if target.startswith(("http://", "https://")):
            return target
        if not target.startswith("/"):
            target = f"/{target}"
        return f"http://{visit.hostname}{target}"
    return visit.hostname


def https_variant(url_value: str) -> str:
    if url_value.startswith("http://"):
        return "https://" + url_value[len("http://") :]
    return url_value


def write_outputs(
    visits: list[DemoVisit],
    output_path: Path,
    manifest_path: Path,
    runtime_patch_path: Path,
    base_time: datetime,
) -> None:
    ensure_parent_dir(output_path)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for index, visit in enumerate(visits, start=1):
            handle.write(json.dumps(build_suricata_event(index, visit, base_time), ensure_ascii=True))
            handle.write("\n")

    ensure_parent_dir(manifest_path)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["event_index", "event_type", "expected_class", "value", "note"],
        )
        writer.writeheader()
        for index, visit in enumerate(visits, start=1):
            writer.writerow(
                {
                    "event_index": index,
                    "event_type": visit.event_type,
                    "expected_class": visit.expected_class,
                    "value": manifest_value(visit),
                    "note": visit.note,
                }
            )

    benign_visits = [visit for visit in visits if visit.expected_class == "benign"]
    ensure_parent_dir(runtime_patch_path)
    with runtime_patch_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rule_type",
                "match_value",
                "dataset_kind",
                "expected_class",
                "collected_at",
                "source",
                "category",
                "source_name",
                "note",
            ],
        )
        writer.writeheader()
        emitted_rules: set[tuple[str, str]] = set()

        def write_rule(rule_type: str, match_value: str, dataset_kind: str, hostname: str, note: str) -> None:
            key = (rule_type, match_value.lower())
            if key in emitted_rules:
                return
            emitted_rules.add(key)
            writer.writerow(
                {
                    "rule_type": rule_type,
                    "match_value": match_value,
                    "dataset_kind": dataset_kind,
                    "expected_class": "benign",
                    "collected_at": base_time.date().isoformat(),
                    "source": "ids_demo_valid_allowlist",
                    "category": "demo_benign_input",
                    "source_name": hostname.upper(),
                    "note": note,
                }
            )

        for visit in benign_visits:
            write_rule(
                "exact_hostname",
                visit.hostname,
                "domain",
                visit.hostname,
                "Known-valid benign domain/hostname in the IDS demo scenario.",
            )
            if visit.event_type == "http":
                http_url = manifest_value(visit)
                write_rule(
                    "exact_url",
                    http_url,
                    "url",
                    visit.hostname,
                    "Known-valid benign HTTP URL in the IDS demo scenario.",
                )
                write_rule(
                    "exact_url",
                    https_variant(http_url),
                    "url",
                    visit.hostname,
                    "HTTPS equivalent of a known-valid benign demo URL.",
                )


def main() -> None:
    args = parse_args()
    output_path = resolve_repo_path(args.output)
    manifest_path = resolve_repo_path(args.manifest)
    runtime_patch_path = resolve_repo_path(args.runtime_patch)
    visits = build_visits()
    base_time = datetime.now(DEMO_TZ).replace(microsecond=0)
    write_outputs(visits, output_path, manifest_path, runtime_patch_path, base_time)

    counts: dict[tuple[str, str], int] = {}
    for visit in visits:
        key = (visit.event_type, visit.expected_class)
        counts[key] = counts.get(key, 0) + 1

    print(f"Wrote {len(visits)} demo IDS events to {output_path}")
    print(f"Wrote demo manifest to {manifest_path}")
    print(f"Wrote demo valid URL/domain allowlist to {runtime_patch_path}")
    print(f"First event timestamp: {event_timestamp(1, base_time)}")
    for (event_type, expected_class), count in sorted(counts.items()):
        print(f"{event_type}/{expected_class}: {count}")


if __name__ == "__main__":
    main()
