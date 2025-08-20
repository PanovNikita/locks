import streamlit as st
import pandas as pd
import os
from datetime import datetime
from collections import Counter
import re

# Конфигурация страницы
st.set_page_config(page_title="Locks Analyser", page_icon="🔒", layout="wide")


def load_data():
    """Загрузка данных из CSV файла"""
    if not os.path.exists("data.csv"):
        return None, "Файл data.csv не найден!"

    try:
        df = pd.read_csv("data.csv", header=None, dtype=str)
        return df, None
    except Exception as e:
        return None, f"Ошибка при чтении файла data.csv: {str(e)}"


def get_file_info():
    """Получение информации о файле"""
    if os.path.exists("data.csv"):
        stat = os.stat("data.csv")
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        return mod_time
    return "Файл не найден"


def normalize_row_number(row_num):
    """Нормализация номера строки к 6-значному формату"""
    try:
        num = int(row_num)
        return f"{num:06d}"
    except:
        return None


def validate_data(df):
    """Валидация данных CSV файла"""
    errors = []

    # Проверка структуры
    if df.shape[1] < 7:
        errors.append(
            "Недостаточно колонок в файле. Ожидается минимум 7 колонок (номер строки + 6 значений)"
        )
        return errors

    # Проверка дубликатов номеров строк
    row_numbers = df[0].tolist()
    duplicates = [item for item, count in Counter(row_numbers).items() if count > 1]
    if duplicates:
        errors.append(f"Найдены дублирующиеся номера строк: {', '.join(duplicates)}")

    # Проверка двузначных значений
    for idx, row in df.iterrows():
        row_num = row[0]
        for col_idx in range(1, 7):  # Проверяем колонки 1-6
            if col_idx < len(row):
                value = str(row[col_idx]).strip()
                if value and value != "nan":  # Пропускаем пустые значения
                    try:
                        num_val = int(value)
                        if num_val < 10 or num_val > 99:
                            errors.append(
                                f"Строка {row_num}, позиция {col_idx}: значение '{value}' не является двузначным числом"
                            )
                    except ValueError:
                        errors.append(
                            f"Строка {row_num}, позиция {col_idx}: значение '{value}' не является числом"
                        )
            else:
                errors.append(
                    f"Строка {row_num}: отсутствует значение в позиции {col_idx}"
                )

    return errors


def check_range_integrity(df, start_num, end_num):
    """Проверка целостности диапазона"""
    missing_rows = []
    existing_rows = set(df[0].astype(str).tolist())

    for i in range(int(start_num), int(end_num) + 1):
        row_num = f"{i:06d}"
        if row_num not in existing_rows:
            missing_rows.append(row_num)

    return missing_rows


def get_single_row(df, row_number):
    """Получение одной строки по номеру"""
    normalized_num = normalize_row_number(row_number)
    if not normalized_num:
        return None, "Некорректный номер строки"

    row_data = df[df[0] == normalized_num]
    if row_data.empty:
        return None, f"Строка {normalized_num} не найдена"

    return row_data.iloc[0], None


def calculate_digit_difference(num):
    """Вычисление разности цифр двузначного числа"""
    if pd.isna(num) or str(num).strip() == "":
        return None
    try:
        num_str = str(int(num))
        if len(num_str) == 2:
            return abs(int(num_str[0]) - int(num_str[1]))
        else:
            return None
    except:
        return None


def is_mirror_number(num):
    """Проверка, является ли число зеркальным"""
    if pd.isna(num) or str(num).strip() == "":
        return False
    try:
        num_str = str(int(num))
        if len(num_str) == 2:
            return num_str[0] == num_str[1]
        return False
    except:
        return False


