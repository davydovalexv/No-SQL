import argparse
import random
import statistics
import threading
import time
from dataclasses import dataclass
from typing import List

import os

import matplotlib
import matplotlib.pyplot as plt

import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection


MONGO_URI_SHARDED = os.getenv("MONGO_URI_SHARDED", os.getenv("MONGO_URI", "mongodb://localhost:27018"))
MONGO_URI_SINGLE = os.getenv("MONGO_URI_SINGLE", "mongodb://localhost:27019")
DB_NAME = "university_grades"


@dataclass
class OpResult:
    latency_ms: float
    success: bool


def get_db(mongo_uri: str):
    client = MongoClient(mongo_uri)
    return client[DB_NAME]


def collect_student_ids(mongo_uri: str, limit: int = 1000) -> List[str]:
    db = get_db(mongo_uri)
    ids = [s["student_id"] for s in db.students.find({}, {"student_id": 1, "_id": 0}).limit(limit)]
    return ids


def worker_read_grades(
    collection: Collection,
    student_ids: List[str],
    n_ops: int,
    results: List[OpResult],
):
    for _ in range(n_ops):
        sid = random.choice(student_ids)
        start = time.perf_counter()
        try:
            list(collection.find({"student_id": sid}))
            latency_ms = (time.perf_counter() - start) * 1000.0
            results.append(OpResult(latency_ms=latency_ms, success=True))
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000.0
            results.append(OpResult(latency_ms=latency_ms, success=False))


def run_benchmark(mongo_uri: str, threads: int, ops_per_thread: int):
    db = get_db(mongo_uri)
    student_ids = collect_student_ids(mongo_uri)
    if not student_ids:
        raise RuntimeError("В коллекции students нет данных, сначала импортируйте JSON.")

    collection = db.grades
    all_results: List[OpResult] = []
    thread_list: List[threading.Thread] = []

    start = time.perf_counter()
    for _ in range(threads):
        t = threading.Thread(
            target=worker_read_grades,
            args=(collection, student_ids, ops_per_thread, all_results),
        )
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()
    total_time = time.perf_counter() - start

    print(f"\nВсего операций: {len(all_results)}")
    print(f"Потоков: {threads}")
    print(f"Общее время: {total_time:.3f} сек")
    print(f"Пропускная способность: {len(all_results) / total_time:.2f} ops/sec")

    latencies = [r.latency_ms for r in all_results if r.success]
    if latencies:
        print(f"Средняя задержка: {statistics.mean(latencies):.2f} мс")
        print(f"Медиана задержки: {statistics.median(latencies):.2f} мс")
        print(f"95-й перцентиль: {statistics.quantiles(latencies, n=100)[94]:.2f} мс")

    return all_results, total_time


def to_dataframe(results: List[OpResult], cluster_name: str) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "latency_ms": [r.latency_ms for r in results],
            "success": [r.success for r in results],
        }
    )
    df["op_index"] = range(len(df))
    df["cluster"] = cluster_name
    return df


def plot_comparison(df: pd.DataFrame, throughput_single: float, throughput_sharded: float) -> None:
    df_ok = df[df["success"]]
    if df_ok.empty:
        print("Нет успешных операций для построения графиков.")
        return

    out_dir = os.getcwd()
    path_latency = os.path.join(out_dir, "comparison_latency.png")
    path_throughput = os.path.join(out_dir, "comparison_throughput.png")

    # 1) Столбчатая диаграмма: средняя задержка single vs sharded
    mean_single = df_ok[df_ok["cluster"] == "single"]["latency_ms"].mean()
    mean_sharded = df_ok[df_ok["cluster"] == "sharded"]["latency_ms"].mean()
    clusters = ["single", "sharded"]
    means = [mean_single, mean_sharded]
    colors = ["gray", "steelblue"]
    plt.figure(figsize=(6, 4))
    plt.bar(clusters, means, color=colors)
    plt.ylabel("Средняя задержка, мс")
    plt.title("Сравнение задержки: одиночный инстанс vs шардированный кластер")
    for i, v in enumerate(means):
        plt.text(i, v, f"{v:.1f}", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(path_latency, dpi=120)

    # 2) Столбчатая диаграмма пропускной способности
    plt.figure(figsize=(6, 4))
    clusters = ["single", "sharded"]
    throughputs = [throughput_single, throughput_sharded]
    plt.bar(clusters, throughputs, color=["gray", "steelblue"])
    plt.ylabel("ops/sec")
    plt.title("Пропускная способность: одиночный инстанс vs шардированный кластер")
    for i, v in enumerate(throughputs):
        plt.text(i, v, f"{v:.0f}", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(path_throughput, dpi=120)

    try:
        plt.show()
    except Exception:
        plt.close("all")
    print("\nГрафики также сохранены в файлы:")
    print(f"  — {path_latency}")
    print(f"  — {path_throughput}")


def main():
    parser = argparse.ArgumentParser(
        description="Нагрузочное тестирование MongoDB (шардированная БД университета)."
    )
    parser.add_argument("--threads", type=int, default=8, help="Количество потоков")
    parser.add_argument("--ops-per-thread", type=int, default=1000, help="Операций на поток")

    args = parser.parse_args()

    print(f"Запуск бенчмарка для одиночного инстанса: threads={args.threads}, ops_per_thread={args.ops_per_thread}")
    results_single, total_single = run_benchmark(MONGO_URI_SINGLE, args.threads, args.ops_per_thread)
    df_single = to_dataframe(results_single, "single")
    throughput_single = len(results_single) / total_single

    print(f"\nЗапуск бенчмарка для шардированного кластера: threads={args.threads}, ops_per_thread={args.ops_per_thread}")
    results_sharded, total_sharded = run_benchmark(MONGO_URI_SHARDED, args.threads, args.ops_per_thread)
    df_sharded = to_dataframe(results_sharded, "sharded")
    throughput_sharded = len(results_sharded) / total_sharded

    df_all = pd.concat([df_single, df_sharded], ignore_index=True)

    print("\nПримеры строк DataFrame (single):")
    print(df_single.head())
    print("\nПримеры строк DataFrame (sharded):")
    print(df_sharded.head())

    print("\nСводка по пропускной способности:")
    print(f"  single:  {throughput_single:.2f} ops/sec")
    print(f"  sharded: {throughput_sharded:.2f} ops/sec")

    plot_comparison(df_all, throughput_single, throughput_sharded)
    plt.show()


if __name__ == "__main__":
    main()

