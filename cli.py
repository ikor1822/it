import pickle
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import glob
import argparse

class ScheduleLoader:
    def __init__(self, cache_dir="schedule_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.browser = None
        self.options = Options()
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")

    def _get_cache_path(self, group, week):
        return os.path.join(self.cache_dir, f"{group}_week{week}.pkl")

    def _load_from_cache(self, group, week):
        path = self._get_cache_path(group, week)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None

    def _save_to_cache(self, group, week, data):
        path = self._get_cache_path(group, week)
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def _process_part(self, part):
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

    def _select_department(self):
        department = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "department"))
        ))
        department.select_by_visible_text("Институт №8")

        course = Select(WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, "course"))
        ))
        course.select_by_visible_text("Все курсы")

        button = WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Отобразить']"))
        )
        button.click()

    def _select_group_tab(self, group):
        group_map = {
            '1': {'Б': 'nav-1-3-tab', 'С': 'nav-1-2-tab', 'А': 'nav-1-1-tab'},
            '2': {'Б': 'nav-2-1-tab', 'М': 'nav-2-2-tab', 'А': 'nav-2-3-tab'},
            '3': {'Б': 'nav-3-1-tab', 'А': 'nav-3-2-tab'},
            '4': {'А': 'nav-4-1-tab'}
        }

        course = group[4]
        subgroup = group[7] if len(group) > 7 else 'А'
        
        if course in group_map and subgroup in group_map[course]:
            tab_id = group_map[course][subgroup]
            elem = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.ID, tab_id))
            )
            ActionChains(self.browser).move_to_element(elem).perform()
            elem.click()

    def load_schedule(self, group, week, subject=None):
        cached_data = self._load_from_cache(group, week)
        if cached_data:
            return self._filter_subject(cached_data, subject) if subject else cached_data

        self.browser = webdriver.Chrome(options=self.options)
        try:
            self.browser.get("https://mai.ru/education/studies/schedule/groups.php")

            try:
                cookie_button = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-bs-dismiss='alert']"))
                )
                cookie_button.click()
                WebDriverWait(self.browser, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, "//button[@data-bs-dismiss='alert']"))
                )
            except Exception:
                pass

            self._select_department()

            group_link = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="nav-1-1-eg1"]/a[1]'))
            )
            ActionChains(self.browser).move_to_element(group_link).perform()
            group_link.click()

            self._select_department()
            self._select_group_tab(group)

            link1 = f"//a[@href='index.php?group={group}']"

            group_elem = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, link1))
            )
            ActionChains(self.browser).move_to_element(group_elem).perform()
            group_elem.click()

            WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div/div[1]/article/div[3]/div/a[3]"))
            ).click()
            week_link = f'/html/body/main/div/div/div[1]/article/div[4]/div/div/ul/li[{week}]/a'
            WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, week_link))
            ).click()

            day = self.browser.find_element(By.XPATH, "/html/body/main/div/div/div[1]/article/ul")
            lines = day.text.split("\n")
            schedule = []
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
                        teacher, classroom = self._process_part(details)
                        schedule.append({
                            'subject': current_subject,
                            'lesson_type': lesson_type,
                            'date': current_date,
                            'time': time_slot,
                            'teacher': teacher,
                            'classroom': classroom,
                            'group': group,
                            'week': week
                        })
                    current_subject = ""
                    lesson_type = ""

            self._save_to_cache(group, week, schedule)
            return self._filter_subject(schedule, subject) if subject else schedule

        finally:
            if self.browser:
                self.browser.quit()

    def _filter_subject(self, schedule, subject):
        return [record for record in schedule if subject.lower() in record['subject'].lower()]

    def search_cache(self, subject=None, teacher=None, group=None):
        results = []
        cache_files = glob.glob(os.path.join(self.cache_dir, "*.pkl"))

        for cache_file in cache_files:
            filename = os.path.basename(cache_file)
            try:
                group_name, week_part = filename.replace('.pkl', '').split('_week')
                week_num = int(week_part)
            except ValueError:
                continue

            with open(cache_file, 'rb') as f:
                schedule = pickle.load(f)
                for record in schedule:
                    match = True
                    entry_group = record.get('group', group_name)
                    if subject and subject.lower() not in record['subject'].lower():
                        match = False
                    if teacher and teacher.lower() not in record.get('teacher', '').lower():
                        match = False
                    if group and group.lower() not in entry_group.lower():
                        match = False
                    if match:
                        record['group'] = entry_group
                        record.setdefault('week', week_num)
                        results.append(record)

        return results

def print_schedule(schedule):
    if not schedule:
        print("Нет данных в кэше по указанным критериям")
        return
    for record in schedule:
        group = record.get('group', 'Не указана')
        week = record.get('week', 'Не указана')
        print(f"\nГруппа: {group} | Неделя: {week}")
        print(f"Предмет: {record['subject']} {record['lesson_type']}")
        print(f"Дата: {record['date']}")
        print(f"Время: {record['time']}")
        if record['teacher']:
            print(f"Преподаватель: {record['teacher']}")
        if record['classroom']:
            print(f"Аудитория: {record['classroom']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group')
    parser.add_argument('--week', type=int)
    parser.add_argument('--subject')
    parser.add_argument('--teacher')
    parser.add_argument('--cache-only', action='store_true')

    args = parser.parse_args()

    loader = ScheduleLoader()

    if args.cache_only:
        found = loader.search_cache(subject=args.subject, teacher=args.teacher, group=args.group)
        print_schedule(found)
        return

    if args.group and args.week:
        data = loader.load_schedule(args.group, args.week, args.subject)
        print_schedule(data)
    else:
        found = loader.search_cache(subject=args.subject, teacher=args.teacher, group=args.group)
        print_schedule(found)

if __name__ == "__main__":
    main()
