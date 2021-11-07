import requests
from pprint import pp, pprint


def predict_rub_salary_page(vacancies):
    salaries = list()
    for vacancy in vacancies:
        if vacancy["salary"] is None:
            continue
        if vacancy["salary"]["currency"] != "RUR":
            continue
        if vacancy["salary"]["from"] is not None and vacancy["salary"]["to"] is not None:
            salaries.append((vacancy["salary"]["from"] + vacancy["salary"]["to"]) / 2)
        elif vacancy["salary"]["from"] is not None:
            salaries.append(vacancy["salary"]["from"] * 1.2)
        else:
            salaries.append(vacancy["salary"]["to"] * 0.8)
    return salaries

def fetch_vacancies_hh(language, area=1):
    payload = {"text": f"Программист {language}", "area": area}
    response = requests.get(url="https://api.hh.ru/vacancies", params=payload)
    response.raise_for_status()
    vacancies = response.json()
    vacancies_found = vacancies["found"]
    salaries = list()
    salaries = predict_rub_salary_page(vacancies["items"])
    for page in range(1, vacancies["pages"]):
        payload["page"] = page
        response = requests.get(url="https://api.hh.ru/vacancies", params=payload)
        response.raise_for_status()
        vacancies = response.json()
        salaries += predict_rub_salary_page(vacancies["items"])
    return dict([
        ("vacancies_found", vacancies_found),
        ("vacancies_processed", len(salaries)),
        ("average_salary", int(sum(salaries) / len(salaries)))
        ])


def fetch_vacancies_sj():
    pass

def main():
    """ HH area 51-Сыктывкар, 66-Нижний Новгород, 1-Москва, 54-Краснодар, ..."""
    languages = ["python", "java", "PHP"]
    vacancies_summary_hh = dict()
    for language in languages:
        vacancies_summary_hh[language] = fetch_vacancies_hh(language)
    pprint(vacancies_summary_hh)


if __name__ == "__main__":
    main()
