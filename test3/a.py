import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from time import sleep
import re
import hashlib
from collections import defaultdict

# 저장할 폴더
save_dir = "fomos_images"
os.makedirs(save_dir, exist_ok=True)

# 로그 폴더
log_dir = "fomos_logs"
os.makedirs(log_dir, exist_ok=True)

# 요청 헤더 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.fomos.kr/'
}

# indexno 범위 설정
start = 1791000
end = 1791867  # 테스트를 위해 좁은 범위로 설정해도 됩니다

base_url = "https://www.fomos.kr/talk/article_view?bbs_id=5&indexno="

# 이미지 중복 방지를 위한 해시 저장소
image_hashes = set()
duplicate_count = 0
ignored_images = set()  # 무시할 이미지 URL 패턴

# 통계 추적
stats = {
    "total_articles": 0,
    "articles_with_images": 0,
    "total_images_found": 0,
    "unique_images_downloaded": 0,
    "duplicates_skipped": 0,
    "errors": 0
}

def get_image_hash(img_data):
    """이미지 데이터의 MD5 해시를 계산합니다."""
    return hashlib.md5(img_data).hexdigest()

def save_debug_info(index, soup):
    """디버깅을 위해 HTML 구조 정보를 저장합니다."""
    try:
        debug_file = os.path.join(log_dir, f"debug_{index}.txt")
        with open(debug_file, 'w', encoding='utf-8') as f:
            # 페이지 제목
            title = soup.title.string if soup.title else "제목 없음"
            f.write(f"페이지 제목: {title}\n\n")
            
            # 가능한 본문 영역 클래스 목록
            f.write("=== 가능한 본문 영역 ===\n")
            for div in soup.find_all('div', class_=True):
                class_name = ' '.join(div.get('class'))
                img_count = len(div.find_all('img'))
                text_len = len(div.text.strip())
                if img_count > 0 or text_len > 200:  # 이미지가 있거나 텍스트가 많은 div
                    f.write(f"클래스: {class_name}, 이미지 수: {img_count}, 텍스트 길이: {text_len}\n")
            
            # 이미지 태그 목록
            f.write("\n=== 이미지 태그 정보 ===\n")
            for i, img in enumerate(soup.find_all('img')):
                src = img.get('src') or img.get('data-src') or "없음"
                alt = img.get('alt') or "없음"
                width = img.get('width') or "없음"
                height = img.get('height') or "없음"
                parent = img.parent.name
                parent_class = ' '.join(img.parent.get('class')) if img.parent.get('class') else "없음"
                
                f.write(f"이미지 #{i+1}:\n")
                f.write(f"  src: {src}\n")
                f.write(f"  alt: {alt}\n")
                f.write(f"  크기: {width}x{height}\n")
                f.write(f"  부모 태그: {parent}, 클래스: {parent_class}\n\n")
    except Exception as e:
        print(f"디버그 정보 저장 중 오류: {e}")

def should_ignore_image(url):
    """무시해야 할 이미지인지 확인합니다."""
    # 무시할 URL 패턴 (광고, 아이콘, UI 요소 등)
    ignore_patterns = [
        'banner', 'logo', 'icon', 'button', 
        'header', 'footer', 'nav', 'avatar',
        'bg_', 'background', 'ad_', 'ads_',
        'emoji', 'emoticon', 'thumbnail'
    ]
    
    url_lower = url.lower()
    
    # 이미 무시 목록에 있는 URL 패턴
    if url in ignored_images:
        return True
        
    # 패턴 매치 확인
    for pattern in ignore_patterns:
        if pattern in url_lower:
            ignored_images.add(url)
            return True
            
    return False

