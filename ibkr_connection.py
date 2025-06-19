
import logging
from ib_insync import IB

class IBKRConnectionError(Exception):
    pass

def setup_logger(log_file='ibkr_api.log'):
    logger = logging.getLogger('IBKR')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

logger = setup_logger()

def connect_ibkr(read_only=True, host='127.0.0.1', port=7497, client_id=1):
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id)
        logger.info(f"Connected to IBKR API at {host}:{port} with clientId={client_id}")
    except Exception as e:
        logger.error(f"Failed to connect to IBKR API: {e}")
        raise IBKRConnectionError(f"Failed to connect to IBKR API: {e}")

    if read_only:
        logger.info("Connection established in read-only mode.")
        print("[INFO] Connected to IBKR API in read-only mode (no orders allowed).")
    else:
        logger.warning("Connection established with write access! Be careful with orders!")
        print("[WARNING] Connected with write access enabled. Be careful with orders!")

    return ib

def confirm_order_placement(order_desc: str):
    """
    Ask user to confirm order placement before sending.
    """
    print(f"\n⚠️ About to place order: {order_desc}")
    answer = input("Type 'YES' to confirm order placement: ")
    if answer.strip().upper() == 'YES':
        logger.info(f"Order confirmed by user: {order_desc}")
        return True
    else:
        logger.info(f"Order denied by user: {order_desc}")
        print("Order placement cancelled by user.")
        return False
