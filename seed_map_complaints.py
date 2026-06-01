"""Seed MAP_DEMO complaints into the database via the API."""
import urllib.request, urllib.error, json, sys

BASE = "http://127.0.0.1:8000/api"

MAP_DEMO = [
    {"cat": 1, "status": "in_progress", "title": "Нет горячей воды",
     "desc": "В доме уже несколько дней отсутствует горячее водоснабжение. Жители не могут нормально мыться и готовить.",
     "addr": "ул. Тверская, 18", "priority": "medium"},
    {"cat": 6, "status": "new", "title": "Яма на дороге",
     "desc": "На проезжей части образовалась крупная выбоина глубиной около 20 см. Опасна для транспорта и пешеходов.",
     "addr": "Кутузовский пр., 32", "priority": "high"},
    {"cat": 2, "status": "resolved", "title": "Не работает отопление",
     "desc": "В квартирах холодно, батареи не греют. Температура в помещениях опускается до 14 градусов.",
     "addr": "ул. Мира, 12", "priority": "high"},
    {"cat": 4, "status": "in_progress", "title": "Лифт не работает",
     "desc": "Лифт в подъезде не работает более трёх суток. Жителям верхних этажей приходится ходить пешком.",
     "addr": "б-р Ломоносова, 5", "priority": "medium"},
    {"cat": 5, "status": "new", "title": "Не вывезен мусор",
     "desc": "Мусорные баки переполнены, вывоз не производился уже несколько дней. Неприятный запах.",
     "addr": "ул. Садовая, 44", "priority": "medium"},
    {"cat": 3, "status": "resolved", "title": "Перебои с электричеством",
     "desc": "Периодически пропадает электричество в подъезде и квартирах. Особенно критично вечером.",
     "addr": "ул. Строителей, 7", "priority": "high"},
    {"cat": 8, "status": "in_progress", "title": "Течёт крыша",
     "desc": "Протечка кровли — намокают стены и потолок на верхних этажах. Портится отделка, появляется плесень.",
     "addr": "пр. Победы, 19", "priority": "high"},
    {"cat": 6, "status": "new", "title": "Разбитые бордюры",
     "desc": "Бордюры разрушены, тротуар в аварийном состоянии. Пожилые люди рискуют споткнуться и упасть.",
     "addr": "ул. Зелёная, 3", "priority": "low"},
    {"cat": 1, "status": "new", "title": "Прорыв трубы",
     "desc": "Прорвало водопроводную трубу в подвале, вода затопила часть подъезда. Нужен срочный ремонт.",
     "addr": "пер. Лесной, 8", "priority": "critical"},
    {"cat": 2, "status": "new", "title": "Холодные батареи",
     "desc": "Отопительный сезон уже начался, но батареи по-прежнему холодные. Жители мёрзнут.",
     "addr": "ул. Северная, 22", "priority": "high"},
    {"cat": 6, "status": "new", "title": "Выбоины на тротуаре",
     "desc": "Тротуар покрыт выбоинами и трещинами — опасно ходить, особенно в дождь.",
     "addr": "ул. Якиманка, 5", "priority": "low"},
    {"cat": 5, "status": "in_progress", "title": "Переполненные баки",
     "desc": "Мусорные контейнеры переполнены уже несколько дней. Отходы разлетаются по двору.",
     "addr": "ул. Бауманская, 10", "priority": "medium"},
]


def post(url, data, token=None):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{url}", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def patch(url, data, token):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(f"{BASE}{url}", data=body, headers=headers, method="PATCH")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    print("Logging in as admin...")
    resp = post("/auth/login", {"email": "admin@zhalobi.ru", "password": "admin123"})
    token = resp["access_token"]
    print(f"Token OK")

    ok = 0
    for c in MAP_DEMO:
        try:
            created = post("/complaints", {
                "category_id": c["cat"],
                "title": c["title"],
                "description": c["desc"],
                "address": c["addr"],
                "priority": c["priority"],
            }, token)
            cid = created["id"]
            # update status if not "new"
            if c["status"] != "new":
                patch(f"/admin/complaints/{cid}", {
                    "status": c["status"],
                    "comment": "Демонстрационные данные"
                }, token)
            print(f"  ✓ #{cid} {c['title']} [{c['status']}]")
            ok += 1
        except Exception as e:
            print(f"  ✗ {c['title']}: {e}")

    print(f"\nДобавлено {ok}/{len(MAP_DEMO)} жалоб.")


if __name__ == "__main__":
    main()
