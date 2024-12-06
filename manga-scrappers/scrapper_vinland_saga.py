import os
import time

from playwright.sync_api import sync_playwright


def save_image_manually(page, image_url, folder, page_number):
    """Simulates manual downloading of an image by opening it and saving it."""
    # Create a new browser context and page
    page.goto(image_url)

    # Wait for the image to load
    page.wait_for_load_state("load")

    # Save the image to the specified folder
    filepath = os.path.join(folder, f"{page_number}.jpeg")
    with open(filepath, "wb") as file:
        file.write(page.screenshot(full_page=True))

    print(f"Saved: {filepath}")

def scroll_to_bottom_slowly(page, scroll_delay=2):
    """Scroll to the bottom of the page slowly, pausing for the specified delay."""
    previous_height = 0
    while True:
        # Scroll down the page
        page.evaluate("window.scrollBy(0, window.innerHeight)")
        time.sleep(scroll_delay)

        # Check if we have reached the bottom
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break  # No more scrolling possible
        previous_height = current_height

def scrape_chapter_images(base_url, chapter_number, output_folder):
    """Scrape images for a specific chapter."""
    chapter_url = base_url.format(number=chapter_number)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(chapter_url)
        
         # Buscar si la página contiene el mensaje de error
        error_element = page.query_selector('div.font-bold.text-4xl.text-center')
        
        if error_element and '404 - Waifu Page Not Found' in error_element.text_content():
            print(f"Capítulo {chapter_number} no disponible (Error 404). Terminando descarga.")
            return False

        # Wait for the page to load completely
        page.wait_for_selector('h1.text-lg')  # Ensure the header is loaded

        # Perform slow scroll to load all images
        scroll_to_bottom_slowly(page)

        # Extract chapter title (optional, used for naming)
        chapter_title = page.locator('h1.text-lg').inner_text()

        # Ensure the output folder exists
        chapter_folder = os.path.join(output_folder, f"{chapter_title}")
        os.makedirs(chapter_folder, exist_ok=True)

        # Locate image elements and extract src attributes into an array
        image_elements = page.locator('//img[contains(@class, "js-page")]')
        image_sources = image_elements.evaluate_all("elements => elements.map(el => el.src)")

        if not image_sources:
            print("No images found. Verify the selector.")
            return

        # Save each image using the src values from the array
        for i, image_url in enumerate(image_sources, start=1):
            try:
                save_image_manually(page, image_url, chapter_folder, i)
            except Exception as e:
                print(f"Error saving image {i}: {e}")

        page.close()
        browser.close()

def main():
    base_url = "https://ww4.readvinlandsaga.com/chapter/vinland-saga-chapter-{number}/"
    output_folder = "C:/me/content/manga-videos/mangas/vinland-saga/"  # Directory to save images
    chapter = 12
     
    os.makedirs(output_folder, exist_ok=True)

    while True:
        print(f"Intentando descargar el capítulo {chapter}...")
        scrape_chapter_images(base_url, chapter, output_folder)
        chapter += 1  # Incrementamos el número del capítulo

if __name__ == "__main__":
    main()