def analyze_range(df, start_range, end_range, is_skat=False):
    """Анализ диапазона строк"""
    start_num = normalize_row_number(start_range)
    end_num = normalize_row_number(end_range)

    if not start_num or not end_num:
        return None, "Некорректный формат диапазона"

    if int(start_num) > int(end_num):
        return None, "Начало диапазона не может быть больше конца"

    # Проверка целостности диапазона
    missing_rows = check_range_integrity(df, start_num, end_num)
    if missing_rows:
        return None, f"В диапазоне отсутствуют строки: {', '.join(missing_rows)}"

    # Фильтрация данных по диапазону
    df_filtered = df[
        (df[0].astype(str) >= start_num) & (df[0].astype(str) <= end_num)
    ].copy()

    if df_filtered.empty:
        return None, "Нет данных в указанном диапазоне"

    # Определяем количество колонок для анализа
    cols_to_analyze = 5 if is_skat else 6

    results = {
        "total_count": 0,
        "doubled_count": 0,
        "quadrupled_count": 0,
        "difference_groups": {},
        "mirror_numbers": [],
        "special_numbers": [],  # Для режима СКАТ
    }

    special_numbers = [11, 22, 33, 44, 55, 66, 77]

    for _, row in df_filtered.iterrows():
        for col_idx in range(1, cols_to_analyze + 1):
            if col_idx < len(row):
                try:
                    value = int(row[col_idx])
                    if 10 <= value <= 99:  # Двузначное число
                        results["total_count"] += 1

                        # Проверка на специальные числа в режиме СКАТ
                        if is_skat and value in special_numbers:
                            results["quadrupled_count"] += 4
                            results["special_numbers"].append(value)
                        else:
                            results["doubled_count"] += 2

                        # Группировка по разности цифр
                        diff = calculate_digit_difference(value)
                        if diff is not None:
                            if diff not in results["difference_groups"]:
                                results["difference_groups"][diff] = []
                            results["difference_groups"][diff].append(value)

                        # Поиск зеркальных чисел
                        if is_mirror_number(value):
                            results["mirror_numbers"].append(value)
                except:
                    continue

    return results, None


def format_results_for_copy(results, is_skat=False):
    """Форматирование результатов для копирования"""
    text = []
    text.append("=== РЕЗУЛЬТАТЫ АНАЛИЗА ===")
    text.append("")

    mode = "СКАТ" if is_skat else "Обычный"
    text.append(f"Режим: {mode}")
    text.append("")

    text.append(f"Общее количество чисел: {results['total_count']}")

    if is_skat and results["quadrupled_count"] > 0:
        text.append(f"Удвоенное количество: {results['doubled_count']}")
        text.append(f"Учетверенное количество: {results['quadrupled_count']}")
        text.append(f"Итого: {results['doubled_count'] + results['quadrupled_count']}")
        if results["special_numbers"]:
            special_count = Counter(results["special_numbers"])
            text.append(f"Специальные числа (x4): {dict(special_count)}")
    else:
        text.append(f"Удвоенное количество: {results['doubled_count']}")

    text.append("")
    text.append("ГРУППИРОВКА ПО РАЗНОСТИ ЦИФР:")
    for diff in sorted(results["difference_groups"].keys()):
        numbers = results["difference_groups"][diff]
        count = Counter(numbers)
        text.append(f"Разность {diff}: {dict(count)}")

    if results["mirror_numbers"]:
        text.append("")
        text.append("ЗЕРКАЛЬНЫЕ ЧИСЛА:")
        mirror_count = Counter(results["mirror_numbers"])
        text.append(f"{dict(mirror_count)}")

    return "\n".join(text)


