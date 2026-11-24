from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(r"D:\大學\專題\MUS_Project_v2")
DATA_DIR = Path(r"D:\大學\專題\測試資料")
THESIS_DIR = ROOT / "論文"
FIG_DIR = THESIS_DIR / "圖表"
OUT_TEX = THESIS_DIR / "實驗結果與比較.tex"

PRIMARY_CSV = DATA_DIR / "batch_test_results.csv"
SIMILARITY_CSV = DATA_DIR / "batch_test_results_v1.csv"


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() == "TRUE"


def escape_latex(text: object) -> str:
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def load_results(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for column in ["elapsed_ms", "top1_confidence", "top2_confidence", "top1_similarity", "top2_similarity"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["top1_match", "truth_in_top2", "success", "fallback_used"]:
        if column in df.columns:
            df[column] = df[column].map(parse_bool)
    return df


def summarize(df: pd.DataFrame, method_name: str) -> dict[str, object]:
    total = len(df)
    success_rate = float(df["success"].mean()) if "success" in df.columns and total else 0.0
    top1_rate = float(df["top1_match"].mean()) if "top1_match" in df.columns and total else 0.0
    top2_rate = float(df["truth_in_top2"].mean()) if "truth_in_top2" in df.columns and total else 0.0
    avg_latency = float(df["elapsed_ms"].mean()) if "elapsed_ms" in df.columns and total else 0.0
    median_latency = float(df["elapsed_ms"].median()) if "elapsed_ms" in df.columns and total else 0.0
    p95_latency = float(df["elapsed_ms"].quantile(0.95)) if "elapsed_ms" in df.columns and total else 0.0
    provider_counts = Counter(df["provider"].fillna("unknown")) if "provider" in df.columns else Counter()
    fallback_rate = float(df["fallback_used"].mean()) if "fallback_used" in df.columns and total else 0.0

    return {
        "method_name": method_name,
        "total": total,
        "success_rate": success_rate,
        "top1_rate": top1_rate,
        "top2_rate": top2_rate,
        "avg_latency": avg_latency,
        "median_latency": median_latency,
        "p95_latency": p95_latency,
        "provider_counts": provider_counts,
        "fallback_rate": fallback_rate,
    }


def configure_fonts() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def make_metric_comparison_chart(primary: dict[str, object], similarity: dict[str, object]) -> Path:
    labels = ["RAG 視覺辨識", "特徵比對"]
    accuracy = [primary["top1_rate"] * 100, similarity["top1_rate"] * 100]
    success_rate = [primary["success_rate"] * 100, similarity["success_rate"] * 100]
    latency_sec = [primary["avg_latency"] / 1000.0, similarity["avg_latency"] / 1000.0]

    x = range(len(labels))
    width = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    ax = axes[0]
    ax.bar([i - width / 2 for i in x], accuracy, width=width, label="Top-1 準確率", color="#1f77b4")
    ax.bar([i + width / 2 for i in x], success_rate, width=width, label="成功率", color="#ff7f0e")
    ax.set_ylim(0, 110)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("百分比 (%)")
    ax.set_title("辨識成效比較")
    ax.legend(frameon=False)
    for idx, value in enumerate(accuracy):
        ax.text(idx - width / 2, value + 2, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)
    for idx, value in enumerate(success_rate):
        ax.text(idx + width / 2, value + 2, f"{value:.1f}%", ha="center", va="bottom", fontsize=9)

    ax = axes[1]
    ax.bar(labels, latency_sec, color="#2ca02c")
    ax.set_ylabel("平均延遲 (秒)")
    ax.set_title("平均回應時間")
    for idx, value in enumerate(latency_sec):
        ax.text(idx, value + 0.5, f"{value:.2f}s", ha="center", va="bottom", fontsize=9)

    fig.suptitle("藥物辨識測試結果比較", fontsize=14, fontweight="bold")
    output = FIG_DIR / "comparison_metrics.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def make_provider_chart(summary: dict[str, object]) -> Path:
    provider_counts: Counter = summary["provider_counts"]  # type: ignore[assignment]
    labels = list(provider_counts.keys()) or ["unknown"]
    values = [provider_counts.get(label, 0) for label in labels] or [0]

    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    colors = ["#4c78a8", "#f58518", "#54a24b", "#e45756"]
    bars = ax.bar(labels, values, color=colors[: len(labels)])
    ax.set_ylabel("樣本數")
    ax.set_title("辨識流程使用的 Provider 分布")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2, str(value), ha="center", va="bottom")

    output = FIG_DIR / "provider_distribution.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def make_latency_chart(primary: dict[str, object], similarity: dict[str, object]) -> Path:
    labels = ["RAG 視覺辨識", "特徵比對"]
    datasets = [
        [primary["median_latency"], primary["p95_latency"]],
        [similarity["median_latency"], similarity["p95_latency"]],
    ]

    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    x = range(len(labels))
    width = 0.34
    ax.bar([i - width / 2 for i in x], [v[0] / 1000.0 for v in datasets], width=width, label="中位數", color="#9c755f")
    ax.bar([i + width / 2 for i in x], [v[1] / 1000.0 for v in datasets], width=width, label="P95", color="#76b7b2")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("延遲 (秒)")
    ax.set_title("延遲分布摘要")
    ax.legend(frameon=False)
    for idx, vals in enumerate(datasets):
        ax.text(idx - width / 2, vals[0] / 1000.0 + 0.3, f"{vals[0] / 1000.0:.2f}s", ha="center", fontsize=9)
        ax.text(idx + width / 2, vals[1] / 1000.0 + 0.3, f"{vals[1] / 1000.0:.2f}s", ha="center", fontsize=9)

    output = FIG_DIR / "latency_summary.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output


def build_table_rows(summary: dict[str, object]) -> list[str]:
    return [
        escape_latex(summary["method_name"]),
        str(summary["total"]),
        f'{summary["success_rate"] * 100:.1f}\\%',
        f'{summary["top1_rate"] * 100:.1f}\\%',
        f'{summary["top2_rate"] * 100:.1f}\\%',
        f'{summary["avg_latency"] / 1000.0:.2f}',
        f'{summary["median_latency"] / 1000.0:.2f}',
        f'{summary["p95_latency"] / 1000.0:.2f}',
    ]


def thesis_relative_path(path: Path) -> str:
    return path.relative_to(THESIS_DIR).as_posix()


def render_tex(primary: dict[str, object], similarity: dict[str, object], fig_paths: list[Path]) -> None:
    primary_row = build_table_rows(primary)
    similarity_row = build_table_rows(similarity)
    metric_path = thesis_relative_path(fig_paths[0])
    provider_path = thesis_relative_path(fig_paths[1])
    latency_path = thesis_relative_path(fig_paths[2])

    tex = f"""% 由 scripts/export_thesis_experiments.py 自動產生
\\section{{實驗設計與結果}}

\\subsection{{測試設計}}
本研究以兩組測試資料驗證系統辨識能力。第一組為以 Gemini Vision 與藥物資料庫檢索整合的 RAG 辨識流程；第二組為以相似度特徵為核心的比對流程。每筆測試皆以單張圖片輸入，記錄辨識是否成功、Top-1 是否命中真值、真值是否落入 Top-2、平均延遲與回應來源，藉此比較不同方法在準確率與效能上的差異。

本研究採用下列指標：
\\begin{{align}}
\\text{{成功率}} &= \\frac{{\\text{{success}}}}{{N}} \\\\
\\text{{Top-1 準確率}} &= \\frac{{\\text{{top1\\_match}}}}{{N}} \\\\
\\text{{Top-2 命中率}} &= \\frac{{\\text{{truth\\_in\\_top2}}}}{{N}} \\\\
\\text{{平均延遲}} &= \\frac{{\\sum \\text{{elapsed\\_ms}}}}{{N}}
\\end{{align}}

\\subsection{{測試結果}}
\\begin{{table}}[htbp]
\\centering
\\caption{{藥物辨識測試結果摘要}}
\\label{{tab:drug-test-summary}}
\\begin{{tabular}}{{lrrrrrrr}}
\\hline
方法 & 樣本數 & 成功率 & Top-1 準確率 & Top-2 命中率 & 平均延遲 (s) & 中位數 (s) & P95 (s) \\\\
\\hline
{primary_row[0]} & {primary_row[1]} & {primary_row[2]} & {primary_row[3]} & {primary_row[4]} & {primary_row[5]} & {primary_row[6]} & {primary_row[7]} \\\\
{similarity_row[0]} & {similarity_row[1]} & {similarity_row[2]} & {similarity_row[3]} & {similarity_row[4]} & {similarity_row[5]} & {similarity_row[6]} & {similarity_row[7]} \\\\
\\hline
\\end{{tabular}}
\\end{{table}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.95\\linewidth]{{{metric_path}}}
\\caption{{藥物辨識成效與平均回應時間比較}}
\\label{{fig:drug-comparison-metrics}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.72\\linewidth]{{{provider_path}}}
\\caption{{RAG 辨識流程的 Provider 使用分布}}
\\label{{fig:provider-distribution}}
\\end{{figure}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.85\\linewidth]{{{latency_path}}}
\\caption{{辨識流程延遲摘要}}
\\label{{fig:latency-summary}}
\\end{{figure}}

由表 \\ref{{tab:drug-test-summary}} 可見，RAG 視覺辨識流程在 Top-1 準確率與成功率上具有明顯優勢，而特徵比對流程在延遲上相對接近但辨識品質較低。圖 \\ref{{fig:drug-comparison-metrics}} 至圖 \\ref{{fig:latency-summary}} 進一步顯示，系統在大多數測試中能維持穩定回應，但不同流程的品質與效能仍存在取捨。
"""

    OUT_TEX.write_text(tex, encoding="utf-8")


def main() -> None:
    THESIS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_fonts()

    if not PRIMARY_CSV.exists():
        raise FileNotFoundError(f"找不到測試結果檔: {PRIMARY_CSV}")
    if not SIMILARITY_CSV.exists():
        raise FileNotFoundError(f"找不到測試結果檔: {SIMILARITY_CSV}")

    primary_df = load_results(PRIMARY_CSV)
    similarity_df = load_results(SIMILARITY_CSV)

    primary_summary = summarize(primary_df, "RAG 視覺辨識")
    similarity_summary = summarize(similarity_df, "特徵比對")

    metric_chart = make_metric_comparison_chart(primary_summary, similarity_summary)
    provider_chart = make_provider_chart(primary_summary)
    latency_chart = make_latency_chart(primary_summary, similarity_summary)
    render_tex(primary_summary, similarity_summary, [metric_chart, provider_chart, latency_chart])

    print(f"已輸出 LaTeX：{OUT_TEX}")
    print(f"已輸出圖表：{metric_chart}")
    print(f"已輸出圖表：{provider_chart}")
    print(f"已輸出圖表：{latency_chart}")
    print("摘要：")
    for summary in [primary_summary, similarity_summary]:
        print(
            f"- {summary['method_name']}: 樣本 {summary['total']}，成功率 {summary['success_rate']*100:.1f}%"
            f"，Top-1 {summary['top1_rate']*100:.1f}%，平均延遲 {summary['avg_latency']/1000.0:.2f}s"
        )


if __name__ == "__main__":
    main()