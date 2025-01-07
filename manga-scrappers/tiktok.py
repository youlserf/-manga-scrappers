import os
import re
import time
from datetime import datetime, timedelta
from enum import Enum

import pyautogui
import pyperclip
from playwright.sync_api import sync_playwright

SLEEP_DURATION = 2  # Pausa predeterminada en segundos

CLICK_COORDINATES = {
    "upload": (625, 80),  # Coordenadas para el botón de 'Seleccionar video'
    "search": (276, 234), # Coordenadas para el botón de búsqueda
    # Agregar otras coordenadas necesarias aquí
}

def right_click_at(coords):
    """Right-click at specified coordinates."""
    pyautogui.click(coords, button='right')
    wait()
    
def wait(seconds=SLEEP_DURATION):
    """Pausa la ejecución por un tiempo dado."""
    time.sleep(seconds)

def click_at(coords):
    """Realiza clic en las coordenadas especificadas."""
    pyautogui.click(coords)
    print(f"Clic en {coords}")
    wait()

def copy_text(text):
    """Copia el texto proporcionado al portapapeles."""
    pyperclip.copy(text)
    print(f"Texto copiado: {text[:30]}...")  # Mostrar una vista previa del texto

def paste_clipboard():
    """Pega el contenido del portapapeles."""
    pyautogui.hotkey('ctrl', 'v')
    print("Pega el contenido del portapapeles")
    wait()

def press_enter():
    """Simula presionar la tecla Enter."""
    pyautogui.press('enter')
    print("Presiona Enter")
    wait()

def normalize_path(path):
    """Convert a Windows-style path to Unix-style."""
    return path.replace("\\", "/")
def upload_file(chapter_path):
    """Function to interact with the file upload dialog and upload the file."""
    wait(2)
    right_click_at(CLICK_COORDINATES["upload"])
    pyautogui.moveTo(635, 160)
    pyautogui.press('enter')
    click_at(CLICK_COORDINATES["upload"])
    copy_text(chapter_path)
    paste_clipboard()
    press_enter()
    click_at(CLICK_COORDINATES["search"])
    pyautogui.press('enter')


class Month(Enum):
    Enero = 1
    Febrero = 2
    Marzo = 3
    Abril = 4
    Mayo = 5
    Junio = 6
    Julio = 7
    Agosto = 8
    Septiembre = 9
    Octubre = 10
    Noviembre = 11
    Diciembre = 12

def set_datetime_fields(page, date, time):
    target_date = date.split("-")
    target_year = int(target_date[0])
    target_month = int(target_date[1])
    target_day = int(target_date[2])
    target_hour, target_minute = map(int, time.split(":"))


    date_picker_selector = 'input.TUXTextInputCore-input[type="text"][value*="-"]'

    time_picker_selector = 'input.TUXTextInputCore-input[type="text"][value*=":"]'
    
    page.locator(time_picker_selector).click()

    # Scroll to the hour element
    hour_selector = f'.tiktok-timepicker-option-list .tiktok-timepicker-option-item .tiktok-timepicker-left:has-text("{target_hour:02}")'
    hour_element = page.locator(hour_selector)
    hour_element.scroll_into_view_if_needed()  # Scrolls the element into view if not already visible
    wait()
    hour_element.click()

    # Scroll to the minute element
    minute_selector = f'.tiktok-timepicker-option-list .tiktok-timepicker-option-item .tiktok-timepicker-right:has-text("{target_minute:02}")'
    minute_element = page.locator(minute_selector)
    minute_element.scroll_into_view_if_needed() 
    wait()
    minute_element.click()

    
    page.locator(date_picker_selector).click()

    while True:
        current_month_text = page.text_content('.scheduled-picker .month-title')
        current_year_text = page.text_content('.scheduled-picker .year-title')
        current_month = [k for k, v in Month.__members__.items() if v.value == target_month][0]
        current_year = int(current_year_text)

        if current_month == current_month_text and current_year == target_year:
            break

        arrows = page.query_selector_all('.scheduled-picker .arrow')

        if len(arrows) > 1:
            arrows[1].click()

    # Get all enabled days
    enabled_days = page.query_selector_all('.scheduled-picker .day.valid')

    # Extract the day numbers from the enabled days
    enabled_day_numbers = [int(day.text_content()) for day in enabled_days]

    # Check if the target day is in the enabled days
    if target_day in enabled_day_numbers:
        # Select the target day if it's valid
        day_selector = f'.scheduled-picker .day:has-text("{target_day}")'
    else:
        # Find the closest valid day
        closest_day = min(enabled_day_numbers, key=lambda x: abs(x - target_day))
        day_selector = f'.scheduled-picker .day:has-text("{closest_day}")'

    # Click the selected day
    page.click(day_selector)
    
    page.locator(date_picker_selector).click()
    
    
    wait()
    # Close the picker
    page.click('.scheduled-picker')  # Assuming clicking outside closes the picker

