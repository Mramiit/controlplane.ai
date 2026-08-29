from fastapi import Header, HTTPException

def get_scenario(x_use_case: str = Header(default="scenario_a_support")) -> str:
    valid_scenarios = ["scenario_a_support", "scenario_b_internal", "scenario_c_finance"]
    if x_use_case not in valid_scenarios:
        raise HTTPException(status_code=400, detail="Invalid X-Use-Case header")
    return x_use_case