def is_valid_content_image(img_tag):
    """이미지가 본문 내용의 일부인지 확인합니다."""
    # 1. alt 텍스트가 있으면 본문 이미지일 가능성 높음
    alt = img_tag.get('alt', '')
    if alt and len(alt) > 5 and not any(x in alt.lower() for x in ['logo', 'icon', 'banner']):
        return True
        
    # 2. 크기가 큰 이미지는 본문 이미지일 가능성 높음
    width = img_tag.get('width')
    height = img_tag.get('height')
    if width and height:
        try:
            if int(width) > 100 and int(height) > 100:
                return True
        except ValueError:
            pass
            
    # 3. 특정 CSS 클래스나 ID를 가진 이미지
    classes = img_tag.get('class', [])
    if classes and any(c in [c.lower() for c in classes] for c in ['content', 'article', 'post', 'image']):
        return True
        
    # 4. 부모 태그의 클래스/ID 확인
    parent = img_tag.parent
    if parent:
        parent_classes = parent.get('class', [])
        if parent_classes and any(c in [c.lower() for c in parent_classes] for c in ['content', 'article', 'post', 'text']):
            return True
            
    return False

def normalize_url(url, base):
    """URL을 정규화합니다."""
    if not url:
        return None
        
    # 빈 URL이나 javascript 링크 제외
    if url.startswith('javascript:') or url == '#':
        return None
        
    # 상대 URL을 절대 URL로 변환
    full_url = urljoin(base, url)
    
    return full_url

def download_image(img_url, index, img_index):
    """이미지를 다운로드하고 중복 체크를 수행합니다."""
    global duplicate_count
    
    try:
        # URL 검증
        if not img_url or should_ignore_image(img_url):
            return False
            
        # 이미지 다운로드
        img_response = requests.get(img_url, headers=headers, timeout=10)
        if img_response.status_code != 200:
            print(f"✗ 이미지 다운로드 실패 (상태코드: {img_response.status_code}): {img_url}")
            return False
            
        # Content-Type 확인
        content_type = img_response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            print(f"✗ 이미지가 아닌 컨텐츠: {content_type}")
            return False
            
        # 이미지 데이터
        img_data = img_response.content
        
        # 파일 크기가 너무 작으면 의미 있는 이미지가 아닐 수 있음
        if len(img_data) < 5000:  # 5KB 미만
            print(f"✗ 너무 작은 이미지 무시: {len(img_data)} bytes")
            return False
            
        # 이미지 해시 계산 (중복 확인용)
        img_hash = get_image_hash(img_data)
        
        # 이미 다운로드한 이미지인지 확인
        if img_hash in image_hashes:
            print(f"✗ 중복 이미지 무시: {img_url}")
            stats["duplicates_skipped"] += 1
            return False
        
        # 이미지 해시 저장
        image_hashes.add(img_hash)
        
        # 확장자 결정
        ext = 'jpg'  # 기본 확장자
        if 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
            
        # 파일명 생성 및 저장
        filename = f"{index}_{img_index}.{ext}"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
            
        print(f"✓ 이미지 저장 완료: {filename} ({len(img_data)/1024:.1f} KB)")
        stats["unique_images_downloaded"] += 1
        return True
        
    except Exception as e:
        print(f"✗ 이미지 다운로드 중 오류: {e}")
        stats["errors"] += 1
        return False

def find_content_area(soup):
    """게시글 본문 영역을 찾습니다."""
    # 일반적인 본문 영역 클래스
    common_content_classes = [
        'view_content', 'article_content', 'content', 'board_content',
        'post_content', 'entry_content', 'article-content', 'post-content'
    ]
    
    # 1. 직접적인 클래스명으로 찾기
    for class_name in common_content_classes:
        content = soup.find(['div', 'article', 'section'], class_=class_name)
        if content:
            return content
    
    # 2. 클래스명에 'content' 또는 'article'이 포함된 요소 찾기
    for element in soup.find_all(['div', 'article', 'section'], class_=True):
        class_names = ' '.join(element.get('class')).lower()
        if 'content' in class_names or 'article' in class_names or 'post' in class_names:
            # 텍스트 길이가 충분히 길거나 이미지가 포함된 경우만
            if len(element.text.strip()) > 200 or len(element.find_all('img')) > 0:
                return element
    
    # 3. id에 'content' 또는 'article'이 포함된 요소 찾기
    for id_name in ['content', 'article', 'post']:
        content = soup.find(id=re.compile(id_name, re.I))
        if content:
            return content
    
    # 4. 가장 텍스트가 많은 div 찾기 (마지막 수단)
    divs = soup.find_all('div')
    if divs:
        # 텍스트 길이 기준으로 정렬
        divs_by_text = sorted(divs, key=lambda x: len(x.text.strip()), reverse=True)
        if divs_by_text and len(divs_by_text[0].text.strip()) > 200:
            return divs_by_text[0]
    
    return None

