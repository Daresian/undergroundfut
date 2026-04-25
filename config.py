# config.py
# ─────────────────────────────────────────────────────────────
# RELLENA ESTOS VALORES ANTES DE ARRANCAR EL BOT
# ─────────────────────────────────────────────────────────────

# Token del bot — lo encontrarás en @BotFather
BOT_TOKEN = "8308224905:AAFDyD8gcydGFZfwAVsPF4G9Tn8136lXPhw"

# Tu ID personal de Telegram — escribe a @userinfobot para obtenerlo
ADMIN_ID =13493800

# ID del grupo principal.
# Cómo obtenerlo: en Telegram Web, abre el grupo y mira la URL.
# Si la URL es https://web.telegram.org/a/#-1001234567890 → el ID es -1001234567890
# Si la URL es https://web.telegram.org/a/#-1003985478277 → el ID es -1003985478277
GROUP_ID =-1003985478277

# Dirección PayPal donde los jugadores envían el dinero
PAYPAL_ADDRESS ="paypal.me/bucefalo74"

# Stakes disponibles en €
STAKES = [5, 10, 20, 50, 100]

# Usuarios de prueba: pon aquí los Telegram IDs (números)
# Estos usuarios se resetean cada vez que salen y entran al grupo
TEST_USERS = [8792953979,6452948848]  # Ejemplo: [123456789, 987654321]

# ─── Tiempos (no tocar salvo que sepas lo que haces) ──────────
TIMEOUT_PAGO_MINUTOS        = 15
TIMEOUT_CONTACTO_MINUTOS    = 15
TIMEOUT_JUGAR_MINUTOS       = 60
TIMEOUT_REPORTAR_MINUTOS    = 120
TIMEOUT_DISPUTA_HORAS       = 48
COOLDOWN_MINUTOS            = 10
BLOQUEO_HORAS               = 24

# Base de datos
DB_PATH = "futelite.db"
