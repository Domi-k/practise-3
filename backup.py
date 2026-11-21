"""ПР1. Резервное копирование с ротацией, проверкой целостности и восстановлением."""
import hashlib
import json
import shutil
import tarfile
import time
from datetime import datetime
from pathlib import Path

SOURCE = Path("company_data")      # что копируем
BACKUP_DIR = Path("backups")       # куда складываем архивы
KEEP_LAST = 7                      # сколько последних копий хранить (по варианту 2)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_manifest(folder):
    """Контрольная сумма каждого файла: {относительный_путь: sha256}."""
    return {str(p.relative_to(folder)): sha256(p)
            for p in sorted(folder.rglob("*")) if p.is_file()}


def create_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = BACKUP_DIR / f"backup_{stamp}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(SOURCE, arcname=SOURCE.name)
    manifest = {
        "created": stamp,
        "archive_sha256": sha256(archive),
        "files": make_manifest(SOURCE)
    }
    archive.with_suffix("").with_suffix(".json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] Создан {archive.name}, файлов: {len(manifest['files'])}, "
          f"размер: {archive.stat().st_size / 1024:.1f} КБ")
    return archive


def rotate():
    archives = sorted(BACKUP_DIR.glob("backup_*.tar.gz"))
    for old in archives[:-KEEP_LAST]:
        old.unlink()
        old.with_suffix("").with_suffix(".json").unlink(missing_ok=True)
        print(f"[ROTATE] Удалена старая копия {old.name}")


def verify_restore(archive):
    """Восстанавливает архив во временную папку и сравнивает контрольные суммы."""
    json_path = archive.with_suffix("").with_suffix(".json")
    if not json_path.exists():
        print(f"[FAIL] Манифест для {archive.name} не найден")
        return False

    manifest = json.loads(json_path.read_text(encoding="utf-8"))
    if sha256(archive) != manifest["archive_sha256"]:
        print("[FAIL] Архив повреждён: контрольная сумма не совпадает")
        return False

    tmp = Path("restore_test")
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        with tarfile.open(archive) as tar:
            tar.extractall(tmp)
    except Exception as e:
        print(f"[FAIL] Ошибка при распаковке архива: {e}")
        shutil.rmtree(tmp, ignore_errors=True)
        return False

    restored = make_manifest(tmp / SOURCE.name)
    shutil.rmtree(tmp)

    original_files = manifest["files"]

    if restored == original_files:
        print(f"[OK] Восстановление проверено: {len(restored)} файлов совпадают")
        return True

    # Задание 3: Подробный отчёт о различиях
    print("[FAIL] Восстановленные данные не совпадают с оригиналом:")
    restored_keys = set(restored.keys())
    orig_keys = set(original_files.keys())

    missing = orig_keys - restored_keys
    extra = restored_keys - orig_keys
    common = orig_keys & restored_keys

    changed = [k for k in common if restored[k] != original_files[k]]

    if missing:
        print(f"  - Отсутствуют файлы: {sorted(missing)}")
    if extra:
        print(f"  - Лишние файлы: {sorted(extra)}")
    if changed:
        print(f"  - Изменены файлы (не совпадает хэш): {sorted(changed)}")

    return False


def restore(archive):
    """Задание 4: Восстановление после инцидента с замером времени RTO."""
    start_time = time.perf_counter()

    print(f"[INFO] Начало восстановления из архива {archive.name}...")

    if SOURCE.exists():
        shutil.rmtree(SOURCE)
        print(f"[INFO] Поврежденная папка {SOURCE} удалена.")

    with tarfile.open(archive) as tar:
        tar.extractall()

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"[OK] Данные успешно восстановлены из архива в папку {SOURCE}")
    print(f"[TIME] Время восстановления (RTO замер): {elapsed:.4f} секунд")


if __name__ == "__main__":
    # Шаг 1: Создаем бэкап, ротируем старые и проверяем
    archive = create_backup()
    rotate()
    verify_restore(archive)

    # Шаг 2 (Демо Задания 4): Имитация инцидента (удаление папки buh)
    buh_folder = SOURCE / "buh"
    if buh_folder.exists():
        shutil.rmtree(buh_folder)
        print(f"\n[INCIDENT] Папка {buh_folder} случайно удалена сотрудником!")

    # Восстановление из последней копии
    restore(archive)