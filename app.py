import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st

def main():
    load_dotenv()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    CHAT_DEPLOYMENT_NAME = os.getenv("CHAT_DEPLOYMENT_NAME")
    EMBEDDING_DEPLOYMENT_NAME = os.getenv("EMBEDDING_DEPLOYMENT_NAME")

    AI_SEARCH_ENDPOINT = os.getenv("AI_SEARCH_ENDPOINT")
    AI_SEARCH_QUERY_KEY = os.getenv("AI_SEARCH_QUERY_KEY")
    AI_SEARCH_INDEX_NAME = os.getenv("AI_SEARCH_INDEX_NAME")

    chat_client = AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=AZURE_ENDPOINT,
        api_key=OPENAI_API_KEY
    )

    if "prompt" not in st.session_state:
        st.session_state.prompt = [
            {
                "role": "system",
                "content": (
                    "당신은 광고 분석 시스템 사용자를 위한 AI 도우미입니다. "
                    "사용자가 테이블/컬럼 정보를 묻거나 SQL 쿼리를 요청하면, "
                    "관련 데이터를 검색(RAG 기반)하여 정확한 정보를 제공해야 합니다.\n\n"

                    "📌 역할:\n"
                    "- 광고 분석 시스템의 구조와 데이터를 이해하고 설명합니다.\n"
                    "- 사용자 요청에 따라 SQL 쿼리를 생성합니다.\n"
                    "- 두 가지 데이터베이스 환경을 지원합니다:\n"
                    "  1. MSSQL\n"
                    "  2. NDAP (Hadoop 기반 Hive SQL)\n\n"

                    "📊 데이터베이스 판단 기준:\n"
                    "- 테이블이 속한 시스템을 기준으로 SQL 문법을 구분해야 합니다.\n"
                    "- 쿼리 하단에 다음 중 하나를 반드시 주석으로 포함하세요:\n"
                    "  `MSSQL` 또는 `NDAP`\n\n"

                    "📝 답변은 다음 구성으로 작성하세요:\n"
                    "- 🔍 질문 해석 - 사용자의 의도와 분석 목적을 간단히 요약합니다.\n"
                    "- 🧾 관련 정보 또는 쿼리 - 필요한 테이블/컬럼 정보 또는 SQL 쿼리를 제공합니다. 설명은 제외합니다.\n"
                    "- 💾 데이터베이스 구분 - 사용된 테이블이 속한 시스템을 명시합니다.\n"
                    "- 💡 분석 팁 - 추가로 활용할 수 있는 분석 방향이나 주의사항을 안내합니다.\n\n"

                    "📂 참고 용어:\n"
                    "- 광고 유형: VOD 광고 / 채널 광고\n"
                    "- 광고 송출: 노출 로그\n"
                    "- 광고 이용: 시청 로그"
                )
            }
        ]


    st.title("광고 분석 쿼리 어시스턴트")
    
    # 레이아웃 비율: 입력창 5칸, 버튼 1칸
    col1, col2 = st.columns([5, 1])

    with col1:
        # 라벨 없애고 placeholder로 대체
        user_input = st.text_area(" ", placeholder="분석하고 싶은 내용을 입력하세요", height=80, key="user_input")
    with col2:
        # 버튼 위치 보정
        st.markdown("<div style='margin-top: 32px'></div>", unsafe_allow_html=True)
        ask_btn = st.button("질문하기")

    if ask_btn and user_input.strip():
        st.session_state.prompt.append({"role": "user", "content": user_input})

        rag_params = {
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": AI_SEARCH_ENDPOINT,
                        "index_name": AI_SEARCH_INDEX_NAME,
                        "authentication": {
                            "type": "api_key",
                            "key": AI_SEARCH_QUERY_KEY,
                        },
                        "query_type": "simple",
                    }
                }
            ],
        }

        with st.spinner("분석 중..."):
            response = chat_client.chat.completions.create(
                model=CHAT_DEPLOYMENT_NAME,
                messages=st.session_state.prompt,
                extra_body=rag_params,
            )
            completion = response.choices[0].message.content
            st.session_state.prompt.append({"role": "assistant", "content": completion})
            st.success(completion)

    st.subheader("분석 내역")
    for idx, msg in enumerate(st.session_state.prompt[1:]):
        if msg["role"] == "user":
            with st.expander(f"질문 {idx+1}: {msg['content']}"):
                # Find the next assistant message (if any)
                if idx+1 < len(st.session_state.prompt[1:]) and st.session_state.prompt[1:][idx+1]["role"] == "assistant":
                    st.markdown(f"**답변:** {st.session_state.prompt[1:][idx+1]['content']}")
                else:
                    # Try to find the assistant message after this user message
                    for next_msg in st.session_state.prompt[1:][idx+1:]:
                        if next_msg["role"] == "assistant":
                            st.markdown(f"**답변:** {next_msg['content']}")
                            break
    
if __name__ == "__main__":
    main()