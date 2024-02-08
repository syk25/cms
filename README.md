# 🗒 온라인 쇼핑몰 서비스
### 소개
소비자가 상품을 보고 장바구니에 담아 주문할 수 있는 서비스입니다.
### 개발동기
이커머스에서 마주할 수 있는 문제를 특정하고 기술들을 탐색, 적용하여 해결경험을 얻고자 함입니다.

## 기능
### 회원
1. 회원 가입 기능 - 아이디, 비밀번호, 이름, 전화번호, 이메일, 주소, 마케팅 수신동의 여부를 저장하여 회원 가입 기능을 구현합니다.
2. SNS 가입 기능
3. 회원 로그인 기능 - 아이디와 비밀번호를 입력하여 로그인을 합니다.
4. SNS 로그인 기능

### 상품
1. 상품 등록 기능 - 관리자는 상품명, 상품 수량, 상품소개를 등록할 수 있습니다.
2. 상품 검색 기능 - 상품명을 입력 할 경우, 상품 사진, 제목, 가격을 포함한 상품 정보객체 리스트를 반환합니다.
3. 상품 상세 조회 기능 - 상품목록 중에 상품 객체를 선택할 경우 상품상세 정보(상품명, 가격, 상세설명)을 반환합니다.

### 장바구니
1. 장바구니에 추가 기능 - 상품을 상품명과 수량을 함께 장바구니에 추가합니다.
2. 장바구니에서 상품 삭제 기능 - 장바구니에 상품명과 수량을 선택하여 삭제할 수 있습니다.
3. 장바구니 조회 기능 - 장바구니에 담긴 상품의 상품명, 가격, 개수, 총 가격을 보여줍니다.

### 주문 / 결제
1. 주문 기능 - 구매자, 받는 사람, 결제 정보(주문수단, 지불 비용)을 담아 결제를 요청합니다.
2. 주문 취소 기능 - 결제 취소 요청 후 주문기록에 주문이 취소되었음을 갱신합니다.
3. 주문 조회 기능 - 주문목록을 보여줍니다. 주문목록에는 주문일자, 주문 상세가 명시되어 있습니다.

## 적용 기술
1. Framework: spring security, JPA, AOP, caching
2. db: H2, MySQL, Redis
3. search: elastic search
4. testing: mockito

## 시스템 구성도

## ERD

<img width="841" alt="Screenshot 2023-12-18 at 3 36 55 AM" src="https://github.com/syk25/e-cms/assets/129013571/6fd2ca4b-9a8b-4d5a-b2a0-01f6e11fcd5e">

### 기술스택
<div align=center> 
  <img src="https://img.shields.io/badge/java-007396?style=for-the-badge&logo=java&logoColor=white"> 
  <img src="https://img.shields.io/badge/spring-6DB33F?style=for-the-badge&logo=spring&logoColor=white"> 
  <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white"> 
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
</div>



