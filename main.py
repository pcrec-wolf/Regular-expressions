import csv
import re
from collections import defaultdict


def process_phone(phone):
    """Приводит телефон к стандартному формату"""
    if not phone:
        return ""

    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', phone)

    # Если номер начинается с 8, заменяем на +7
    if digits.startswith('8'):
        digits = '7' + digits[1:]

    # Проверяем, что номер имеет правильную длину
    if len(digits) == 11 and digits.startswith('7'):
        main_number = digits[1:]  # Убираем код страны

        # Форматируем основной номер
        formatted = f"+7({main_number[:3]}){main_number[3:6]}-{main_number[6:8]}-{main_number[8:]}"

        return formatted
    else:
        # Если номер некорректный, возвращаем исходный
        return phone


def process_phone_with_extension(phone):
    """Обрабатывает телефон с возможным добавочным номером"""
    if not phone:
        return ""

    # Разделяем основной номер и добавочный
    if 'доб' in phone.lower():
        parts = re.split(r'доб\.?\s*', phone, flags=re.IGNORECASE)
        main_phone = process_phone(parts[0])
        extension = re.sub(r'\D', '', parts[1]) if len(parts) > 1 else ''
        return f"{main_phone} доб.{extension}" if extension else main_phone
    else:
        return process_phone(phone)


def parse_fio(fio_string):
    """Разбирает ФИО на компоненты"""
    parts = fio_string.strip().split(' ')

    # Убираем пустые строки
    parts = [part for part in parts if part]

    # Базовые случаи
    if len(parts) >= 3:
        # Уже есть Ф+И+О
        lastname, firstname, surname = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        # Ф+ИО или Ф+И
        lastname, firstname = parts[0], parts[1]
        surname = ""  # Отчество отсутствует
    else:
        # Только фамилия
        lastname = parts[0] if parts else ""
        firstname = ""
        surname = ""

    return lastname, firstname, surname


def merge_contacts(contacts_list):
    """Объединяет дублирующиеся записи по Фамилии и Имени"""
    merged = defaultdict(lambda: {
        'lastname': '',
        'firstname': '',
        'surname': '',
        'organization': '',
        'position': '',
        'phone': '',
        'email': ''
    })

    for contact in contacts_list:
        # Ключ для группировки - только Фамилия и Имя
        key = (contact['lastname'], contact['firstname'])

        # Для каждого поля берем первое непустое значение
        for field in ['lastname', 'firstname', 'surname', 'organization', 'position']:
            if contact[field] and not merged[key][field]:
                merged[key][field] = contact[field]

        # Телефон и email - берем первый попавшийся (у человека может быть только один)
        if contact['phone'] and not merged[key]['phone']:
            merged[key]['phone'] = contact['phone']
        if contact['email'] and not merged[key]['email']:
            merged[key]['email'] = contact['email']

    return list(merged.values())


def read_phonebook(filename):
    """Читает CSV файл с телефонной книгой"""
    contacts = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append({
                'lastname': row.get('lastname', ''),
                'firstname': row.get('firstname', ''),
                'surname': row.get('surname', ''),
                'organization': row.get('organization', ''),
                'position': row.get('position', ''),
                'phone': row.get('phone', ''),
                'email': row.get('email', '')
            })
    return contacts


def write_phonebook(filename, contacts):
    """Записывает обработанную телефонную книгу в CSV"""
    fieldnames = ['lastname', 'firstname', 'surname', 'organization', 'position', 'phone', 'email']

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for contact in contacts:
            writer.writerow(contact)


def process_address_book(input_file, output_file):
    """Основная функция обработки записной книжки"""

    # Читаем исходные данные
    raw_contacts = read_phonebook(input_file)
    processed_contacts = []

    print(f"Прочитано контактов из файла: {len(raw_contacts)}")

    for contact in raw_contacts:
        # Обрабатываем ФИО - объединяем все части и разбираем заново
        fio_parts = []
        if contact['lastname']:
            fio_parts.append(contact['lastname'])
        if contact['firstname']:
            fio_parts.append(contact['firstname'])
        if contact['surname']:
            fio_parts.append(contact['surname'])

        fio_string = ' '.join(fio_parts)
        lastname, firstname, surname = parse_fio(fio_string)

        # Обрабатываем телефон
        phone = process_phone_with_extension(contact.get('phone', ''))

        # Создаем обработанный контакт
        processed_contact = {
            'lastname': lastname,
            'firstname': firstname,
            'surname': surname,
            'organization': contact.get('organization', ''),
            'position': contact.get('position', ''),
            'phone': phone,
            'email': contact.get('email', '')
        }

        processed_contacts.append(processed_contact)

    print(f"После обработки ФИО и телефонов: {len(processed_contacts)} контактов")

    # Объединяем дублирующиеся записи
    final_contacts = merge_contacts(processed_contacts)

    print(f"После объединения дублей: {len(final_contacts)} контактов")

    # Записываем результат
    write_phonebook(output_file, final_contacts)
    print(f"Результат записан в файл: {output_file}")

    return final_contacts


if __name__ == "__main__":
    input_filename = "phonebook_raw.csv"
    output_filename = "phonebook.csv"

    try:
        result = process_address_book(input_filename, output_filename)

    except FileNotFoundError:
        print(f"Ошибка: Файл {input_filename} не найден!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")