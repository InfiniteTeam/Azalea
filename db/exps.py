from utils import datamgr
from utils.basecog import BaseCog
import random

def fishing(*, req: int, fish: datamgr.Item):
    rand = random.uniform(0.02, 0.06)
    return round(fish.meta['exp_multiple']*(req*rand+10))