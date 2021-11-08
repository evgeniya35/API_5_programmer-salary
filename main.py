import requests
import os

from dotenv import load_dotenv
from itertools import count
from statistics import mean
from terminaltables import SingleTable
import json


def lang_table(vacancies, title):
    rows = list()
    rows.append(["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"])
    for key, value in vacancies.items():
        rows.append([key, value["vacancies_found"], value["vacancies_processed"], value["average_salary"]])
    return SingleTable(rows, title).table


def predict_rub_salary_page_sj(vacancies):
    salaries = list()
    for vacancy in vacancies:
        if vacancy["payment_from"] == 0 and vacancy["payment_to"] == 0 or vacancy["currency"] != "rub":
            continue
        elif vacancy["payment_from"] == 0:
            salaries.append(vacancy["payment_to"] * 0.8)
        elif vacancy["payment_to"] == 0:
            salaries.append(vacancy["payment_from"] * 1.2)
        else:
            salaries.append(mean([vacancy["payment_from"], vacancy["payment_to"]]))
    return salaries


def predict_rub_salary_page_hh(vacancies):
    salaries = list()
    for vacancy in vacancies:
        if vacancy["salary"] is None:
            continue
        if vacancy["salary"]["currency"] != "RUR":
            continue
        if vacancy["salary"]["from"] is not None and vacancy["salary"]["to"] is not None:
            salaries.append(mean([vacancy["salary"]["from"], vacancy["salary"]["to"]]))
        elif vacancy["salary"]["from"] is not None:
            salaries.append(vacancy["salary"]["from"] * 1.2)
        else:
            salaries.append(vacancy["salary"]["to"] * 0.8)
    return salaries


def fetch_vacancies_hh(language, area=1):
    payload = {"text": f"Программист {language}", "area": area}
    salaries = list()
    for page in count(0):
        payload.update({"page": page})
        page_response = requests.get("https://api.hh.ru/vacancies", params=payload)
        page_response.raise_for_status()
        page_data = page_response.json()
        vacancies_found = page_data["found"]
        if page >= page_data["pages"]:
            break
        salaries += predict_rub_salary_page_hh(page_data["items"])
    return dict([
        ("vacancies_found", vacancies_found),
        ("vacancies_processed", len(salaries)),
        ("average_salary", int(mean(salaries)))
        ])


def fetch_vacancies_sj(language, sj_secret_key, town=4):
    payload = {"keyword": f"Программист {language}", "town": town, "count":100, "catalogues":33}
    headers = {"X-Api-App-Id": sj_secret_key}
    salaries = list()
    for page in count():
        payload.update({"page": page})
        page_response = requests.get("https://api.superjob.ru/2.0/vacancies/",
            headers=headers, params=payload)
        page_response.raise_for_status()
        page_data = page_response.json()
        salaries += predict_rub_salary_page_sj(page_data["objects"])
        if not page_data["more"]:
            break
    vacancies_found = page_data["total"]
    return dict([
        ("vacancies_found", vacancies_found),
        ("vacancies_processed", len(salaries)),
        ("average_salary", int(mean(salaries)))
        ])


def main():
    load_dotenv()
    sj_secret_key = os.getenv("SJ_SECRET_KEY")
    """ HH area 51-Сыктывкар, 66-Нижний Новгород, 1-Москва, 54-Краснодар, ..."""
    languages = ["python", "java", "PHP", "1C"]
    vacancies_summary_hh = dict()
    vacancies_summary_sj = dict()
    for language in languages:
        vacancies_summary_hh[language] = fetch_vacancies_hh(language, 66)
        vacancies_summary_sj[language] = fetch_vacancies_sj(language, sj_secret_key, 4)
    #with open("hh.json", "w") as f:
    #    json.dump(vacancies_summary_hh, f)
    print(lang_table(vacancies_summary_hh, "HeadHunter Moscow"))
    print(lang_table(vacancies_summary_sj, "Supejob Moscow"))

def main1():
    with open("hh.json", "r") as f:
        hh = json.load(f)
   
    print(lang_table(hh, "HeadHunter Moscow"))

if __name__ == "__main__":
    main()

