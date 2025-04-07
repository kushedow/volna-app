from datetime import datetime


def format_datetime_ru(value: datetime):
    month_names_ru = {
        1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля", 5: "Мая", 6: "Июня",
        7: "Июля", 8: "Августа", 9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
    }
    """Formats datetime object to Russian format: Day Month Year Hour:Minute without leading zeros."""
    day = str(value.day).lstrip("0")  # Remove leading zero from day
    month = month_names_ru[value.month]
    year = value.year
    hour = value.hour
    minute = value.minute
    return f"{day} {month} {year} {hour:02}:{minute:02}" #Ensure to add time
