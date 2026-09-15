import csv
import io

from bot.models.user import User


def stats_to_csv(general: dict, referral: dict, funnel: dict, top: list[tuple[User, int]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Umumiy statistika"])
    labels = {
        "total_users": "Jami /start bosganlar",
        "today_users": "Bugun qo'shilganlar",
        "last_7d_users": "Oxirgi 7 kunda",
        "last_30d_users": "Oxirgi 30 kunda",
        "subscribed": "Barcha kanallarga obuna bo'lganlar",
        "generated_link": "Referral havola yaratganlar",
        "at_least_one_referral": "Kamida bitta taklif qilganlar",
        "completed_all_requirements": "Barcha shartlarni bajarganlar",
        "secret_link_taken": "Maxfiy havola olganlar",
        "joined_private": "Yopiq kanalga qo'shilganlar",
        "blocked": "Botni bloklaganlar",
    }
    for key, label in labels.items():
        writer.writerow([label, general.get(key, 0)])

    writer.writerow([])
    writer.writerow(["Referral statistikasi"])
    writer.writerow(["Jami referral", referral["total"]])
    writer.writerow(["Tasdiqlangan", referral["approved"]])
    writer.writerow(["Shartlarni bajarmagan", referral["pending"]])
    writer.writerow(["Konversiya (%)", referral["conversion_pct"]])

    writer.writerow([])
    writer.writerow(["Konversiya voronkasi (%)"])
    funnel_labels = {
        "start_to_subscribed": "/start -> obunani tasdiqlash",
        "subscribed_to_link": "obuna -> referral havola olish",
        "link_to_completed": "havola -> shartlarni bajarish",
        "completed_to_secret": "shartlar -> maxfiy havola olish",
        "secret_to_joined": "maxfiy havola -> kanalga qo'shilish",
    }
    for key, label in funnel_labels.items():
        writer.writerow([label, funnel.get(key, 0)])

    writer.writerow([])
    writer.writerow(["Top referrerlar"])
    writer.writerow(["Telegram ID", "Ism", "Username", "Tasdiqlangan takliflar"])
    for user, cnt in top:
        writer.writerow([user.tg_id, user.first_name, user.username or "-", cnt])

    return buf.getvalue()
