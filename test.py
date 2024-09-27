import os


def merge_py_files(folder_path):
    # Путь к выходному файлу
    output_file = os.path.join(folder_path, "ALL_FILES.py")

    # Открываем выходной файл для записи
    with open(output_file, "w") as all_files:
        # Проходим по всем файлам в папке
        for file_name in os.listdir(folder_path):
            # Проверяем, что файл имеет расширение .py
            if file_name.endswith(".py") and file_name != "ALL_FILES.py":
                file_path = os.path.join(folder_path, file_name)

                # Читаем содержимое каждого .py файла
                with open(file_path, "r") as py_file:
                    file_content = py_file.read()

                    # Пишем комментарий с именем файла и его содержимое в выходной файл
                    all_files.write(f"# {file_name}\n")
                    all_files.write(file_content)
                    all_files.write("\n\n")  # Добавляем пустую строку между файлами

    print(f"Файл ALL_FILES.py успешно создан в папке {folder_path}")


# Пример использования
merge_py_files(r"C:\Users\user\Downloads\py_scripts")
