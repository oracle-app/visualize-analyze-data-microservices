import pandas as pd
#File with all the necesary functions to translate the proposed data to the necesary info for Koala Plot
#Requirements per chart: 
#    a) Tile: Whatever it is. 
#    b) Vertical Bar Chart: List<Str: Float> //May be worth considering remove one of this
#    c) Horizontal Bar Chart: List<Str: Float> //May be worth considering remove one of this
#    d) Stacked Bar Chart: List<Str: List<Float>>  
#    e) Line: List<Float : Float>
#    f) Pie: List<Float>
#    g) Donut: List<Float>
#    h) Scatter: List<Float : Float>
#    i) Area: List<Float : List<Float>>
"""
{  
    "Charts": [
        {
            "chartName": "Survival Rate by Class",
            "chartType": "Vertical Bar Chart",
            "data": {
                "field1": [1, 2, 3],
                "field2": [45, 33, 22]
            }
        }
    ]
}
"""

def dataQuery(formatedData: str, df): 
    map = {"Max": "max", "Min": "min", "Avg" : "mean", "Sum": "sum", "Count": "count"}
    chartType = formatedData["chartType"]
    metrics = formatedData["metrics"]
    filters = formatedData["metricsFilter"] or {}
    category = metrics.get("field1")
    value = metrics.get("field2")
    agg = map.get(filters.get(value, "Count"), "count")
    if agg in ["mean", "sum", "max", "min"] and not pd.api.types.is_numeric_dtype(df[value]):
        agg = "count"
    if not category or not value:
        return {
            "chartName": formatedData.get("chartName", "Unknown"),
            "chartType": chartType,
            "error": "Missing required fields",
            "data": {}
        }
    if category not in df.columns or value not in df.columns:
        return {
            "chartName": formatedData.get("chartName", "Unknown"),
            "chartType": chartType,
            "error": f"Column not found in dataset",
            "data": {}
        }
    type1 = ["Vertical Bar Chart", "Horizontal Bar Chart"]
    type2 = ["Line", "Scatter"]
    type3 = ["Pie","Donut"]
    type4 = ["Area"]
    type5 = ["Stacked Bar Chart"]
  
    if chartType in type1:  # Vertical/Horizontal Bar
        result = df.groupby(category)[value].agg(agg).reset_index()
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "field1": result[category].tolist(),
                "field2": result[value].tolist()
            }
        }

    elif chartType in type2:  # Line/Scatter
        result = df[[category, value]].dropna()
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "field1": result[category].tolist(),
                "field2": result[value].tolist()
            }
        }

    elif chartType in type3:  # Pie/Donut
        result = df.groupby(category)[value].agg(agg).reset_index()
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "field1": result[category].tolist(),
                "field2": result[value].tolist()
            }
        }


    elif chartType == "Tile":
        agg_func = getattr(df[value], agg)
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "value": agg_func()
            }
        }
    elif chartType in type4:  # Area
        field3 = metrics.get("field3")
        if field3:
            result = df.groupby([category, value])[field3].agg(agg).unstack(fill_value=0)
            return {
                "chartName": formatedData["chartName"],
                "chartType": chartType,
                "fieldNames" : metrics,
                "data": {
                    "field1": result.index.tolist(),
                    "field2": {
                        str(col): result[col].tolist() for col in result.columns
                    }
                }
            }
        # Counter-measure if no field3 
        result = df.groupby(category)[value].agg(agg).reset_index()
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "field1": result[category].tolist(),
                "field2": result[value].tolist()
            }
        }
    elif chartType in type5:  # Stacked Bar
        field3 = metrics.get("field3")
        if field3:
            result = df.groupby([category, value])[field3].agg(agg).unstack(fill_value=0)
            return {
                "chartName": formatedData["chartName"],
                "chartType": chartType,
                "fieldNames" : metrics,
                "data": {
                    "field1": result.index.tolist(),
                    "field2": {
                        str(col): result[col].tolist() for col in result.columns
                    }
                }
            }
        # Counter-measure if no field3 
        result = df.groupby(category)[value].agg(agg).reset_index()
        return {
            "chartName": formatedData["chartName"],
            "chartType": chartType,
            "fieldNames" : metrics,
            "data": {
                "field1": result[category].tolist(),
                "field2": result[value].tolist()
            }
        }


    return {}