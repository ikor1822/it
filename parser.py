from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import csv



def select_department():
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

browser = webdriver.Chrome()
browser.get("https://mai.ru/education/studies/schedule/groups.php")

# Закрытие баннера с куками
try:
    cookie_button = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@data-bs-dismiss='alert']"))
    )
    cookie_button.click()
    WebDriverWait(browser, 5).until(
        EC.invisibility_of_element_located((By.XPATH, "//button[@data-bs-dismiss='alert']"))
    )
except:
    pass

select_department()

group = WebDriverWait(browser, 5).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="nav-1-1-eg1"]/a[1]'))
)
ActionChains(browser).move_to_element(group).perform()
group.click()


with open("groups.txt", "r", encoding="utf-8") as file:
    gro = [line.strip() for line in file]



for gr in gro:
    select_department()
    if gr[4] == '1':
        if gr[7] == 'Б':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-1-3-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
        elif gr[7] == 'С':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-1-2-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
        elif gr[7] == 'А':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-1-1-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
    elif gr[4] == '2':
        if gr[7] == 'Б':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-2-1-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
        elif gr[7] == 'М':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-2-2-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
        elif gr[7] == 'А':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-2-3-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()   
    elif gr[4] == '3':
        if gr[7] == 'Б':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-3-1-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
        elif gr[7] == 'А':
            elem = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "nav-3-2-tab"))
            )
            ActionChains(browser).move_to_element(elem).perform()
            elem.click()
    elif gr[4] == '4':
        elem = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.ID, "nav-4-1-tab"))
        )
        ActionChains(browser).move_to_element(elem).perform()
        elem.click()



    
    link1 = f"//a[@href='index.php?group={gr}']"
    group = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.XPATH, link1)))
    ActionChains(browser).move_to_element(group).perform()
    group.click()


    for n in range(1, 19):
        # Переход на нужную неделю
        WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div/div[1]/article/div[3]/div/a[2]"))).click()
        link = f'/html/body/main/div/div/div[1]/article/div[4]/div/div/ul/li[{n}]/a'
        WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.XPATH, link))).click()

        # текст расписания
        day = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/main/div/div/div[1]/article/ul"))
        )
        a = day.text









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
                    teacher, classroom = "", ""

                    match_details = re.match(r"^(.*?)\s+((?:ГУК|Орш\.|--каф\.)\s+.+)$", details)
                    if match_details:
                        teacher = match_details.group(1).strip()
                        classroom = match_details.group(2).strip()
                    else:
                        if re.match(r"^(ГУК|Орш\.|--каф\.)", details):
                            classroom = details
                        else:
                            teacher = details

                    filtered_schedule.append((current_subject, current_date, time_slot, lesson_type, teacher, classroom, gr))
                current_subject = ""
                lesson_type = ""

        # Запись в CSV
        with open("schedule.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if file.tell() == 0: 
                writer.writerow(["subject", "date", "time", "lesson_type", "teacher", "classroom", "group"])
            writer.writerows(filtered_schedule)

        print("Данные успешно записаны в schedule.csv!")
    back = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div/div[1]/article/div[3]/div/a[1]"))
    )
    ActionChains(browser).move_to_element(back).perform()
    back.click()




browser.quit()
