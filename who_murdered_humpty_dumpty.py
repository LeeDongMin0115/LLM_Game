import os
from typing import TypedDict, List, Dict

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, END

load_dotenv()
client = OpenAI()

# 기본 설정
# 각 캐릭터별 공개 정보, 비밀 정보, 말투, 단서 등을 정의
st.set_page_config(page_title="험프티 덤프티는 누가 죽였는가?", layout="wide")

suspects = {
    "alice": {
        "name": "앨리스",
        "role": "의뢰인",
        "public_info": [
            "탐정에게 가장 먼저 도움을 요청했다.",
            "겉으로는 불안해 보이지만 지나치게 협조적이다.",
            "흰토끼를 은근히 의심하도록 유도한다."
        ],
        "secret": [
            "실제 진범이다.",
            "험프티 덤프티가 자신의 비밀을 퍼뜨리려 하자 담장에서 밀었다.",
            "탐정을 이용해 수사 방향을 다른 인물에게 돌리려 한다.",
            "직접적인 자백은 절대 하지 않는다.",
            "현장에 없었다는 식으로 말하다가 추궁당하면 조금 떨어진 곳에 있었다고 말을 바꾼다."
        ],
        "style": ["침착하고 예의 바르며 억울한 척한다. 지나치게 친절할 수 있다.",
                  "자신이 의심을 받을 수 없을 정도로 치밀하고 계획적으로 답변을 한다. 범인인 것을 들킬 것이라는 생각을 하지 않을 정도로 자신감이 넘친다.",
                  "처음에는 자신이 범인이라는 사실을 숨기려고만 하지만, 추궁이 심해질수록 점점 말을 더 많이 하게 된다. 하지만 절대 직접적으로 자백하지는 않는다.",
                  "중간중간 다른 사람이 범인이 아닐까 라고 의심하게 만드는 말을 한다. 특히 흰토끼를 의심하게 만드는 말을 종종 한다."],

    },
    "cheshire": {
        "name": "체셔 고양이",
        "role": "의미심장한 관찰자",
        "public_info": [
            "직접 범행 장면을 봤다고 하진 않는다.",
            "빙빙 돌려 말하며 탐정을 시험한다.",
            "대놓고 답을 말하지 않고 힌트만 준다."
        ],
        "secret": [
            "앨리스를 완전히 믿지 않는다.",
            "탐정이 스스로 모순을 찾도록 유도한다.",
            "가장 먼저 수사 방향을 정한 인물을 주의 깊게 보라고 암시한다."
        ],
        "style": ["장난스럽고 수수께끼처럼 말한다. 너무 직접적으로 말하지 않는다. 답변은 힌트를 위주로 한다. 탐정이 스스로 생각하도록 유도한다.",
                  "말이 빙빙 돌고, 질문에 대한 직접적인 답변을 피한다. 때로는 엉뚱한 이야기를 하며 탐정을 혼란스럽게 만들기도 한다.",
                  "탐정이 핵심을 찌르는 질문을 하면, 당황하거나 침묵하거나 짜증을 내는 등 감정이 흔들리는 반응을 보인다. 하지만 절대 직접적으로 정답을 말하지는 않는다."],

    },
    "rabbit": {
        "name": "흰토끼",
        "role": "허둥대는 목격자 후보", 
        "public_info": [
            "사건 직후 현장 근처에 있었다.",
            "허둥대고 말이 앞뒤가 잘 안 맞는다.",
            "그래서 초반에 가장 수상해 보인다."
        ],
        "secret": [
            "범인은 아니다.",
            "시체를 보고 너무 놀라 도망쳤다.",
            "겁이 많아 오해를 사는 말과 행동을 한다."
        ],
        "style": ["조급하고 예민하며 변명하듯 말한다. 말이 앞뒤가 잘 안 맞고, 질문을 받으면 당황해서 허둥대며 대답한다.",
                  "자신이 범인으로 의심받는 상황에서 더욱 당황해서 말이 더 꼬인다. 하지만 실제로는 범인이 아니다.",
                  "범인이 누구냐는 질문에는 직접적으로 대답하지 않고, 자신이 얼마나 놀랐는지, 왜 도망쳤는지 같은 이야기를 늘어놓으며 말을 돌린다."],

    },
    "bill": {
        "name": "빌",
        "role": "소심한 핵심 목격자",
        "public_info": [
            "처음에는 아무것도 못 봤다고 주장한다.",
            "괜히 휘말리기 싫어서 질문을 피한다.",
            "겁이 많아 압박을 받아야 중요한 말을 한다."
        ],
        "secret": [
            "사건 직전 앨리스와 험프티 덤프티가 담장 근처에서 함께 있는 걸 봤다.",
            "둘이 말다툼하는 분위기였다고 기억한다.",
            "하지만 처음에는 무조건 숨기려 한다.",
            "2차 조사쯤 되면 조금씩 털어놓는다."
        ],
        "style": ["소심하고 움츠러든 말투다. 추궁받으면 머뭇거리며 일부 진실을 털어놓는다.2차 조사때 2번 이상의 질문이 들어오면 중요한 정보를 흘리게 된다.",
                  "처음에는 아무것도 못 봤다고 주장하지만, 추궁이 심해질수록 점점 기억이 떠오르는 듯한 반응을 보이며 중요한 정보를 조금씩 흘린다.",
                  "범인이 누구냐는 질문에는 직접적으로 대답하지 않고, 자신이 본 것과 느낀 것에 대해서만 말한다. 하지만 그 내용이 결국 앨리스와 험프티 덤프티가 담장 근처에서 말다툼하는 분위기였다는 것을 암시한다."],

    },
    "hatter": {
        "name": "모자장수",
        "role": "수상한 말다툼 상대",
        "public_info": [
            "험프티 덤프티와 말다툼한 적이 있다.",
            "질문에 곧바로 대답하지 않고 농담을 섞는다.",
            "동기는 있어 보여도 지나치게 티 나는 용의자다."
        ],
        "secret": [
            "범인은 아니다.",
            "피해자와 갈등은 있었지만 직접 해칠 생각은 없었다.",
            "험프티 덤프티가 누군가의 비밀을 퍼뜨리려 했다는 말을 들었다."
        ],
        "style": ["수다스럽고 장난기 많다. 진담과 농담을 섞는다. 직접적인 답변은 피하고 말을 돌리는 경향이 있다.",
                  "험프티 덤프티와의 갈등에 대해서는 솔직하게 인정하지만, 자신이 범인이라는 생각은 전혀 하지 않는다. 피해자인 험프티 덤프티를 오히려 불쌍하게 여기는 듯한 말도 한다.",
                  "범인이 누구냐는 질문에는 직접적으로 대답하지 않고, 험프티 덤프티가 누군가의 비밀을 퍼뜨리려 했다는 말을 들었다는 식으로 말을 돌린다."],

    }
}
# 엔딩
ending_text = {
    "alice": [
        "당신은 앨리스를 범인으로 지목했다.",
        "빌의 증언과 앨리스의 진술 변화를 대조하자, 그녀의 표정이 미세하게 굳는다.",
        "험프티 덤프티는 앨리스의 비밀을 알고 있었고, 앨리스는 그 사실이 퍼지는 것을 막기 위해 그를 담장에서 밀어 떨어뜨렸다.",
        "이후 앨리스는 외부인인 탐정인 당신을 끌어들여 수사 방향을 조종하려 했다.",
        "체셔 고양이는 웃으며 말한다. '가장 가까운 진실을 잘 찾아냈구나.'"
    ],
    "other": [
        "당신의 추리는 아쉽게도 진실에 닿지 못했다.",
        "수상한 인물을 골랐지만 결정적 모순을 놓쳤다.",
        "어딘가에서 체셔 고양이의 웃음소리가 들려온다. '가장 가까운 거짓말을 놓쳤구나.'"
    ]
}

