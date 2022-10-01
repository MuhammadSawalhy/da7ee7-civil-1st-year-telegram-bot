from time import sleep
from tqdm import tqdm
from utils.logging import logging, logging_setup_file, logging_setup_tqdm

logging_setup_tqdm()
logging_setup_file(".log")

for i in tqdm(range(10)):
    logging.info(str(i))
    sleep(1)

print('Done!')
