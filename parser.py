from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import csv

def select_department(browser):
    department = Select(WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.ID, "department"))
    ))
    department.select_by_visible_text("Институт №8")
    
    course = Select(WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.ID, "course"))
    ))
    course.select_by_visible_text("Все курсы")
    
    button = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Отобразить']"))
    )
    button.click()

def process_part(part):
    part = part.strip()
    teacher = ""
    classroom = ""
    markers = ["ГУК", "Орш.", "--каф."]
    
    for marker in markers:
        if marker in part:
            try:
                teacher, room = part.split(marker, 1)
                classroom = f"{marker} {room.strip()}"
                teacher = teacher.strip()
                break
            except ValueError:
                classroom = part
                teacher = ""
    else:
        words = part.split()
        for i in range(len(words) - 1, -1, -1):
            if re.match(r"\d+-\d+", words[i]):  
                classroom = words[i]
                teacher = " ".join(words[:i])
                break
        else:
            if re.match(r"^[А-Яа-яЁё\s,\.]+$", part) and len(words) >= 2:
                teacher = part
            else:
                classroom = part
    
    return teacher, classroom

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(options=options)
    browser.get("https://mai.ru/education/studies/schedule/groups.php")
    
    try:
        cookie_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-bs-dismiss='alert']"))
        )
        cookie_button.click()
        WebDriverWait(browser, 5).until(
            EC.invisibility_of_element_located((By.XPATH, "//button[@data-bs-dismiss='alert']"))
        )
    except Exception as e:
        print("Нет Куки")
    
    select_department(browser)
    
    group = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="nav-1-1-eg1"]/a[1]'))
    )
    ActionChains(browser).move_to_element(group).perform()
    group.click()
    
    with open("groups.txt", "r", encoding="utf-8") as file:
        gro = [line.strip() for line in file]
    
    for gr in gro:
        select_department(browser)

        if gr[4] == '1':
            if gr[7] == 'Б':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-1-3-tab"))
                )
            elif gr[7] == 'С':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-1-2-tab"))
                )
            elif gr[7] == 'А':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-1-1-tab"))
                )
        elif gr[4] == '2':
            if gr[7] == 'Б':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-2-1-tab"))
                )
            elif gr[7] == 'М':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-2-2-tab"))
                )
            elif gr[7] == 'А':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-2-3-tab"))
                )
        elif gr[4] == '3':
            if gr[7] == 'Б':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-3-1-tab"))
                )
            elif gr[7] == 'А':
                elem = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.ID, "nav-3-2-tab"))
                )
        elif gr[4] == '4':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-4-1-tab"))
            )
        
        ActionChains(browser).move_to_element(elem).perform()
        elem.click()
    
        link1 = f"//a[@href='index.php?group={gr}']"
        group = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, link1))
        )
        ActionChains(browser).move_to_element(group).perform()
        group.click()
    
        for n in range(1, 19):
            try:
                WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "/html/body/main/div/div/div[1]/article/div[3]/div/a[3]"))
                ).click()
                link = f'/html/body/main/div/div/div[1]/article/div[4]/div/div/ul/li[{n}]/a'
                WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, link))
                ).click()
                
                day = browser.find_element(By.XPATH, "/html/body/main/div/div/div[1]/article/ul")
                a = day.text
            except Exception as e:
                print("нет пар")
                continue
            
            lines = a.split("\n")
            filtered_schedule = []
            current_date = ""
            current_subject = ""
            lesson_type = ""
            
            for line in lines:
                line = line.strip()
                if re.match(r"^(Пн|Вт|Ср|Чт|Пт|Сб),", line):
                    current_date = line.replace(",", "")
                elif "ПЗ" in line or "ЛР" in line:
                    current_subject = line
                    m = re.search(r"(ПЗ|ЛР)", current_subject)
                    if m:
                        lesson_type = m.group(1)
                        current_subject = current_subject.replace(lesson_type, "").strip()
                    else:
                        lesson_type = ""
                elif "–" in line and current_subject:
                    match = re.match(r"(\d{2}:\d{2} – \d{2}:\d{2})\s*(.*)", line)
                    if match:
                        time_slot = match.group(1)
                        details = match.group(2).strip()
                        teacher, classroom = process_part(details)
                        
                        filtered_schedule.append(
                            (current_subject, current_date, time_slot, lesson_type, teacher, classroom, gr)
                        )
                    current_subject = ""
                    lesson_type = ""

            with open("schedule.csv", "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=";")
                if file.tell() == 0:
                    writer.writerow(["subject", "date", "time", "lesson_type", "teacher", "classroom", "group"])
                writer.writerows(filtered_schedule)
    
            print(f'данные записаны для недели {n}')

        back = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div/div[1]/article/div[3]/div/a[1]"))
        )
        ActionChains(browser).move_to_element(back).perform()
        back.click()
    
    browser.quit()

if __name__ == '__main__':
    main()