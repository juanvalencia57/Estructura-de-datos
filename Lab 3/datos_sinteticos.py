import random

FIRST_NAMES = (
    "Ariadna", "Bruno", "Celia", "Dario", "Ema", "Fabian",
    "Greta", "Hugo", "Irene", "Jonas", "Kiara", "Lautaro",
    "Mara", "Nicolas", "Olga", "Rafael", "Tania", "Ulises",
)
FAMILY_NAMES = (
    "Acosta", "Benitez", "Cabrera", "Dominguez", "Escobar",
    "Ferreyra", "Gimenez", "Herrera", "Ibarra", "Juarez",
)


def generate_students(count=10000, sorted_input=False, seed=None):
    if count < 1:
        raise ValueError("Count must be positive")

    rng = random.Random(seed)
    keys = list(range(1001, count + 1001))
    if not sorted_input:
        rng.shuffle(keys)

    records = []
    for key in keys:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(FAMILY_NAMES)}"
        records.append({
            "id": key,
            "name": name,
            "age": rng.randint(17, 30),
            "average": round(3.0 + rng.random() * 7.0, 2),
        })
    return records
