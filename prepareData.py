import pandas as pd
def prepareData(df, filename): 
    listFormat = """
    1. PointOne
    2. PointTwo
    ...
    10. FinalPoint

    Example: 
    1. Survival was strongly correlated with social class ($\text{Pclass}$), indicating that passengers in higher-class accommodations had a statistically significant advantage in survival rates.
    2. The financial standing of the passenger, reflected by the ticket fare ($\text{Fare}$), was a significant predictor of survival, demonstrating that economic status was a critical factor in the outcome of the event.
    3. There is a strong inverse relationship between passenger class and fare ($\text{Pclass}$ vs $\text{Fare}$ correlation of -0.577), confirming the rigid stratification of wealth across the passenger manifest.
    4. While age ($\text{Age}$) showed a weak linear correlation with survival, the interaction between class, fare, and age suggests that socio-economic status provided a much stronger predictive power for survival than individual age alone.
    5. The data reveals a clear pattern of inequality, where class and the price paid were deeply intertwined with the probability of survival, highlighting systemic disadvantages based on social standing.

    """
    stats = []
    for col in df.columns:
        #print(col)
        if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
            mins = df[col].min()
            maxs = df[col].max()
            quantiles = df[col].quantile([0.25, 0.5, 0.75])
            q1, q2, q3 = quantiles[0.25], quantiles[0.5], quantiles[0.75]
        else: 
            mins = "N/A"
            maxs = "N/A"
            q3 = "N/A"
            q2 = "N/A"
            q1 = "N/A"
        stats.append({"nameCol": col, "min" : mins, "max" : maxs,"q3": q3,"q2": q2, "q1":q1})
    filterCols = [col for col in df.columns if corrMatrixFilter(df[col], df)]
    corr_matrix = df[filterCols].corr(numeric_only=True)
    samples = df.sample(25)

    DataFormatPrompt = f""" 
    You are a BUSSINES INTELIGENCE agent. 
    Analyze the following file:  {filename}, with the task of searching meaningfull insights. 
    Everything is sorted per section. 
    ##Data name and type
    Column names: 
    ##Data distributions
    min: 
    max, q1, q2 ,q3
    {stats}
    ##Correlations between data
    corr_matrix: {corr_matrix}
    ## 25 Data samples: 
    {samples}

    Return your top 5 Findings using this format: 
    {listFormat}. 
    Do not add extra comments before and after the five points.
    """
    #print(DataFormatPrompt)
    return DataFormatPrompt

#Diabolic filter to check if the variable makes senses in a corr_matrix. 
def corrMatrixFilter(series, df): 
    if not pd.api.types.is_numeric_dtype(series): 
        return False
    if series.nunique() == len(df): 
        return False
    nameLowerCase = series.name.lower()
    #Modify and append more names of cols to filter if they mean nothing
    #Humanity counts on this in order to generate a propper chart
    filterOfEternalDoom = ["id", "code", "key", "index", "num", "no"]
    if any(nameLowerCase == s or nameLowerCase.endswith(s) for s in filterOfEternalDoom):
        return False
    return True



def prepareInsightsData(df, insights): 
    columnNames = df.columns.tolist()
    jsonFormat =  """
    EXAMPLE OUTPUT - follow this exactly:
    {
        "Charts": [
            {
                "chartName": "Sales by Region",
                "chartType": "Vertical Bar Chart"
                "metrics": { "field1": "region", "field2": "sales" },
                "metricsFilter": {"sales" : "Max"}
            }, 
            {
                "chartName": "Avg age by country by sex",
                "chartType": "Stacked Bar"
                "metrics": { "field1": "country", "field2": "age", "field3" : "sex" },
                "metricsFilter": {"age" : "Avg"} 
            }
        ]
    }
    """
    #toDo: Consider adding instructions of when using which chart. 
    chartsGeneratingPrompt = f"""
    Your task is to think about the 5 usefull charts to visualize from the following insights {insights}
    and return them in a Json format STRICTLY and with NO CHANGE: {jsonFormat}, no extra comments using 
    the following variable names {columnNames}

    Each chart must be stricly one of the following types and be returned: 
    a) Tile: A single KPI, write only a single field in fields. 
    b) Vertical Bar Chart: default
    c) Horizontal Bar Chart: default
    d) Stacked Bar Chart: Three fields as in example
    e) Line, write only two fields in fields to compare
    f) Pie, default
    g) Donut, default
    h) Scatter, write only two fields in fields to compare
    i) Area, Three fields as in example for Stacked Bar

    Filters can be: Max, Min, Avg, Sum. 

    Review your response and remeber to strictly follow the format {jsonFormat}
    fields must be exactly the name of the var and filter the way you consider to handle that data. 
    CRITICAL: The variable names in fields must be EXACTLY as they appear in this list, 
    character by character, case sensitive: {columnNames}
    Do not paraphrase, translate, or rename them under any circumstances.

    Do one area chart, please. 
    """
    return chartsGeneratingPrompt

#insights = """
#1. Survival was strongly correlated with social class ($\text{Pclass}$), indicating that passengers in higher-class accommodations had a statistically significant advantage in survival rates.
#2. The financial standing of the passenger, reflected by the ticket fare ($\text{Fare}$), was a significant predictor of survival, demonstrating that economic status was a critical factor in the outcome of the event.
#3. There is a strong inverse relationship between passenger class and fare ($\text{Pclass}$ vs $\text{Fare}$ correlation of -0.577), confirming the rigid stratification of wealth across the passenger manifest.
#4. While age ($\text{Age}$) showed a weak linear correlation with survival, the interaction between class, fare, and age suggests that socio-economic status provided a much stronger predictive power for survival than individual age alone.
#5. The data reveals a clear pattern of inequality, where class and the price paid were deeply intertwined with the probability of survival, highlighting systemic disadvantages based on social standing.
#"""

