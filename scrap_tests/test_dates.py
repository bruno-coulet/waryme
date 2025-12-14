from datetime import date, timedelta

today = date(2025, 12, 8)  # Lundi 08/12/2025
print(f'Aujourd hui : {today.strftime("%A %d/%m/%Y")} (weekday={today.weekday()})')

days_since_monday = today.weekday()
start_date = today - timedelta(days=days_since_monday + 7)
end_date = start_date + timedelta(days=6)

print(f'Plage : {start_date.strftime("%A %d/%m/%Y")} au {end_date.strftime("%A %d/%m/%Y")}')
print(f'Attendu : lundi 01/12/2025 au dimanche 07/12/2025')
