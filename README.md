Нет отдельной ручки на создание категории и пока что заносим в бд её ручками:
```bash
docker exec -it zhigalev_delivery_club-db-1 psql -U delivery_user -d delivery_db
```

```bash
INSERT INTO package_types (id, name)
VALUES (1, 'Standard');
INSERT 0 1
```
```bash
SELECT * FROM package_types;
```

## Ручки реализованные в проекте:
1. Зарегистрировать посылку  

Метод: POST  
URL: http://localhost:8000/packages/

Body:  
```json
{
  "name": "International Parcel #101",
  "weight_kg": 3.45,
  "type_id": 1,
  "contents_value_usd": 250.00
}
```
2. Получить все типы посылок  
Метод: GET    
URL: http://localhost:8000/packages/types

Ожидаемый ответ:
```json
[
    {
        "id": 1,
        "name": "Standard"
    }
]
```

3. Получить данные о конкретной посылке  
Метод: GET  
URL: http://localhost:8000/packages/8d25a21a-f05d-4b3b-9f6f-6653216f059, `8d25a21a-f05d-4b3b-9f6f-6653216f059` где это UUID

Ожидаемый ответ:
```json
{
    "id": "8d25a21a-f05d-4b3b-9f6f-6653216f0593",
    "name": "International Parcel #101",
    "weight_kg": "3.450",
    "type_id": 1,
    "contents_value_usd": "250.00",
    "delivery_cost_rub": "344.99",
    "company_id": null,
    "created_at": "2025-10-23T10:07:57.336048Z"
}
```


4. Получить список своих посылок  
Метод: GET  
URL: http://localhost:8000/packages/?page=1&per_page=5&type_id=1

Ожидаем ответ:
```json
[
    {
        "id": "911d12f9-3e67-415d-9e5e-66de40d2f667",
        "name": "International Parcel #101",
        "weight_kg": "3.450",
        "type_id": 1,
        "contents_value_usd": "250.00",
        "delivery_cost_rub": "344.99",
        "company_id": null,
        "created_at": "2025-10-23T10:09:49.958981Z"
    },
    {
        "id": "8d25a21a-f05d-4b3b-9f6f-6653216f0593",
        "name": "International Parcel #101",
        "weight_kg": "3.450",
        "type_id": 1,
        "contents_value_usd": "250.00",
        "delivery_cost_rub": "344.99",
        "company_id": null,
        "created_at": "2025-10-23T10:07:57.336048Z"
    }
]
```

5. Привязать посылку к транспортной компании  
Запрос:  
POST http://localhost:8000/packages/packages/{pkg_id}/bind-company — {pkg_id} нужно подставить реальный UUID посылки.
Пример полного запроса:  
```bash
POST http://localhost:8000/packages/8d25a21a-f05d-4b3b-9f6f-6653216f0593/bind-company?company_id=2
 
```

6. Принудительный расчёт стоимости  
Запрос:  
POST http://localhost:8000/admin/trigger_compute

Ответ:
```json
{
  "processed_packages": 5
}
```