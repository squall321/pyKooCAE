"""
템플릿 자동 선택 시스템 (Priority 2)

누적 낙하/열응력 시뮬레이션에서 각 Step에 맞는 템플릿을 자동으로 선택합니다.

템플릿 종류 (5개):
    - DROP_FIRST: 첫 번째 낙하
    - DROP_CUMULATIVE: 누적 낙하 (DYNAIN_TO_INITIAL → DROP_ATTITUDE)
    - THERMAL_FIRST: 첫 번째 열해석
    - THERMAL_CUMULATIVE: 누적 열해석 (DYNAIN_TO_INITIAL → THERMAL_CYCLE)
    - THERMAL_TO_DROP: 열→낙하 전환 (DYNAIN_TO_INITIAL(열) → DROP_ATTITUDE)

자동 선택 로직:
    - Step 1: DROP_FIRST 또는 THERMAL_FIRST
    - Step 2+:
        - DROP 모드:
            - 이전이 THERM → THERMAL_TO_DROP
            - 이전이 DROP → DROP_CUMULATIVE
        - THERM 모드:
            - THERMAL_CUMULATIVE
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class SimulationMode(Enum):
    """시뮬레이션 모드"""
    DROP = "DROP"              # 낙하
    IMPACT = "IMPACT"          # 충격 (DropWeightImpactTest)
    THERM = "THERM"            # 열응력
    STAT = "STAT"              # 정적 하중
    VIB = "VIB"                # 진동
    DWI = "DWI"                # 수침
    COMB = "COMB"              # 조합


class TemplateType(Enum):
    """템플릿 타입"""
    DROP_FIRST = "DROP_FIRST"                      # 첫 번째 낙하
    DROP_CUMULATIVE = "DROP_CUMULATIVE"            # 누적 낙하
    IMPACT_FIRST = "IMPACT_FIRST"                  # 첫 번째 충격
    IMPACT_CUMULATIVE = "IMPACT_CUMULATIVE"        # 누적 충격
    THERMAL_FIRST = "THERMAL_FIRST"                # 첫 번째 열해석
    THERMAL_CUMULATIVE = "THERMAL_CUMULATIVE"      # 누적 열해석
    THERMAL_TO_DROP = "THERMAL_TO_DROP"            # 열→낙하 전환


@dataclass
class StepInfo:
    """Step 정보"""
    step_number: int           # Step 번호 (1, 2, 3, ...)
    mode: SimulationMode       # 현재 Step의 모드
    prev_mode: Optional[SimulationMode] = None  # 이전 Step의 모드 (Step 1이면 None)


@dataclass
class TemplateInfo:
    """템플릿 정보"""
    template_type: TemplateType
    description: str
    requires_dynain: bool      # dynain 파일 필요 여부


# 템플릿 정의
TEMPLATE_DEFINITIONS = {
    TemplateType.DROP_FIRST: TemplateInfo(
        template_type=TemplateType.DROP_FIRST,
        description="첫 번째 낙하 (DROP_ATTITUDE 실행, DR 자동 포함)",
        requires_dynain=False
    ),
    TemplateType.DROP_CUMULATIVE: TemplateInfo(
        template_type=TemplateType.DROP_CUMULATIVE,
        description="누적 낙하 (DYNAIN_TO_INITIAL → DROP_ATTITUDE, DR 자동 재추가)",
        requires_dynain=True
    ),
    TemplateType.IMPACT_FIRST: TemplateInfo(
        template_type=TemplateType.IMPACT_FIRST,
        description="첫 번째 충격 (DROP_WEIGHT_IMPACT_TEST 실행)",
        requires_dynain=False
    ),
    TemplateType.IMPACT_CUMULATIVE: TemplateInfo(
        template_type=TemplateType.IMPACT_CUMULATIVE,
        description="누적 충격 (DYNAIN_TO_INITIAL → DROP_WEIGHT_IMPACT_TEST)",
        requires_dynain=True
    ),
    TemplateType.THERMAL_FIRST: TemplateInfo(
        template_type=TemplateType.THERMAL_FIRST,
        description="첫 번째 열해석 (THERMAL_CYCLE 실행)",
        requires_dynain=False
    ),
    TemplateType.THERMAL_CUMULATIVE: TemplateInfo(
        template_type=TemplateType.THERMAL_CUMULATIVE,
        description="누적 열해석 (DYNAIN_TO_INITIAL → THERMAL_CYCLE)",
        requires_dynain=True
    ),
    TemplateType.THERMAL_TO_DROP: TemplateInfo(
        template_type=TemplateType.THERMAL_TO_DROP,
        description="열→낙하 전환 (DYNAIN_TO_INITIAL(열) → DROP_ATTITUDE)",
        requires_dynain=True
    ),
}


def select_template_for_step(
    step: int,
    mode: SimulationMode,
    prev_mode: Optional[SimulationMode] = None
) -> TemplateType:
    """
    Step 번호와 모드에 따라 자동으로 템플릿 선택

    Parameters:
        step: Step 번호 (1, 2, 3, ...)
        mode: 현재 Step의 모드
        prev_mode: 이전 Step의 모드 (Step 1이면 None)

    Returns:
        TemplateType

    Example:
        >>> # 3회 연속 낙하
        >>> select_template_for_step(1, SimulationMode.DROP)
        <TemplateType.DROP_FIRST: 'DROP_FIRST'>
        >>> select_template_for_step(2, SimulationMode.DROP, SimulationMode.DROP)
        <TemplateType.DROP_CUMULATIVE: 'DROP_CUMULATIVE'>
        >>> select_template_for_step(3, SimulationMode.DROP, SimulationMode.DROP)
        <TemplateType.DROP_CUMULATIVE: 'DROP_CUMULATIVE'>

        >>> # 열→낙하
        >>> select_template_for_step(1, SimulationMode.THERM)
        <TemplateType.THERMAL_FIRST: 'THERMAL_FIRST'>
        >>> select_template_for_step(2, SimulationMode.DROP, SimulationMode.THERM)
        <TemplateType.THERMAL_TO_DROP: 'THERMAL_TO_DROP'>

        >>> # 열→열→낙하
        >>> select_template_for_step(1, SimulationMode.THERM)
        <TemplateType.THERMAL_FIRST: 'THERMAL_FIRST'>
        >>> select_template_for_step(2, SimulationMode.THERM, SimulationMode.THERM)
        <TemplateType.THERMAL_CUMULATIVE: 'THERMAL_CUMULATIVE'>
        >>> select_template_for_step(3, SimulationMode.DROP, SimulationMode.THERM)
        <TemplateType.THERMAL_TO_DROP: 'THERMAL_TO_DROP'>
    """
    # Step 1: 첫 번째 Step
    if step == 1:
        if mode == SimulationMode.DROP:
            return TemplateType.DROP_FIRST
        elif mode == SimulationMode.IMPACT:
            return TemplateType.IMPACT_FIRST
        elif mode == SimulationMode.THERM:
            return TemplateType.THERMAL_FIRST
        else:
            raise ValueError(f"Step 1에서 지원하지 않는 모드: {mode}")

    # Step 2+: 누적 Step
    else:
        if prev_mode is None:
            raise ValueError(f"Step {step}에서 prev_mode가 None입니다. 이전 모드를 지정해야 합니다.")

        if mode == SimulationMode.DROP:
            # DROP 모드
            if prev_mode == SimulationMode.THERM:
                # 열→낙하 전환
                return TemplateType.THERMAL_TO_DROP
            else:
                # 낙하→낙하 (누적 낙하)
                return TemplateType.DROP_CUMULATIVE

        elif mode == SimulationMode.IMPACT:
            # IMPACT 모드
            return TemplateType.IMPACT_CUMULATIVE

        elif mode == SimulationMode.THERM:
            # THERM 모드 (항상 누적)
            return TemplateType.THERMAL_CUMULATIVE

        else:
            raise ValueError(f"Step {step}에서 지원하지 않는 모드: {mode}")


def select_template_for_scenario(scenario: List[SimulationMode]) -> List[TemplateType]:
    """
    시나리오 전체에 대해 템플릿 자동 선택

    Parameters:
        scenario: 모드 리스트 (Step 1, 2, 3, ...)

    Returns:
        템플릿 리스트

    Example:
        >>> # 3회 연속 낙하
        >>> scenario = [SimulationMode.DROP, SimulationMode.DROP, SimulationMode.DROP]
        >>> templates = select_template_for_scenario(scenario)
        >>> [t.value for t in templates]
        ['DROP_FIRST', 'DROP_CUMULATIVE', 'DROP_CUMULATIVE']

        >>> # 열→낙하
        >>> scenario = [SimulationMode.THERM, SimulationMode.DROP]
        >>> templates = select_template_for_scenario(scenario)
        >>> [t.value for t in templates]
        ['THERMAL_FIRST', 'THERMAL_TO_DROP']

        >>> # 열→열→낙하
        >>> scenario = [SimulationMode.THERM, SimulationMode.THERM, SimulationMode.DROP]
        >>> templates = select_template_for_scenario(scenario)
        >>> [t.value for t in templates]
        ['THERMAL_FIRST', 'THERMAL_CUMULATIVE', 'THERMAL_TO_DROP']
    """
    if not scenario:
        raise ValueError("시나리오가 비어 있습니다.")

    templates = []
    prev_mode = None

    for step_number, mode in enumerate(scenario, start=1):
        template = select_template_for_step(step_number, mode, prev_mode)
        templates.append(template)
        prev_mode = mode

    return templates


def get_template_info(template_type: TemplateType) -> TemplateInfo:
    """
    템플릿 정보 조회

    Parameters:
        template_type: TemplateType

    Returns:
        TemplateInfo
    """
    return TEMPLATE_DEFINITIONS[template_type]


def print_template_summary(scenario: List[SimulationMode]):
    """
    시나리오 템플릿 요약 출력 (디버깅용)

    Parameters:
        scenario: 모드 리스트
    """
    templates = select_template_for_scenario(scenario)

    print(f"\n{'='*100}")
    print(f"시나리오 템플릿 자동 선택 결과")
    print(f"총 Step 수: {len(scenario)}")
    print(f"{'='*100}\n")

    print(f"{'Step':<6} {'Mode':<10} {'Template':<25} {'Dynain':<10} {'Description':<40}")
    print(f"{'-'*100}")

    for i, (mode, template) in enumerate(zip(scenario, templates), start=1):
        info = get_template_info(template)
        dynain_required = "Required" if info.requires_dynain else "Not Needed"
        print(f"{i:<6} {mode.value:<10} {template.value:<25} {dynain_required:<10} {info.description:<40}")

    print(f"{'-'*100}\n")


# 테스트 코드
if __name__ == "__main__":
    print("\n" + "="*100)
    print("템플릿 자동 선택 시스템 테스트")
    print("="*100)

    # 테스트 1: 3회 연속 낙하
    print("\n테스트 1: 3회 연속 낙하")
    scenario1 = [SimulationMode.DROP, SimulationMode.DROP, SimulationMode.DROP]
    print_template_summary(scenario1)

    # 테스트 2: 열→낙하
    print("\n테스트 2: 열→낙하")
    scenario2 = [SimulationMode.THERM, SimulationMode.DROP]
    print_template_summary(scenario2)

    # 테스트 3: 열→열→낙하
    print("\n테스트 3: 열→열→낙하")
    scenario3 = [SimulationMode.THERM, SimulationMode.THERM, SimulationMode.DROP]
    print_template_summary(scenario3)

    # 테스트 4: 낙하→열→낙하
    print("\n테스트 4: 낙하→열→낙하")
    scenario4 = [SimulationMode.DROP, SimulationMode.THERM, SimulationMode.DROP]
    print_template_summary(scenario4)

    # 테스트 5: 복잡한 시나리오 (낙하→낙하→열→낙하→낙하)
    print("\n테스트 5: 복잡한 시나리오 (낙하→낙하→열→낙하→낙하)")
    scenario5 = [
        SimulationMode.DROP,
        SimulationMode.DROP,
        SimulationMode.THERM,
        SimulationMode.DROP,
        SimulationMode.DROP
    ]
    print_template_summary(scenario5)

    print("\n" + "="*100)
    print("모든 테스트 완료!")
    print("="*100 + "\n")
