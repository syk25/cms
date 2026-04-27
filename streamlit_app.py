import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="CMS", layout="wide")
st.title("콘텐츠 매니지먼트 서비스")

tab_ingest, tab_discovery, tab_cowrite, tab_distribute = st.tabs(
    ["글감 수집", "주제 추천", "글쓰기", "발행"]
)

# ── Tab 1: Ingest ──────────────────────────────────────────────────────────────
with tab_ingest:
    st.header("글감 수집")

    col_import, col_list = st.columns([1, 2])

    with col_import:
        st.subheader("Notion 동기화")
        st.caption("Notion DB에서 글감을 증분 import합니다.")
        if st.button("Notion 동기화 시작", type="primary"):
            with st.spinner("Notion에서 글감을 가져오는 중..."):
                res = requests.post(f"{API_BASE}/ingest/notion")
            if res.status_code == 200:
                data = res.json()
                st.success(f"{data['imported']}개 글감 import 완료")
            else:
                st.error(f"오류: {res.status_code} — {res.text}")

    with col_list:
        st.subheader("글감 목록")
        limit = st.slider("최대 표시 개수", 10, 200, 50, key="ingest_limit")
        if st.button("목록 새로고침"):
            with st.spinner("글감 목록 조회 중..."):
                res = requests.get(f"{API_BASE}/ingest/contents", params={"limit": limit})
            if res.status_code == 200:
                st.session_state["ingest_items"] = res.json()
            else:
                st.error(f"오류: {res.status_code}")

        if "ingest_items" in st.session_state:
            data = st.session_state["ingest_items"]
            st.caption(f"총 {data['total']}개")
            rows = [
                {
                    "소스": item.get("source", "-"),
                    "태그": ", ".join(item.get("tags", []) or []),
                    "글감": (item["text"] or "")[:120] + ("..." if len(item.get("text", "")) > 120 else ""),
                }
                for item in data["items"]
            ]
            st.dataframe(rows, use_container_width=True)

# ── Tab 2: Discovery ───────────────────────────────────────────────────────────
with tab_discovery:
    st.header("주제 추천")

    query = st.text_area(
        "어떤 주제로 쓰고 싶으세요?",
        placeholder="예) 개발자로서 번아웃을 극복한 경험을 써보고 싶어",
        height=100,
    )
    memory_ctx = st.text_input(
        "메모리 컨텍스트 (선택)",
        placeholder="예) 최근 커리어 전환에 관심 많음",
    )

    if st.button("주제 추천 받기", type="primary", disabled=not query.strip()):
        with st.spinner("RAG 검색 및 주제 추천 중..."):
            res = requests.post(
                f"{API_BASE}/discovery/route",
                json={"query": query, "memory_context": memory_ctx},
            )
        if res.status_code == 200:
            st.session_state["discovery_result"] = res.json()
        else:
            st.error(f"오류: {res.status_code} — {res.text}")

    if "discovery_result" in st.session_state:
        result = st.session_state["discovery_result"]
        intent_map = {"RECOMMEND": "주제 추천", "QUESTION": "질문 응답", "SUMMARIZE": "요약"}
        st.caption(f"의도: **{intent_map.get(result['intent'], result['intent'])}**")
        st.markdown(result["response"])

        if result["intent"] == "RECOMMEND":
            st.divider()
            topic_pick = st.text_input(
                "글쓰기 주제 선택",
                placeholder="위 추천 중 하나를 복사하거나 직접 입력",
                key="topic_pick",
            )
            if st.button("이 주제로 글쓰기 시작", disabled=not topic_pick.strip()):
                st.session_state["cowrite_topic"] = topic_pick
                st.success(f"주제 설정 완료 → '글쓰기' 탭으로 이동하세요.")

