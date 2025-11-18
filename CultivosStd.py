from CultivoData import load_cultivo
import os 
import pandas as pd

xl = pd.ExcelFile("./data/2730325-cuadros-en-excel-del-anuario-produccion-agricola-2022.xlsx")
cultivos = xl.sheet_names[7:]
#['acelga', 'aji', 'ajo', 'albahaca',PASTOS FORRAJEROS, rocoto, fpalo, caña, algodon, SEMIPERMAMENTES, PERMANENTES:

rows = []   # almacenamos todas las filas aquí

for cultivo in cultivos:
    print(cultivo + "  ==============================================")
    try:
        print(f"Procesando: {cultivo}...")

        df = load_cultivo(cultivo)

        # Cálculo de std
        output_json = (
            df[["d-m-y", "produccion", "precio"]]
            .groupby(by=["d-m-y"], as_index=False)
            .mean()
            .drop(columns=["d-m-y"])
            .std(axis=0)
            .to_dict()
        )

        row = {
            "cultivo": cultivo,
            "produccion_std": output_json["produccion"],
            "precio_std": output_json["precio"]
        }

        rows.append(row)

    except Exception as e:
        print(f"❌ Error con {cultivo}: {e}")
        continue


# === Guardar todo al final ===
csv_path = "stdCultivos.csv"
df_out = pd.DataFrame(rows)
df_out.to_csv(csv_path, index=False)

print("\n======================================")
print("   ✅ Archivo generado:", csv_path)
print("   🧾 Filas creadas:", len(df_out))
print("======================================\n")
