"""ПР1. Создаёт тестовые «данные компании» для резервного копирования."""
import random
from pathlib import Path

root = Path("company_data")
# Вариант 2: отделы it, buh, legal и по 6 файлов на отдел
for dept in ["it", "buh", "legal"]:
    (root / dept).mkdir(parents=True, exist_ok=True)
    for i in range(1, 7):
        lines = [f"{dept};doc{i};{random.randint(1000, 99999)}" for _ in range(200)]
        (root / dept / f"report_{i}.csv").write_text("\n".join(lines), encoding="utf-8")
print("Тестовые данные созданы в папке company_data/")