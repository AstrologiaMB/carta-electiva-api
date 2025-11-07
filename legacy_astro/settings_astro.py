from immanuel.setup import settings
from immanuel.const import calc,dignities,chart

def astro_avanzada_settings():
    settings.planet_orbs = {
            calc.CONJUNCTION: 10.0,
            calc.OPPOSITION: 10.0,
            calc.SQUARE: 10.0,
            calc.TRINE: 10.0,
            calc.SEXTILE: 6.0,
            calc.SEPTILE: 3.0,
            calc.SEMISQUARE: 3.0,
            calc.SESQUISQUARE: 3.0,
            calc.SEMISEXTILE: 3.0,
            calc.QUINCUNX: 3.0,
            calc.QUINTILE: 2.0,
            calc.BIQUINTILE: 2.0,
        }
    settings.set({
    'triplicities':dignities.LILLEAN_TRIPLICITIES,
    'terms':dignities.PTOLEMAIC_TERMS,
    'rulerships':dignities.TRADITIONAL_RULERSHIPS,
    'house_system':chart.REGIOMONTANUS})

    return True