# ── Tab 3: Cowriting ───────────────────────────────────────────────────────────
with tab_cowrite:
    st.header("글쓰기")

    default_topic = st.session_state.get("cowrite_topic", "")
    topic = st.text_input("글쓰기 주제", value=default_topic, placeholder="주제를 입력하세요")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        if st.button("초안 생성", type="primary", disabled=not topic.strip()):
            with st.spinner("초안 작성 중..."):
                res = requests.post(
                    f"{API_BASE}/cowrite/draft",
                    json={"topic": topic, "related_contents": []},
                )
            if res.status_code == 200:
                data = res.json()
                st.session_state["cowrite_draft"] = data["draft"]
                st.session_state["cowrite_history"] = data["history"]
                st.session_state["cowrite_topic"] = topic
            else:
                st.error(f"오류: {res.status_code} — {res.text}")

        current_draft = None
        if "cowrite_draft" in st.session_state:
            current_draft = st.text_area(
                "초안 (직접 편집 가능)", value=st.session_state["cowrite_draft"], height=350
            )

            st.subheader("퇴고")
            feedback = st.text_area(
                "수정 요청",
                placeholder="예) 더 감성적인 톤으로, 3문단으로 나눠줘.",
                height=80,
                key="feedback_input",
            )
            if st.button("퇴고 요청", disabled=not feedback.strip()):
                with st.spinner("퇴고 중..."):
                    res = requests.post(
                        f"{API_BASE}/cowrite/revise",
                        json={
                            "feedback": feedback,
                            "history": st.session_state["cowrite_history"],
                        },
                    )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["cowrite_draft"] = data["draft"]
                    st.session_state["cowrite_history"] = data["history"]
                    st.rerun()
                else:
                    st.error(f"오류: {res.status_code} — {res.text}")

    with col_right:
        if "cowrite_draft" in st.session_state:
            st.subheader("품질 평가")
            if st.button("LLM-as-a-judge 평가"):
                with st.spinner("평가 중..."):
                    res = requests.post(
                        f"{API_BASE}/cowrite/judge",
                        json={
                            "topic": st.session_state.get("cowrite_topic", ""),
                            "draft": st.session_state.get("cowrite_draft", ""),
                            "related_contents": [],
                        },
                    )
                if res.status_code == 200:
                    st.session_state["judge_result"] = res.json()
                else:
                    st.error(f"오류: {res.status_code} — {res.text}")

            if "judge_result" in st.session_state:
                j = st.session_state["judge_result"]
                if j["passed"]:
                    st.success("통과 ✅")
                else:
                    st.warning("보완 필요 ⚠️")
                for metric, score in j["scores"].items():
                    st.metric(metric, score)
                st.caption(j["feedback"])

    if "cowrite_draft" in st.session_state:
        st.divider()
        st.subheader("원본 확정")
        tags_input = st.text_input("태그 (쉼표 구분)", placeholder="예) 개발, 성장, 커리어")
        if st.button("원본 확정 & 저장", type="primary"):
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            final_text = current_draft if current_draft is not None else st.session_state.get("cowrite_draft", "")
            with st.spinner("저장 중..."):
                res = requests.post(
                    f"{API_BASE}/cowrite/finalize",
                    json={
                        "text": final_text,
                        "topic": st.session_state.get("cowrite_topic", ""),
                        "tags": tags,
                        "raw_content_ids": [],
                    },
                )
            if res.status_code == 200:
                data = res.json()
                st.session_state["finalized_content_id"] = data["content_id"]
                st.success(f"저장 완료! Content ID: `{data['content_id']}`")
                st.info("'발행' 탭으로 이동하여 플랫폼 변환을 시작하세요.")
                for key in ("cowrite_draft", "cowrite_history", "judge_result"):
                    st.session_state.pop(key, None)
            else:
                st.error(f"오류: {res.status_code} — {res.text}")

# ── Tab 4: Distribute ──────────────────────────────────────────────────────────
with tab_distribute:
    st.header("플랫폼 발행")

    st.subheader("1. 원본 변환")
    default_cid = st.session_state.get("finalized_content_id", "")
    content_id = st.text_input(
        "Content ID",
        value=default_cid,
        placeholder="contents 테이블의 UUID",
    )

    if st.button("변환 시작", disabled=not content_id.strip()):
        with st.spinner("LangGraph Multi-Agent 변환 중..."):
            res = requests.post(f"{API_BASE}/distribute/convert", json={"content_id": content_id})
        if res.status_code == 200:
            st.session_state["convert_result"] = res.json()
            st.success("변환 완료")
        else:
            st.error(f"오류: {res.status_code} — {res.text}")

    if "convert_result" in st.session_state:
        result = st.session_state["convert_result"]
        ig = result["instagram"]
        brunch = result["brunch"]
        thread = result["thread"]

        tab_ig, tab_brunch, tab_thread = st.tabs(["인스타그램", "브런치", "스레드"])

        with tab_ig:
            st.subheader("캡션")
            caption_text = st.text_area("캡션 수정 가능", value=ig["caption"], height=150, key="caption")
            st.subheader("해시태그")
            hashtag_text = st.text_input(
                "해시태그 수정 가능 (쉼표 구분)",
                value=", ".join(ig["hashtags"]),
                key="hashtags",
            )

        with tab_brunch:
            st.subheader(brunch["title"])
            st.markdown(brunch["body"])

        with tab_thread:
            for i, post in enumerate(thread["posts"], 1):
                st.markdown(f"**{i}번 포스트**")
                st.info(post)

        st.divider()
        st.subheader("2. 인스타그램 발행")
        st.caption("Instagram Graph API는 이미지가 필수입니다. 공개 접근 가능한 이미지 URL을 입력하세요.")

        image_url = st.text_input("이미지 URL", placeholder="https://example.com/image.jpg")

        if st.button("인스타 발행", type="primary", disabled=not image_url.strip()):
            hashtags = [t.strip().lstrip("#") for t in hashtag_text.split(",") if t.strip()]
            payload = {
                "content_id": result["content_id"],
                "caption": caption_text,
                "hashtags": hashtags,
                "image_url": image_url,
            }
            with st.spinner("인스타그램에 발행 중..."):
                pub_res = requests.post(f"{API_BASE}/distribute/publish/instagram", json=payload)

            if pub_res.status_code == 200:
                data = pub_res.json()
                if data["status"] == "published":
                    st.success("발행 완료!")
                    st.markdown(f"[게시물 보기]({data['published_url']})")
                    st.session_state["published_url"] = data["published_url"]
                else:
                    st.warning(f"저장 완료 (발행 미완료) — status: {data['status']}")
            else:
                st.error(f"발행 실패: {pub_res.status_code} — {pub_res.text}")

        if "published_url" in st.session_state:
            st.info(f"발행 URL: {st.session_state['published_url']}")
