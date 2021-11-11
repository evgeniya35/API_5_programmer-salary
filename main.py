import os

from itertools import count
from statistics import mean

import requests

from dotenv import load_dotenv
from terminaltables import SingleTable


def print_vacancies(vacancies_stat, title):
    rows = list()
    rows.append([
        "Язык программирования",
        "Вакансий найдено",
        "Вакансий обработано",
        "Средняя зарплата"])
    for lang, vacancies in vacancies_stat.items():
        rows.append([
            lang,
            vacancies["vacancies_found"],
            vacancies["vacancies_processed"],
            vacancies["average_salary"]])
    return SingleTable(rows, title).table


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return mean((salary_from, salary_to))
    elif salary_from:
        return salary_from * 1.2
    else:
        return salary_to * 0.8


def predict_rub_salary_sj(vacancy):
    if not vacancy["payment_from"] and not vacancy["payment_to"] \
        or vacancy["currency"] != "rub":
        return None
    return predict_salary(vacancy["payment_from"], vacancy["payment_to"])


def predict_rub_salary_hh(vacancy):
    if not vacancy["salary"] or vacancy["salary"]["currency"] != "RUR":
        return None
    return predict_salary(vacancy["salary"]["from"], vacancy["salary"]["to"])


def agregate_hh_vacancies(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = predict_rub_salary_hh(vacancy)
        if salary:
            salaries.append(int(salary))
    return salaries


def find_hh_vacancies(language, area=1):
    payload = {
        "text": f"Программист {language}",
        "area": area,
        "per_page": 100
        }
    all_vacancies = []
    for page in count(0):
        # if payload["per_page"] * (page + 1) >= 2000: break
        payload.update({"page": page})
        page_response = requests.get(
            "https://api.hh.ru/vacancies",
            params=payload
            )
        page_response.raise_for_status()
        vacancies = page_response.json()
        all_vacancies.extend(vacancies["items"])
        if page >= vacancies["pages"] - 10:
            break
    vacancies_found = vacancies["found"]
    salaries = agregate_hh_vacancies(all_vacancies)
    return {
        "vacancies_found": vacancies_found,
        "vacancies_processed": len(salaries),
        "average_salary": int(mean(salaries))
    }


def find_sj_vacancies(language, sj_secret_key, town=4):
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
        vacancies = page_response.json()
        all_vacancies.extend(vacancies["objects"])
        if not vacancies["more"]:
            break
    vacancies_found = vacancies["total"]
    for vacancy in all_vacancies:
        salary = predict_rub_salary_sj(vacancy)
        if salary:
            salaries.append(int(salary))
    return {
        "vacancies_found": vacancies_found,
        "vacancies_processed": len(salaries),
        "average_salary": int(mean(salaries))
    }


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
        vacancies_summary_hh[language] = find_hh_vacancies(language, 1)
        vacancies_summary_sj[language] = find_sj_vacancies(language, sj_secret_key, 4)
    print(print_vacancies(vacancies_summary_hh, "HeadHunter Moscow"))
    print(print_vacancies(vacancies_summary_sj, "Supejob Moscow"))


if __name__ == "__main__":
    main()
