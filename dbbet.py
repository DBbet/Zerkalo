"""
DBbet Mirror Resolver
"""

import time
import socket
import hashlib
from urllib.parse import urlparse
import requests


class MirrorNode:
    def __init__(self, url: str):
        self.url = url
        self.parsed = urlparse(url)
        self.hostname = self.parsed.hostname

    def dns_resolves(self) -> bool:
        try:
            socket.gethostbyname(self.hostname)
            return True
        except socket.gaierror:
            return False

    def latency(self) -> float:
        start = time.time()
        try:
            requests.get(self.url, timeout=3)
            return time.time() - start
        except Exception:
            return float("inf")

    def fingerprint(self) -> str:
        try:
            r = requests.get(self.url, timeout=5)
            return hashlib.sha256(r.text.encode()).hexdigest()
        except Exception:
            return "unreachable"

    def health_score(self) -> float:
        if not self.dns_resolves():
            return float("inf")
        return self.latency()


class MirrorCluster:
    def __init__(self, mirrors: list[str]):
        self.nodes = [MirrorNode(m) for m in mirrors]

    def select_optimal(self) -> MirrorNode | None:
        healthy = sorted(self.nodes, key=lambda n: n.health_score())
        return healthy[0] if healthy and healthy[0].health_score() != float("inf") else None

    def topology_report(self) -> dict:
        report = {}
        for node in self.nodes:
            report[node.url] = {
                "dns": node.dns_resolves(),
                "latency": node.latency(),
                "fingerprint": node.fingerprint(),
            }
        return report


if __name__ == "__main__":
    mirrors = [
        "https://dbbet.com",
        "https://dbbet-mirror1.com",
        "https://dbbet-alt.net",
    ]

    cluster = MirrorCluster(mirrors)

    optimal = cluster.select_optimal()

    if optimal:
        print(f"[OK] Selected mirror: {optimal.url}")
    else:
        print("[FAIL] No reachable mirrors")

    print("\nTopology diagnostics:")
    for url, meta in cluster.topology_report().items():
        print(f"{url} -> {meta}")