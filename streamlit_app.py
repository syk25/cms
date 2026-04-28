import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="CMS", layout="wide")
st.title("콘텐츠 매니지먼트 서비스")

tab_ingest, tab_write, tab_distribute = st.tabs(["글감 수집", "글 쓰기", "발행"])


# ── 스트리밍 헬퍼 ──────────────────────────────────────────────────────────────

def _iter_stream(url: str, payload: dict):
    """텍스트 청크를 그대로 yield하는 단순 스트리밍 이터레이터."""
    with requests.post(url, json=payload, stream=True, timeout=60) as res:
        res.raise_for_status()
        for chunk in res.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


class _DiscoveryStream:
    """첫 줄(intent)을 파싱하고 나머지를 스트리밍하는 이터레이터."""

    def __init__(self, url: str, payload: dict):
        self.url = url
        self.payload = payload
        self.intent: str | None = None

    def __iter__(self):
        buf = ""
        first_done = False
        with requests.post(self.url, json=self.payload, stream=True, timeout=60) as res:
            res.raise_for_status()
            for chunk in res.iter_content(chunk_size=None, decode_unicode=True):
                if not chunk:
                    continue
                if not first_done:
                    buf += chunk
                    if "\n" in buf:
                        first_line, rest = buf.split("\n", 1)
                        self.intent = first_line.strip()
                        first_done = True
                        if rest:
                            yield rest
                else:
                    yield chunk


# ── Tab 1: Ingest ──────────────────────────────────────────────────────────────
with tab_ingest:
    st.header("글감 수집")

    col_import, col_list = st.columns([1, 2])

    with col_import:
        st.subheader("Notion 동기화")
        st.caption("Notion DB에서 글감을 증분 import합니다.")
        if st.button("동기화 시작", type="primary"):
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
                    "글감": (item["text"] or "")[:120]
                    + ("..." if len(item.get("text", "")) > 120 else ""),
                }
                for item in data["items"]
            ]
            st.dataframe(rows, use_container_width=True)


