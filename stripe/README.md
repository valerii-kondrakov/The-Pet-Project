# Stripe Checkout Demo (Django)

Демонстрационный проект, повторяющий рекомендуемый Stripe Checkout flow из официальной документации:

- [Docs Home](https://docs.stripe.com/)
- [Accept a payment (Checkout)](https://docs.stripe.com/payments/accept-a-payment?integration=checkout)

Проект показывает полный цикл: создание Checkout Session на бэкенде, редирект клиента в Stripe, обработка успеха/отмены и прием вебхуков.

## Возможности

- Django 5 + Stripe Python SDK 10.
- Создание `checkout.Session` на сервере с защитой ключей.
- Клиентский редирект через Stripe.js и graceful обработка ошибок.
- Success/Cancel страницы для обратного UX.
- Webhook endpoint с валидацией подписи для `checkout.session.completed`.
- Готовый README и `.env` шаблон с нужными переменными.

## Как запустить

1. **Зависимости**
   ```bash
   cd path/to/stripe/config
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r ../requirements.txt
   ```
2. **Настройте переменные**
   - Скопируйте `env.example` → `.env` (в корне репозитория).
   - Заполните ключи из [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys):
     - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`
     - `STRIPE_PRICE_ID` — возьмите ID заранее созданного Price
     - `STRIPE_WEBHOOK_SECRET` появится после настройки webhook через Stripe CLI или Dashboard.
3. **Запуск**
   ```bash
   cd d:\vyz\kurs2\pet\stripe\config
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
4. **Тестовые карты**
   - Используйте номера из [Stripe docs](https://docs.stripe.com/testing).

## Вебхуки

Stripe Checkout подтверждает платеж асинхронно. Чтобы зафиксировать статус на сервере, запустите Stripe CLI в отдельном окне:

```bash
stripe login
stripe listen --forward-to localhost:8000/webhook/
```

Секрет из первой команды вставьте в `STRIPE_WEBHOOK_SECRET`. Event `checkout.session.completed` попадет в Django и появится в логах.

## Как это работает

1. Пользователь открывает `/` → шаблон `payments/checkout.html`. Ключ publishable передается в JS.
2. Кнопка «Перейти к оплате» отправляет `POST /create-checkout-session/` с CSRF-токеном.
3. Представление `create_checkout_session` вызывает `stripe.checkout.Session.create(...)` c `price_id`, `success_url`, `cancel_url`.
4. Ответ содержит `sessionId`, который передается в `stripe.redirectToCheckout`.
5. Stripe показывает безопасную форму, затем возвращает на `success` или `cancel`.
6. Параллельно Stripe шлет webhook → `payments.stripe_webhook`, где мы валидируем подпись и фиксируем `checkout.session.completed`.

## Структура

```
.
├── config/                # Django project root
│   ├── config/            # settings, urls, wsgi/asgi
│   ├── payments/          # приложение с view, urls и шаблонами
│   ├── templates/         # базовые шаблоны (для расширения)
│   └── static/payments/   # стили интерфейса
├── requirements.txt
├── env.example
└── README.md
```

## Дальнейшие шаги

- Добавьте сохранение заказа в БД и связь с пользовательскими аккаунтами.
- Храните чувствительные события Stripe в отдельной модели для аудита.
- Включите CSRF Trusted Origins/HTTPS в продакшне и прокиньте собственный домен в `.env`.