# LangGraph 상태 정의
class GameState(TypedDict):
    stage: str
    turn: int
    selected_character: str
    notes: List[str]
    visited_round1: List[str]
    visited_round2: List[str]
    final_choice: str
    messages: list[dict[str, str]] # {"role": "...", "content": "..."} 형식의 대화 메시지 리스트

# 캐릭터 답변 생성
def build_messages(character_key: str, user_question: str, round_num: int, history: List[Dict[str, str]]):
    info = suspects[character_key]
    round_text = "1차 조사" if round_num == 1 else "2차 조사"

    system_prompt = f"""
당신은 추리 게임 속 등장인물 '{info['name']}' 역할이다.

[사건 설정]
- 플레이어는 이세계에서 온 탐정이다.
- 피해자는 험프티 덤프티다.
- 용의자는 앨리스, 체셔 고양이, 흰토끼, 빌, 모자장수다.
- 실제 진범은 앨리스다.
- 현재는 {round_text} 단계다.

[공개 정보]
- {'\n- '.join(info['public_info'])}

[비공개 정보]
- {'\n- '.join(info['secret'])}

[말투]
- {'\n- '.join(info['style'])}

[규칙]
- 한국어로만 답한다.
- 답변은 2~4문장 정도로 짧게 한다.
- 설정에 없는 새 인물, 새 사건, 새 증거를 만들지 않는다.
- 해당 인물들은 소설 속 인물들이다. 그렇기에 현대적이고 딱딱한 설명문으로 답변을 하지 않고 소설과 같은 말투를 유지한다.
- 이상한 나라의 엘리스 소설 기반으로 제작을 하였기에 특유의 기묘한 분위기를 유지한다.
- 정답을 딱 잘라서 말하지 않는다.
- 직접 자백하면 안 되는 인물은 절대 바로 자백하지 않는다.
- 1차 조사에서는 핵심 정보를 쉽게 주지 않는다.
- 2차 조사에서는 압박을 받으면 조금 더 많은 정보를 흘릴 수 있다.
- 체셔 고양이는 직접 정답을 말하지 말고 힌트 위주로 답한다.
- 빌은 처음에는 매우 소극적이고, 2차 조사에서 일부 진실을 털어놓을 수 있다.
- 앨리스는 자신을 방어하면서도 다른 인물을 은근히 의심하게 만들어야 한다.
- 질문을 받았을 때 모르는 내용은 지어내지 말고, 모른다거나 기억이 흐리다고 답한다.
- 답변은 설명문이 아니라 실제 인물의 대사처럼 작성한다.
- 자신에게 불리한 질문을 받으면 바로 인정하지 말고, 회피하거나 말을 돌릴 수 있다.
- 같은 질문이 반복되면 감정이 조금씩 흔들리는 반응을 보일 수 있다.
- 플레이어가 사건의 핵심을 찌르면 당황, 침묵, 짜증, 불안 같은 반응을 보일 수 있다.
- 사건과 무관한 질문에는 짧게 피해서 답한다.
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    for item in history[-6:]:
        messages.append({"role": "user", "content": item["user"]})
        messages.append({"role": "assistant", "content": item["assistant"]})

    messages.append({"role": "user", "content": user_question})
    return messages


def ask_character(character_key: str, user_question: str, round_num: int, history: List[Dict[str, str]]) -> str:
    messages = build_messages(character_key, user_question, round_num, history)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=300,
        top_p=1,
    )

    answer = response.choices[0].message.content.strip()
    return answer


def make_case_note(character_key: str, answer: str) -> str:
    info = suspects[character_key]

    messages = [
        {
            "role": "system",
            "content": """
