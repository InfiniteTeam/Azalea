from utils.gamemgr import FarmPlant
from utils.gamemgr import FarmPlantStatus as st

PLANTS = (
    FarmPlant('rice', '벼', 'rice_plant', (5, 10), size=1),
    FarmPlant('wheat', '밀', 'wheat', (7, 12), size=2),
)