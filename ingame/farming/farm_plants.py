from utils.gamemgr import FarmPlant
from utils.gamemgr import FarmPlantStatus as st

PLANTS = (
    FarmPlant('rice', '🌾', '벼', 'rice_plant', (5, 10), growtime={st.Growing: (12000, 14200), st.AllGrownUp: None}, exp=1.2),
    FarmPlant('wheat', '🌾', '밀', 'wheat', (7, 12), growtime={st.Growing: (8000, 10000), st.AllGrownUp: None}, exp=1),
)