# ── Tab 2: Write (Discovery + Cowriting 합침) ─────────────────────────────────
with tab_write:
    if "write_phase" not in st.session_state:
        st.session_state["write_phase"] = "start"
    if "write_messages" not in st.session_state:
        st.session_state["write_messages"] = []

    phase = st.session_state["write_phase"]

    # 대화 히스토리 렌더링
    for msg in st.session_state["write_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── start: 주제 입력 ──────────────────────────────────────────────────────
    if phase == "start":
        if not st.session_state["write_messages"]:
            with st.chat_message("assistant"):
                st.markdown(
                    "어떤 주제로 글을 쓰고 싶으세요?\n\n"
                    "관심 있는 경험이나 키워드를 자유롭게 입력하면 관련 주제를 추천해드려요."
                )

        query = st.text_area(
            "주제 입력",
            placeholder="예: 개발자로서 번아웃을 극복한 경험",
            height=80,
            label_visibility="collapsed",
            key="start_query",
        )
        if st.button("주제 추천 받기", type="primary", disabled=not query.strip()):
            q = query.strip()
            st.session_state["write_messages"].append({"role": "user", "content": q})

            discovery = _DiscoveryStream(
                f"{API_BASE}/discovery/route/stream",
                {"query": q, "memory_context": ""},
            )
            with st.chat_message("assistant"):
                full_text = st.write_stream(discovery)

            st.session_state["write_messages"].append(
                {"role": "assistant", "content": full_text}
            )
            st.session_state["write_phase"] = "recommended"
            st.rerun()

    # ── recommended: 주제 선택 ────────────────────────────────────────────────
    elif phase == "recommended":
        topic_input = st.text_input(
            "추천 주제 중 하나를 복사하거나 직접 입력하세요",
            placeholder="주제 입력...",
            key="topic_select_input",
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("이 주제로 초안 작성", type="primary", disabled=not topic_input.strip()):
                topic = topic_input.strip()
                st.session_state["write_topic"] = topic
                st.session_state["write_messages"].append(
                    {"role": "user", "content": f"**주제 선택**: {topic}"}
                )

                with st.chat_message("assistant"):
                    draft_text = st.write_stream(
                        _iter_stream(
                            f"{API_BASE}/cowrite/draft/stream",
                            {"topic": topic, "related_contents": []},
                        )
                    )

                st.session_state["write_draft"] = draft_text
                st.session_state["draft_edit"] = draft_text
                # history: agent가 구성하는 user_message와 동일하게 맞춤
                user_msg = f"주제: {topic}\n\n관련 글감:\n\n위 글감을 바탕으로 초안을 작성해줘."
                st.session_state["write_history"] = [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": draft_text},
                ]
                st.session_state["write_messages"].append(
                    {"role": "assistant", "content": "초안이 완성됐어요. 아래에서 직접 편집하거나 퇴고 요청을 입력하세요."}
                )
                st.session_state["write_phase"] = "drafting"
                st.rerun()
        with col2:
            if st.button("다른 주제 탐색"):
                st.session_state["write_phase"] = "start"
                st.rerun()

    # ── drafting: 퇴고 ────────────────────────────────────────────────────────
    elif phase == "drafting":
        col_draft, col_actions = st.columns([3, 1])

        with col_draft:
            current_draft = st.text_area(
                "초안 (직접 편집 가능)",
                value=st.session_state.get("write_draft", ""),
                height=400,
                key="draft_edit",
            )

        with col_actions:
            if st.button("LLM-as-a-judge 평가"):
                with st.spinner("평가 중..."):
                    res = requests.post(
                        f"{API_BASE}/cowrite/judge",
                        json={
                            "topic": st.session_state.get("write_topic", ""),
                            "draft": current_draft,
                            "related_contents": [],
                        },
                    )
                if res.status_code == 200:
                    st.session_state["judge_result"] = res.json()
                    st.rerun()

            if "judge_result" in st.session_state:
                j = st.session_state["judge_result"]
                if j["passed"]:
                    st.success("통과 ✅")
                else:
                    st.warning("보완 필요 ⚠️")
                for metric, score in j["scores"].items():
                    st.metric(metric, score)
                st.caption(j["feedback"])

            st.divider()
            tags_input = st.text_input(
                "태그 (쉼표 구분)", placeholder="개발, 성장, 커리어", key="write_tags"
            )
            if st.button("원본 확정 & 저장", type="primary"):
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                with st.spinner("저장 중..."):
                    res = requests.post(
                        f"{API_BASE}/cowrite/finalize",
                        json={
                            "text": current_draft,
                            "topic": st.session_state.get("write_topic", ""),
                            "tags": tags,
                            "raw_content_ids": [],
                        },
                    )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["finalized_content_id"] = data["content_id"]
                    st.session_state["finalized_content_preview"] = current_draft[:200]
                    st.session_state["write_messages"].append(
                        {
                            "role": "assistant",
                            "content": "원본이 저장됐어요. **발행** 탭에서 플랫폼 변환을 시작하세요.",
                        }
                    )
                    st.session_state["write_phase"] = "done"
                    for key in ("write_draft", "write_history", "judge_result", "draft_edit", "write_tags"):
                        st.session_state.pop(key, None)
                    st.rerun()
                else:
                    st.error(f"저장 실패: {res.status_code} — {res.text}")

        st.divider()
        feedback = st.text_area(
            "퇴고 요청",
            placeholder="예: 더 감성적인 톤으로, 마지막 문단 다시 써줘",
            height=80,
            key="feedback_input",
        )
        if st.button("퇴고 요청", disabled=not feedback.strip()):
            st.session_state["write_draft"] = current_draft
            history = st.session_state.get("write_history", [])
            st.session_state["write_messages"].append({"role": "user", "content": feedback})

            with st.chat_message("assistant"):
                revised_text = st.write_stream(
                    _iter_stream(
                        f"{API_BASE}/cowrite/revise/stream",
                        {"feedback": feedback, "history": history},
                    )
                )

            st.session_state["write_draft"] = revised_text
            st.session_state["draft_edit"] = revised_text
            st.session_state["write_history"] = history + [
                {"role": "user", "content": feedback},
                {"role": "assistant", "content": revised_text},
            ]
            st.session_state["write_messages"].append(
                {"role": "assistant", "content": "퇴고 완료! 위 초안이 업데이트됐어요."}
            )
            st.rerun()

    # ── done ──────────────────────────────────────────────────────────────────
    elif phase == "done":
        st.success("발행 탭에서 인스타그램·브런치·스레드로 변환·발행할 수 있어요.")
        if st.button("새 글 쓰기"):
            clear_keys = [
                k for k in st.session_state
                if k.startswith("write_")
                or k in ("judge_result", "draft_edit", "write_tags",
                         "topic_select_input", "feedback_input", "start_query")
            ]
            for k in clear_keys:
                st.session_state.pop(k, None)
            st.rerun()


# ── Tab 3: Distribute ──────────────────────────────────────────────────────────
with tab_distribute:
    st.header("플랫폼 발행")

    content_id = st.session_state.get("finalized_content_id")

    if not content_id:
        st.info("글쓰기 탭에서 원본을 확정하면 여기서 발행할 수 있어요.")
    else:
        preview = st.session_state.get("finalized_content_preview", "")
        if preview:
            with st.expander("확정된 원본 미리보기"):
                st.markdown(preview + ("..." if len(preview) >= 200 else ""))

        st.subheader("1. 플랫폼 변환")
        if st.button("인스타·브런치·스레드 동시 변환", type="primary"):
            with st.spinner("LangGraph Multi-Agent 변환 중..."):
                res = requests.post(
                    f"{API_BASE}/distribute/convert", json={"content_id": content_id}
                )
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
                caption_text = st.text_area(
                    "캡션 (수정 가능)", value=ig["caption"], height=150, key="caption"
                )
                hashtag_text = st.text_input(
                    "해시태그 (쉼표 구분, 수정 가능)",
                    value=", ".join(ig["hashtags"]),
                    key="hashtags",
                )

            with tab_brunch:
                st.subheader(brunch["title"])
                st.markdown(brunch["body"])

            with tab_thread:
                for i, post in enumerate(thread["posts"], 1):
                    st.markdown(f"**{i}번**")
                    st.info(post)

            st.divider()
            st.subheader("2. 인스타그램 발행")
            st.caption("Instagram Graph API는 이미지가 필수입니다.")

            image_url = st.text_input(
                "이미지 URL", placeholder="https://example.com/image.jpg"
            )

            if st.button("발행하기", type="primary", disabled=not image_url.strip()):
                hashtags = [t.strip().lstrip("#") for t in hashtag_text.split(",") if t.strip()]
                with st.spinner("인스타그램에 발행 중..."):
                    pub_res = requests.post(
                        f"{API_BASE}/distribute/publish/instagram",
                        json={
                            "content_id": content_id,
                            "caption": caption_text,
                            "hashtags": hashtags,
                            "image_url": image_url,
                        },
                    )
                if pub_res.status_code == 200:
                    data = pub_res.json()
                    if data["status"] == "published":
                        st.success("발행 완료!")
                        st.markdown(f"[게시물 보기]({data['published_url']})")
                    else:
                        st.warning(f"저장 완료 (발행 미완료) — status: {data['status']}")
                else:
                    st.error(f"발행 실패: {pub_res.status_code} — {pub_res.text}")