def replicate_actions(page, chapter_path, hashtags, target_date, target_time):
    """Realiza las acciones necesarias para procesar un capítulo."""
    # Subir el archivo usando Playwright
    page.wait_for_selector('.TUXButton-label')
    page.click('div.TUXButton-label:has-text("Seleccionar vídeo")')
    upload_file(chapter_path)  # Función para interactuar con la ventana emergente

    time.sleep(2)
     
    # Insertar los hashtags en el cuadro correspondiente
    hashtag_container_selector = 'div.public-DraftEditor-content[contenteditable="true"]'
    page.wait_for_selector(hashtag_container_selector)  # Esperar a que el contenedor esté disponible
    
    # Activar el contenedor escribiendo un texto inicial
    page.type(hashtag_container_selector, " ")
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    copy_text("Title")
    paste_clipboard()
    pyautogui.press("enter")
    
    # Pegamos hashtags uno a uno
    for hashtag in hashtags:
        copy_text(hashtag)  # Copiar un hashtag
        paste_clipboard()  
        wait(1)  # Pequeña pausa entre hashtags
        pyautogui.press("enter") 
        pyautogui.press("enter")

    # Hacer click en el radio button de "Programación"
    page.click('input[type="radio"][name="postSchedule"][value="schedule"]')
    
     # Establecer valores de fecha y hora
    try:
        print(target_date, target_time)

        set_datetime_fields(page, target_date, target_time)
    except Exception as e:
        print(f"Error processing chapter {chapter_path} on date {target_date} at {target_time}: {str(e)}")
        print("Breaking the process.")
        return  # Optionally, return the error

    pyautogui.press("enter")
    first_button = page.locator('button:has-text("Cargar")')
    wait(10)
    # Hacer click en el botón de "Programación" para publicar el video
    second_button = page.locator('button:has-text("Programación")')  # Searches for a button with text "Programación"
    second_button.scroll_into_view_if_needed() 
    second_button.click()
    
    wait()
    # Hacer clic en el botón "Cargar"
    first_button.scroll_into_view_if_needed() 
    first_button.click()

def process_chapters(manga_path, hashtags):
    """Procesa cada capítulo en el directorio proporcionado."""
    chapter_folders = sorted(
        (folder for folder in os.listdir(manga_path) if os.path.isdir(os.path.join(manga_path, folder))),
        key=lambda folder: int(re.search(r'(\d+)', folder).group(1))
    )

    try:
        start_chapter = int(input("Introduce el número del capítulo inicial: "))
        start_time = input("Introduce la hora de inicio (formato HH:MM): ")
        start_date = input("Introduce la fecha de inicio (formato YYYY-MM-DD): ")
    except ValueError:
        print("Entrada no válida. Introduce un número válido.")
        return

    start_index = next((idx for idx, folder in enumerate(chapter_folders)
                        if int(re.search(r'(\d+)', folder).group(1)) == start_chapter), None)
    if start_index is None:
        print(f"Capítulo {start_chapter} no encontrado.")
        return

     # Convert start_date and start_time into a datetime object
    current_time = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp('http://localhost:9222')
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        for chapter_folder in chapter_folders[start_index:]:
            chapter_path = os.path.join(manga_path, chapter_folder)
            print(f"Procesando capítulo: {chapter_folder}")
            
            # Format date and time for the replicate_actions function
            formatted_date = current_time.strftime("%Y-%m-%d")
            formatted_time = current_time.strftime("%H:%M")
            replicate_actions(page, chapter_path, hashtags, formatted_date, formatted_time)
            
            # Increase the time by 10 minutes
            current_time += timedelta(minutes=10)
            
            # If the time reaches 23:55, we move to the next day at 00:00
            if current_time.minute == 0 and current_time.hour == 0:
                current_time += timedelta(days=1)

def is_valid_path(path):
    """Valida si la ruta proporcionada existe y es un directorio."""
    return os.path.isdir(path)

def is_valid_hashtags(hashtags):
    """Valida que los hashtags tengan el formato correcto."""
    return all(re.match(r"^#[a-zA-Z0-9_]+$", tag) for tag in hashtags)

def main():
    while True:
        manga_path = input("Introduce la ruta al directorio de videos: ")
        if not is_valid_path(manga_path):
            print(f"Ruta no válida: {manga_path}. Verifica que exista el directorio.")
            continue

        user_hashtags = input("Introduce hashtags separados por comas: ")
        hashtags_list = [f"#{tag.strip()}" for tag in user_hashtags.split(',')]

        if not is_valid_hashtags(hashtags_list):
            print("Formato de hashtags no válido. Asegúrate de que empiecen con '#' y sean alfanuméricos.")
            continue
        wait(5)
        process_chapters(manga_path, hashtags_list)
        break

main()