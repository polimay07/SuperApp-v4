import requests
import pandas as pd
import random
from datetime import datetime, timedelta


class CBRClient:
    @staticmethod
    def get_current_rates():
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()['Valute']
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка подключения к API ЦБ: {e}")
            raise

    @staticmethod
    def get_historical_data(currency_code='USD', days=30):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        url = f"https://api.frankfurter.app/{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}?from={currency_code}&to=RUB"

        try:
            print(f"🔄 Загрузка истории для {currency_code}...")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            dates = list(data['rates'].keys())
            rates = [rate['RUB'] for rate in data['rates'].values()]
            print("✅ Исторические данные успешно загружены.")

            # ВАЖНО: Имя колонки всегда одинаковое
            return pd.DataFrame({
                'Дата': dates,
                'Курс': rates
            })

        except Exception as e:
            print(f"⚠️ Не удалось загрузить историю из API ({e}). Генерирую демо-данные...")
            return CBRClient._generate_mock_data(currency_code, days)

    @staticmethod
    def _generate_mock_data(currency_code, days):
        base_rates = {
            'USD': 92.5,
            'EUR': 100.0,
            'CNY': 12.8,
            'GBP': 117.0
        }
        base_rate = base_rates.get(currency_code, 90.0)

        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]

        rates = []
        current = base_rate
        for _ in range(days):
            current += random.uniform(-0.8, 0.8)
            rates.append(round(current, 2))

        return pd.DataFrame({
            'Дата': dates,
            'Курс': rates
        })