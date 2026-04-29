"""
政策仿真API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.services.simulator import WhatIfSimulator
from app.services.agent.coordinator import AgentCoordinator

router = APIRouter(prefix="/simulation", tags=["政策仿真"])


class SimulationParam(BaseModel):
    indicator_code: str
    simulated_value: float


class SimulationRequest(BaseModel):
    region_code: str
    region_name: str
    report_year: int
    simulation_params: List[SimulationParam]
    user_id: Optional[str] = None
    simulation_name: Optional[str] = None


class PolicyChange(BaseModel):
    indicator_code: str
    change_percent: float


class AgentAnalyzeRequest(BaseModel):
    region_code: str
    region_name: str
    report_year: int
    policy_changes: List[PolicyChange]


@router.post("/what-if")
def simulate_what_if(
    request: SimulationRequest,
    db: Session = Depends(get_db)
):
    """
    What-If仿真计算
    模拟特定指标变化对总分的影响
    """
    simulator = WhatIfSimulator(db)

    params = [
        {"indicator_code": p.indicator_code, "simulated_value": p.simulated_value}
        for p in request.simulation_params
    ]

    result = simulator.simulate(
        region_code=request.region_code,
        region_name=request.region_name,
        report_year=request.report_year,
        simulation_params=params,
        user_id=request.user_id,
        simulation_name=request.simulation_name
    )

    return result


@router.get("/history")
def get_simulation_history(
    region_code: Optional[str] = Query(None, description="行政区划代码"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(20, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取历史仿真记录
    """
    simulator = WhatIfSimulator(db)
    history = simulator.get_simulation_history(
        region_code=region_code,
        user_id=user_id,
        limit=limit
    )

    return {
        "count": len(history),
        "history": history
    }


@router.get("/{simulation_id}")
def get_simulation_detail(
    simulation_id: str,
    db: Session = Depends(get_db)
):
    """
    获取仿真详情
    """
    from app.models.indicator import SimulationLog

    log = db.query(SimulationLog).filter(
        SimulationLog.id == simulation_id
    ).first()

    if not log:
        return {"error": "仿真记录不存在"}

    return {
        "id": str(log.id),
        "region_code": log.region_code,
        "simulation_name": log.simulation_name,
        "params": log.params,
        "original_total_score": log.original_total_score,
        "simulated_total_score": log.simulated_total_score,
        "score_delta": log.score_delta,
        "rank_change": log.rank_change,
        "agent_analysis": log.agent_analysis,
        "created_at": log.created_at.isoformat()
    }


@router.post("/agent-analyze")
def agent_analyze_policy(
    request: AgentAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Agent智能体分析
    使用多智能体框架分析政策变化的影响
    """
    coordinator = AgentCoordinator(db)

    context = {
        "region_code": request.region_code,
        "region_name": request.region_name,
        "report_year": request.report_year,
        "policy_changes": [
            {"indicator_code": p.indicator_code, "change_percent": p.change_percent}
            for p in request.policy_changes
        ]
    }

    result = coordinator.analyze_policy_impact(context)

    return result


@router.get("/agent/full-analysis")
def agent_full_analysis(
    region_code: str = Query(..., description="行政区划代码"),
    report_year: int = Query(..., description="报告年份"),
    db: Session = Depends(get_db)
):
    """
    获取多智能体全维度分析
    """
    coordinator = AgentCoordinator(db)

    context = {
        "region_code": region_code,
        "report_year": report_year
    }

    return coordinator.analyze_all_dimensions(context)