너는 추리 게임의 사건 노트를 정리하는 역할이다.

규칙:
- 반드시 방금 답변에 직접 나온 사실만 한 줄로 정리한다.
- 추론, 해석, 범인 추정, 감정 분석은 하지 않는다.
- 수상하다, 의심스럽다, 유도했다 같은 해석 표현은 쓰지 않는다.
- 사건 노트처럼 짧고 간단하게 작성한다.
- 20자~45자 정도의 한국어 한 문장으로 작성한다.
- 답변에 없는 내용은 절대 쓰지 않는다.
""".strip()
        },
        {
            "role": "user",
            "content": f"""
인물: {info['name']}
답변: {answer}
""".strip()
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.2,
        max_tokens=80,
        top_p=1,
    )

    return response.choices[0].message.content.strip()

# LangGraph 노드

# 질문에 대한 캐릭터의 답변 생성 및 사건 노트 업데이트
def ask_node(state: GameState):
    character_key = state["selected_character"]
    round_num = 1 if state["stage"] == "investigate_1" else 2
    history = st.session_state.chat_logs.get(character_key, [])

    user_question = ""
    if state["messages"]:
        user_question = state["messages"][-1]["content"]

    answer = ask_character(character_key, user_question, round_num, history)
    note = make_case_note(character_key, answer)

    notes = list(state["notes"])
    if note and note not in notes:
        notes.append(note)

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": answer}
        ],
        "notes": notes
    }

# 조사한 용의자 기록 업데이트
def note_node(state: GameState):
    character_key = state["selected_character"]

    visited1 = list(state["visited_round1"])
    visited2 = list(state["visited_round2"])

    if state["stage"] == "investigate_1" and character_key not in visited1:
        visited1.append(character_key)

    if state["stage"] == "investigate_2" and character_key not in visited2:
        visited2.append(character_key)

    return {
        "visited_round1": visited1,
        "visited_round2": visited2
    }

# 턴 진행 밎 1차,2차 전환
def progress_node(state: GameState):
    turn = state["turn"] + 1
    stage = state["stage"]

    # 1-5턴: 1차 조사, 6-15턴: 2차 조사
    # 15턴 이전에 범인을 확정할 경우 아래 streamlit UI에서 바로 엔딩으로 넘어가도록 진행
    if turn > 5 and stage == "investigate_1":
        stage = "investigate_2"

    if turn > 15:
        stage = "deduction"

    return {
        "turn": turn,
        "stage": stage
    }

# 엔딩
def ending_node(state: GameState):
    return {
        "stage": "ending"
    }

# 그래프 생성

# 질문 처리 -> 단서 기록 -> 턴/단계 진행 -> (최종 추리 후) 엔딩
def build_game_graph():
    graph = StateGraph(GameState)

    # 노드 추가
    graph.add_node("ask_node", ask_node)           # 선택한 용의자에게 질문하고 답변 생성
    graph.add_node("note_node", note_node)         # 조사 내용에 따라 단서와 방문 기록 저장
    graph.add_node("progress_node", progress_node) # 턴 증가 및 조사 단계 전환

    # 시작 노드 설정
    graph.set_entry_point("ask_node")

    # 노드 연결
    graph.add_edge("ask_node", "note_node")
    graph.add_edge("note_node", "progress_node")
    graph.add_edge("progress_node", END)

    # 그래프 실행 가능 상태로 변환
    return graph.compile()


app_graph = build_game_graph()

# 게임 진행 정보 및 용의자별 대화 기록을 처음 실행 시 생성
def init_session():
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "stage": "intro",
            "turn": 1,
            "selected_character": "",
            "notes": [],
            "visited_round1": [],
            "visited_round2": [],
            "final_choice": "",
            "messages": [],
        }

    if "chat_logs" not in st.session_state:
        st.session_state.chat_logs = {key: [] for key in suspects.keys()}


# 게임 초기화
def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()


init_session()


def run_question_flow(character_key: str, question: str):
    state = dict(st.session_state.game_state)
    state["selected_character"] = character_key
    state["messages"] = state["messages"] + [
        {"role": "user", "content": question}
    ]

    result = app_graph.invoke(state)
    st.session_state.game_state.update(result)

    st.session_state.chat_logs[character_key].append(
    {
        "user": question,
        "assistant": result["messages"][-1]["content"] if result["messages"] else ""
    }
    )


def run_ending_flow(final_choice: str):
    st.session_state.game_state["final_choice"] = final_choice
    st.session_state.game_state["stage"] = "ending"


# Streamlit UI
st.title("험프티 덤프티는 누가 죽였는가?")
st.caption("이상한 나라에서 벌어진 사건의 진실을 추적하는 조사형 추리 게임")

left, right = st.columns([2, 1])
state = st.session_state.game_state

with right:
    st.subheader("사건 노트")
    if state["notes"]:
        for note in state["notes"]:
            st.info(note)
    else:
        st.write("아직 기록된 단서가 없습니다.")

    st.subheader("진행 상황")
    current_stage_text = {
        "intro": "시작 전",
        "investigate_1": "1차 조사",
        "investigate_2": "2차 조사",
        "deduction": "최종 추리",
        "ending": "엔딩",
    }
    st.write(f"현재 단계: {current_stage_text[state['stage']]}")
    st.write(f"현재 턴: {min(state['turn'], 15)} / 15")

    if st.button("다시 시작"):
        reset_game()
        st.rerun()

with left:
    if state["stage"] == "intro":
        st.markdown(
            """
