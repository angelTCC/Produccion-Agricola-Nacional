import pandas as pd
import numpy as np
import unicodedata

import argparse
import unicodedata

def remove_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def load_cultivo(cultivo, save):
   
    paths = [
        '2730325-cuadros-en-excel-del-anuario-produccion-agricola-2022.xlsx',
        'Cuadros en Excel del anuario _PRODUCCIÓN AGRÍCOLA_ 2021.xls',
        'Cuadros en Excel del anuario _PRODUCCIÓN AGRÍCOLA_ 2020.xls',
        'Cuadros en Excel del anuario _PRODUCCIÓN AGRÍCOLA_ 2019.xls'
    ]
    years = [2022, 2021, 2020, 2019]
    tables = {}

    '''
    extraccion de las tablas del cultivo, en todos los años (excel)
    '''
    for year, table in zip(years, paths):
        
        data = pd.read_excel("./data/"+table, sheet_name=cultivo)
        starts = data.index[data.apply(lambda r: r.astype(str).str.contains("Cuadro").any(), axis=1)]
        
        for start in starts:
            
            # nombre de la tabla
            for i in data.loc[start,:].dropna().values: # imprimiendo el titulo de la tabla
                if type(i)!=np.float64:
                    name_table = (
                        remove_tildes( i.split(":")[1]
                                    .split(",")[0]
                                    .strip())
                                    .split(cultivo)[0] + cultivo
                                    ).lower()
            
            # data de la tabla
            df = data.loc[start+2:start+2+28,:].dropna(axis=1, how="all").reset_index(drop=True)
            df = df.loc[:, df.columns.notna()]

            if df.iloc[-1,0]!="Ucayali":
                df = df[:-1]
            if df.iloc[0,0]=="Región":
                df.columns = df.iloc[0,:]
                df = df.iloc[1:,:]

            # agrega la columna año
            df["year"] = year
            df = df[df["Región"].notna()]
            
            if name_table not in tables:
                tables[name_table] = [df]
            else:
                tables[name_table].append(df)
            
        print("Excel====================", year)


    '''
    Verificando que las tablas que pertenecen a un mismo grupo tengan el mismo numero de columnas
    '''

    dim_check = True
    head_check = True

    for name_table in tables:

        dim = tables[name_table][0].shape
        head = tables[name_table][0].columns.values
        for dataframe in tables[name_table]:

            # cuando estableci las columnas puede que aun se conservaron algunas columnas con nan
            dataframe = dataframe.loc[:, dataframe.columns.notna()]

            if dim == dataframe.shape and all(head==dataframe.columns.values):
                dim = dataframe.shape
                head = dataframe.columns.values
            
            else:
                print("hay al menos una tabla que no coincide con otros años")
                print(dataframe.columns.values)
                dim_check = False
                head_check = False
        

    concat_succes = False

    if dim_check and head_check:
        for name_table in tables :
            tables[name_table] = pd.concat(tables[name_table])
        print("Las columnas son correctas, tablas fueron juntadas")
        concat_succes = True
    else:
        print("no se realizo el cancat, porque una tabla no coincide, analizar")

    '''
    Si el concat fue exitoso, se realiza un pivot en los meses y se crea la columan fecha
    '''

    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']
    mes_map = {
                'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Ago': 8, 'Set': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
            }

    if concat_succes==True:
        for name_table in tables:
            if "mensual" in name_table:
                
                df =  tables[name_table]
                df = pd.melt(df , 
                        id_vars= [col for col in df.columns if col not in meses],
                        value_vars=meses,
                        var_name="meses")

                df['d-m-y'] = "1/"+ df['meses'].map(mes_map).astype(str) +"/"+ df.year.astype(str)
                df.drop(columns=['year', "meses"], inplace=True)
                df = df[["Región","value","d-m-y"]]
                
                ## cambiando llos nombres de las columnas
                for column_name in ["sembrada", "cosechada", "produccion", "precio", "rendimiento"]:
                    if column_name in name_table:
                        df = df.rename(columns={'value': column_name})

                tables[name_table] = df
        print("el concat fue realizado con exito ................")
    else:
        print("concat no realizado ..................")


    """
    se join las tablas, solo se consideran si la fecha esta en todas las tablas
    """

    tables_6 = []
    for name in tables:
        if tables[name].shape[1] == 3:
            tables_6.append(name)

    df = tables[tables_6[0]]
    for name in tables_6[1:]:
        #print(tables[name].columns.values)

        df = df.merge(
            tables[name],
            on=["Región", "d-m-y"],
            how="inner"
        )
    print("tablas join comleted, mensual ...........")

    # palabras clave: sembrada, cosechada, Produccion, Precio
    if save:
        df.to_csv( "./CultivoData/"+cultivo+".csv" ,index=False)
        print("Data guardado:", df.columns.values)
    """
    for name in tables:
        if "precio" in name:
            df.to_csv( "data.csv" ,index=False)
            
    """
    return df

if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--cultivo")
    parser.add_argument("--save", default=False)
    
    save = parser.parse_args().save
    cultivo = parser.parse_args().cultivo

    df = load_cultivo(cultivo, save)