import os
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env si le fichier existe
load_dotenv()

# Mode sandbox (false en production)
MODE_SANDBOX = os.getenv("MODE_SANDBOX", "true").lower() == "true"

# Tokens d'accès à l'API
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "FLOWGLOBAL2025")

# Clés API des exchanges
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "A_REMPLACER")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "A_REMPLACER")
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "A_REMPLACER") 
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "A_REMPLACER")

# Configuration des logs
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/flowglobal.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Limites de la plateforme
MAX_CONCURRENT_OPERATIONS = int(os.getenv("MAX_CONCURRENT_OPERATIONS", "5"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

# Configuration spécifique aux stratégies
# FlowByteBeat
FLOWBYTEBEAT_MAX_LEVERAGE = float(os.getenv("FLOWBYTEBEAT_MAX_LEVERAGE", "10.0"))
FLOWBYTEBEAT_DEFAULT_TIMEFRAME = os.getenv("FLOWBYTEBEAT_DEFAULT_TIMEFRAME", "1h")

# FlowSniper
FLOWSNIPER_MAX_ENTRIES = int(os.getenv("FLOWSNIPER_MAX_ENTRIES", "3"))
FLOWSNIPER_DEFAULT_SLIPPAGE = float(os.getenv("FLOWSNIPER_DEFAULT_SLIPPAGE", "0.05"))

# FlowUpSpin
FLOWUPSPIN_DEFAULT_TRADE_SIZE = float(os.getenv("FLOWUPSPIN_DEFAULT_TRADE_SIZE", "0.01"))
FLOWUPSPIN_SMART_EXIT = os.getenv("FLOWUPSPIN_SMART_EXIT", "true").lower() == "true"