def main():
    st.title("🔒 Locks Analyser")
    st.markdown("---")

    # Информация о файле
    file_mod_time = get_file_info()
    df, load_error = load_data()

    if load_error:
        st.error(load_error)
        st.stop()

    row_count = len(df)
    st.info(f"📄 Файл: data.csv | Обновлен: {file_mod_time} | Строк: {row_count}")

    # Валидация данных
    validation_errors = validate_data(df)
    if validation_errors:
        st.error("❌ Обнаружены ошибки в данных:")
        for error in validation_errors:
            st.write(f"• {error}")
        st.stop()
    else:
        st.success("✅ Данные прошли валидацию")

    # Основной интерфейс
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Анализ диапазона")

        col1_1, col1_2 = st.columns(2)
        with col1_1:
            start_range = st.text_input("От:", placeholder="001000 или 1000")
        with col1_2:
            end_range = st.text_input("До:", placeholder="001020 или 1020")

        is_skat = st.checkbox(
            "Это СКАТ?",
            help="В режиме СКАТ анализируются только первые 5 колонок, специальные числа умножаются на 4",
        )

        if st.button("🔍 Анализировать диапазон", type="primary"):
            if start_range and end_range:
                with st.spinner("Анализ данных..."):
                    results, error = analyze_range(df, start_range, end_range, is_skat)

                if error:
                    st.error(f"❌ {error}")
                else:
                    st.success("✅ Анализ завершен")

                    # Отображение результатов
                    st.subheader("📈 Результаты")

                    col_res1, col_res2, col_res3 = st.columns(3)

                    with col_res1:
                        st.metric("Общее количество", results["total_count"])

                    with col_res2:
                        if is_skat and results["quadrupled_count"] > 0:
                            total = (
                                results["doubled_count"] + results["quadrupled_count"]
                            )
                            st.metric("Итого (x2 + x4)", total)
                        else:
                            st.metric("Удвоенное количество", results["doubled_count"])

                    with col_res3:
                        if is_skat and results["quadrupled_count"] > 0:
                            st.metric("Учетверенное", results["quadrupled_count"])

                    # Группировка по разности цифр
                    if results["difference_groups"]:
                        st.subheader("📋 Группировка по разности цифр")
                        for diff in sorted(results["difference_groups"].keys()):
                            numbers = results["difference_groups"][diff]
                            count = Counter(numbers)
                            st.write(f"**Разность {diff}:** {dict(count)}")

                    # Зеркальные числа
                    if results["mirror_numbers"]:
                        st.subheader("🪞 Зеркальные числа")
                        mirror_count = Counter(results["mirror_numbers"])
                        st.write(dict(mirror_count))

                    # Специальные числа для режима СКАТ
                    if is_skat and results["special_numbers"]:
                        st.subheader("⭐ Специальные числа (x4)")
                        special_count = Counter(results["special_numbers"])
                        st.write(dict(special_count))

                    # Кнопка копирования
                    formatted_text = format_results_for_copy(results, is_skat)

                    # JavaScript для копирования в буфер обмена
                    copy_script = f"""
                    <script>
                    function copyToClipboard() {{
                        const text = `{formatted_text.replace('`', '\\`')}`;
                        if (navigator.clipboard && navigator.clipboard.writeText) {{
                            navigator.clipboard.writeText(text).then(function() {{
                                alert('Результаты скопированы в буфер обмена!');
                            }}).catch(function() {{
                                fallbackCopy(text);
                            }});
                        }} else {{
                            fallbackCopy(text);
                        }}
                    }}
                    
                    function fallbackCopy(text) {{
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            alert('Результаты скопированы в буфер обмена!');
                        }} catch (err) {{
                            prompt('Скопируйте текст:', text);
                        }}
                        document.body.removeChild(textArea);
                    }}
                    </script>
                    
                    <button onclick="copyToClipboard()" style="
                        background-color: #ff4b4b;
                        color: white;
                        border: none;
                        padding: 0.5rem 1rem;
                        border-radius: 0.25rem;
                        cursor: pointer;
                        font-size: 14px;
                        margin-top: 10px;
                    ">📋 Копировать результаты</button>
                    """

                    st.components.v1.html(copy_script, height=100)

                    # Fallback - текстовое поле для ручного копирования
                    with st.expander(
                        "📝 Текст для копирования (если кнопка не работает)"
                    ):
                        st.text_area("Результаты:", formatted_text, height=200)
            else:
                st.warning("⚠️ Укажите диапазон для анализа")

    with col2:
        st.subheader("🔍 Просмотр строки")

        row_number = st.text_input("Номер строки:", placeholder="001010 или 1010")

        if st.button("👁️ Показать строку"):
            if row_number:
                row_data, error = get_single_row(df, row_number)
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.success(f"✅ Строка найдена: {row_data[0]}")

                    # Создаем таблицу для отображения
                    display_data = []
                    for i in range(1, min(7, len(row_data))):
                        display_data.append([f"Позиция {i}", row_data[i]])

                    df_display = pd.DataFrame(
                        display_data, columns=["Позиция", "Значение"]
                    )
                    st.table(df_display)
            else:
                st.warning("⚠️ Укажите номер строки")

    # Справка
    st.markdown("---")
    with st.expander("ℹ️ Справка"):
        st.markdown(
            """
        **Как использовать:**
        
        1. **Анализ диапазона**: Введите начальную и конечную строки диапазона
        2. **Режим СКАТ**: Анализирует только первые 5 колонок, числа 11,22,33,44,55,66,77 умножаются на 4
        3. **Просмотр строки**: Посмотреть содержимое конкретной строки
        
        **Форматы ввода номеров строк:**
        - 001234 (с ведущими нулями)  
        - 1234 (без ведущих нулей)
        
        **Проверки данных:**
        - ✅ Целостность диапазона
        - ✅ Валидация двузначных чисел (10-99)
        - ✅ Проверка дубликатов строк
        """
        )


if __name__ == "__main__":
    main()
