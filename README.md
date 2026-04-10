# Underground FUT Bot

Bot de Telegram para emparejar jugadores de FC Ultimate Team que juegan partidos por créditos (5, 10, 20, 50, 100).  
Valida reglas, gestiona pagos, hace matchmaking y registra resultados.

## 🚀 Flujo básico

1. El propietario añade un miembro al grupo.
2. El bot envía mensaje PRIVADO de bienvenida.
3. El usuario recibe el reglamento (ES/EN) y debe aceptarlo.
4. Una vez aceptado, escribe `PLAY` en privado.
5. Elige importe: 5, 10, 20, 50 o 100.
6. El bot le muestra el enlace de PayPal.
7. El usuario paga y pulsa “He pagado / I have paid”.
8. El admin valida el pago con `/validar`.
9. El bot hace matchmaking y empareja jugadores.
10. Tras el partido, cada uno reporta `/gane` o `/perdi`.

## 📁 Estructura del proyecto

```text
.
├── main.py
├── config.py
├── database.py
├── rules.py
├── requirements.txt
└── handlers
    ├── __init__.py
    ├── start.py
    ├── play.py
    ├── results.py
    └── admin.py