def process_article(index):
    """게시글 처리 함수"""
    url = f"{base_url}{index}"
    stats["total_articles"] += 1
    
    try:
        print(f"\n[{index}/{end}] 처리 중: {url}")
        
        # 웹 페이지 요청
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"✗ 페이지 접근 실패 (상태코드: {response.status_code})")
            return 0
            
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 디버깅 정보 저장
        save_debug_info(index, soup)
        
        # 게시글 본문 영역 찾기
        content_area = find_content_area(soup)
        
        if content_area:
            print(f"✓ 본문 영역 식별: {content_area.name} (클래스: {content_area.get('class', '없음')})")
            images = content_area.find_all('img')
        else:
            print("⚠️ 본문 영역 식별 실패, 전체 HTML에서 이미지 검색")
            images = soup.find_all('img')
        
        # 이미지 수 기록
        print(f"발견된 이미지: {len(images)}개")
        stats["total_images_found"] += len(images)
        
        if not images:
            return 0
        
        # 본문 내용에 해당하는 이미지만 필터링
        content_images = []
        for img in images:
            # src 또는 data-src 속성 확인
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue
                
            # URL 정규화
            img_url = normalize_url(img_url, url)
            if not img_url:
                continue
                
            # 유효한 콘텐츠 이미지인지 확인
            if is_valid_content_image(img):
                content_images.append((img, img_url))
        
        print(f"콘텐츠 이미지로 식별됨: {len(content_images)}개")
        
        # 이미지 다운로드
        downloaded = 0
        for i, (img, img_url) in enumerate(content_images):
            success = download_image(img_url, index, i)
            if success:
                downloaded += 1
                
        if downloaded > 0:
            stats["articles_with_images"] += 1
            print(f"✓ 게시글 {index}에서 {downloaded}개 이미지 다운로드 완료")
            
        return downloaded
            
    except Exception as e:
        print(f"✗ 게시글 {index} 처리 중 오류 발생: {e}")
        stats["errors"] += 1
        return 0

# 메인 실행 코드
print(f"포모스 이미지 스크래핑 시작 (인덱스 {start}~{end})...")

for index in range(start, end + 1):
    process_article(index)
    # 과도한 요청 방지
    sleep(1)
    
    # 중간 결과 출력 (10개 게시글마다)
    if (index - start + 1) % 10 == 0 or index == end:
        print("\n--- 현재까지 스크래핑 현황 ---")
        print(f"처리된 게시글: {stats['total_articles']}개")
        print(f"이미지 있는 게시글: {stats['articles_with_images']}개")
        print(f"발견된 총 이미지: {stats['total_images_found']}개")
        print(f"다운로드된 고유 이미지: {stats['unique_images_downloaded']}개")
        print(f"중복으로 건너뛴 이미지: {stats['duplicates_skipped']}개")
        print(f"오류 발생: {stats['errors']}회")
        print("-----------------------")

# 최종 결과 출력
print("\n==== 스크래핑 완료 ====")
print(f"처리된 게시글: {stats['total_articles']}개")
print(f"이미지 있는 게시글: {stats['articles_with_images']}개")
print(f"발견된 총 이미지: {stats['total_images_found']}개")
print(f"다운로드된 고유 이미지: {stats['unique_images_downloaded']}개")
print(f"중복으로 건너뛴 이미지: {stats['duplicates_skipped']}개")
print(f"이미지 저장 폴더: {os.path.abspath(save_dir)}")
print(f"디버그 로그 폴더: {os.path.abspath(log_dir)}")