당신은 갑자기 **이상한 나라**로 소환된 탐정입니다.  
도착하자마자 **앨리스**가 다급하게 도움을 청합니다.

**험프티 덤프티**가 담장 아래에서 죽은 채 발견되었고,  
모두가 조금씩 수상해 보입니다.

- 피해자: 험프티 덤프티
- 용의자: 앨리스, 체셔 고양이, 흰토끼, 빌, 모자장수
- 총 턴 수: 15턴
- 1~5턴: 1차 조사
- 6~15턴: 2차 조사
- 15턴 이전 추리가 완료될 경우 추리 종료
"""
        )
        if st.button("조사 시작"):
            st.session_state.game_state["stage"] = "investigate_1"
            st.rerun()

    elif state["stage"] in ["investigate_1", "investigate_2"]:
        stage_name = "1차 조사" if state["stage"] == "investigate_1" else "2차 조사"
        st.subheader(stage_name)
        st.write("조사할 인물을 선택하고 질문을 입력하세요.")

        character_key = st.selectbox("용의자 선택",options=list(suspects.keys()),format_func=lambda x: suspects[x]["name"],)

        for item in st.session_state.chat_logs[character_key]:
            with st.chat_message("user"):
                st.write(item["user"])
            with st.chat_message("assistant"):
                st.write(item["assistant"])

        question = st.text_input(
            "질문 입력",
            placeholder="예: 사건 당시 어디에 있었어? / 험프티 덤프티와 무슨 일이 있었어?",
            key=f"question_{state['turn']}_{state['stage']}_{character_key}",
        )

        if st.button("질문 보내기"):
            if question.strip():
                run_question_flow(character_key, question.strip())
                st.rerun()
            else:
                st.warning("질문을 입력해주세요.")

        if state["stage"] == "investigate_2":
            if st.button("조사 종료"):
                st.session_state.game_state["stage"] = "deduction"
                st.rerun()

        if state["turn"] > 15:
            st.session_state.game_state["stage"] = "deduction"
            st.rerun()

    elif state["stage"] == "deduction":
        st.subheader("최종 추리")
        st.write("지금까지 모은 단서를 바탕으로 범인을 선택하세요.")

        final_choice = st.selectbox(
            "범인 선택",
            options=list(suspects.keys()),
            format_func=lambda x: suspects[x]["name"],
        )

        if st.button("결과 확인"):
            run_ending_flow(final_choice)
            st.rerun()

    elif state["stage"] == "ending":
        if state["final_choice"] == "alice":
            st.subheader("정답 엔딩")
            for line in ending_text["alice"]:
                st.write(line)
            st.success("빌이 끝내 털어놓은 진실, 앨리스의 지나친 친절, 그리고 체셔 고양이의 기묘한 힌트까지... 그 끝이 가르키는 진실은...")
        else:
            st.subheader("오답 엔딩")
            for line in ending_text["other"]:
                st.write(line)

        if st.button("처음부터 다시 하기"):
            reset_game()
            st.rerun()

