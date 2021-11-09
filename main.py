import os

from itertools import count
from statistics import mean

import requests

from dotenv import load_dotenv
from terminaltables import SingleTable


def lang_table(vacancies, title):
    rows = list()
    rows.append([
        "Язык программирования",
        "Вакансий найдено",
        "Вакансий обработано",
        "Средняя зарплата"])
    for key, value in vacancies.items():
        rows.append([
            key,
            value["vacancies_found"],
            value["vacancies_processed"],
            value["average_salary"]])
    return SingleTable(rows, title).table


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return mean((salary_from, salary_to))
    elif salary_from:
        return salary_from * 1.2
    else:
        return salary_to * 0.8


def predict_rub_salary_sj(vacancy):
    if vacancy["payment_from"] == 0 \
        and vacancy["payment_to"] == 0 \
            or vacancy["currency"] != "rub":
        return None
    return predict_salary(vacancy["payment_from"], vacancy["payment_to"])


def predict_rub_salary_hh(vacancy):
    if vacancy["salary"] is None or vacancy["salary"]["currency"] != "RUR":
        return None
    return predict_salary(vacancy["salary"]["from"], vacancy["salary"]["to"])


def fetch_vacancies_hh(language, area=1):
    payload = {
        "text": f"Программист {language}",
        "area": area,
        "per_page": 100
        }
    salaries = []
    all_vacancies = []
    for page in count(0):
        if payload["per_page"] * (page + 1) >= 2000: break
        payload.update({"page": page})
        page_response = requests.get(
            "https://api.hh.ru/vacancies",
            params=payload
            )
        page_response.raise_for_status()
        page_data = page_response.json()
        all_vacancies.extend(page_data["items"])
        if page >= page_data["pages"]:
            break
    vacancies_found = page_data["found"]
    for vacancy in all_vacancies:
        salary = predict_rub_salary_hh(vacancy)
        if salary is not None:
            salaries.append(int(salary))
    return dict([
        ("vacancies_found", vacancies_found),
        ("vacancies_processed", len(salaries)),
        ("average_salary", int(mean(salaries)))
        ])


def fetch_vacancies_sj(language, sj_secret_key, town=4):
    payload = {
        "keyword": f"Программист {language}",
        "town": town,
        "count": 100,
        "catalogues": 33
        }
    headers = {"X-Api-App-Id": sj_secret_key}
    salaries = []
    all_vacancies = []
    for page in count():
        payload.update({"page": page})
        page_response = requests.get(
            "https://api.superjob.ru/2.0/vacancies/",
            headers=headers, params=payload
            )
        page_response.raise_for_status()
        page_data = page_response.json()
        all_vacancies.extend(page_data["objects"])
        if not page_data["more"]:
            break
    vacancies_found = page_data["total"]
    for vacancy in all_vacancies:
        salary = predict_rub_salary_sj(vacancy)
        if salary is not None:
            salaries.append(int(salary))
    return dict([
        ("vacancies_found", vacancies_found),
        ("vacancies_processed", len(salaries)),
        ("average_salary", int(mean(salaries)))
        ])


def main():
    load_dotenv()
    sj_secret_key = os.getenv("SJ_SECRET_KEY")
    """
    area 66-Нижний Новгород, 1-Москва, 54-Краснодар... https://api.hh.ru/areas
    town 12-Нижний Новгород, 4-Москва, 25-Краснодар... https://api.superjob.ru/2.0/towns/
    """
    languages = ["Python", "Java", "1C"]
    vacancies_summary_hh = dict()
    vacancies_summary_sj = dict()
    for language in languages:
        vacancies_summary_hh[language] = fetch_vacancies_hh(language, 1)
        vacancies_summary_sj[language] = fetch_vacancies_sj(language, sj_secret_key, 4)
    print(lang_table(vacancies_summary_hh, "HeadHunter Moscow"))
    print(lang_table(vacancies_summary_sj, "Supejob Moscow"))


if __name__ == "__main__":
    main()
