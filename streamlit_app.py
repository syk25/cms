import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="CMS - 발행 검토", layout="wide")
st.title("콘텐츠 매니지먼트 - 플랫폼 발행")

# ── 변환 섹션 ──────────────────────────────────────────────────────────────────
st.header("1. 원본 변환")

content_id = st.text_input("Content ID", placeholder="contents 테이블의 UUID")

if st.button("변환 시작", disabled=not content_id):
    with st.spinner("LangGraph Multi-Agent 변환 중..."):
        res = requests.post(f"{API_BASE}/distribute/convert", json={"content_id": content_id})
    if res.status_code == 200:
        st.session_state["convert_result"] = res.json()
        st.success("변환 완료")
    else:
        st.error(f"오류: {res.status_code} — {res.text}")

# ── 변환 결과 표시 ─────────────────────────────────────────────────────────────
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
        hashtag_text = st.text_input("해시태그 수정 가능 (쉼표 구분)", value=", ".join(ig["hashtags"]), key="hashtags")

    with tab_brunch:
        st.subheader(brunch["title"])
        st.markdown(brunch["body"])

    with tab_thread:
        for i, post in enumerate(thread["posts"], 1):
            st.markdown(f"**{i}번 포스트**")
            st.info(post)

    # ── 인스타 발행 섹션 ───────────────────────────────────────────────────────
    st.divider()
    st.header("2. 인스타그램 발행")
    st.caption("Instagram Graph API는 이미지가 필수입니다. 공개 접근 가능한 이미지 URL을 입력하세요.")

    image_url = st.text_input("이미지 URL", placeholder="https://example.com/image.jpg")

    if st.button("인스타 발행", type="primary", disabled=not image_url):
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
