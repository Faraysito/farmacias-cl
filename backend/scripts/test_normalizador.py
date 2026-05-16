from app.normalizador import normalizar

ejemplos = [
    "Cozaar (R) Losartán 50mg 30 Comprimidos Recubiertos",
    "Losartan (B) 50mg 30 Comprimidos Recubiertos",
    "Losapres (B) Losartán 100mg 30 Comprimidos Recubiertos",
    "Losartán Potásico 50 mg",
    "Corodin (B) Losartán Potásico 50mg 30 Comprimidos Recubiertos",
    "Losartan / Hidroclorotiazida (B) 50/12.5 30 Comprimidos",
]

for n in ejemplos:
    print(f"{n[:55]:<55} -> {normalizar(n)}")