from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mma_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mma_scraper")

XML_PAYLOAD = """<?xml version="1.0" encoding="UTF-8"?>
<Root xmlns="http://www.nexacroplatform.com/platform/dataset">
    <Parameters>
        <Parameter id="SCOUTER">x4ukdpk8jj6p2b</Parameter>
        <Parameter id="ssotoken">Vy3zFyENGINEx5F1zTyGIDx5FRAONx5F1zCy1744419662zPy86400zAy23zEysX1G118eCx2BwVx2BQHboU32qJV6JPUJ4MKfVRUPwZx79PIYk4Db8ZM5x7ADZAWlBvx79apD9YN49ux78L6EpfJZpiu7GFumwx79FHHx79Qkl72A1x7Apjcmpx7A8BRBBUWffoIPx79gx78a4knEs4Kugdb61HBQ8u2x2F4RMYsuuMwV8x7Alx2BZPmFKK62x78aLI1eXc7DfOa0VG1XKlulx78fLx78bKMKpmHvCHeCK1moHWSCPbx2Bx78158CY46hRMgiDx788pk2x2BXonJ9j7eIkNbifx7A3r6x79E4sooE7Z5Sax7AwT8uGi9qKYw7mVh5nUBJkg3H33GM7MenBAhB2x78b3qYLEpsO8rx2BYX7cqTOGT30M2l8Gx7AKYHu2YAL0Ua4J2U6ECBCFua4pwex7Adx2BsZG4x3DzKyCnvIx2B43ksFCTgEjK9Nl5Pmnx2BMx78l2QVi1x2FHcgR6UgrMkP8dh8V5YGLcJusgPcKrlTx00x00x00x00x00zSSy00002938051zUURy08ba5752053809bazMymaZAx7AWXUaIgx3Dz</Parameter>
    </Parameters>
    <Dataset id="inputVO">
        <ColumnInfo>
            <Column id="eopjong_gbcd" type="STRING" size="256"  />
            <Column id="eopjong_gbcd_list" type="STRING" size="4000"  />
            <Column id="gegyumo_cd" type="STRING" size="256"  />
            <Column id="eopche_nm" type="STRING" size="256"  />
            <Column id="juso" type="STRING" size="256"  />
            <Column id="chaeyongym" type="STRING" size="256"  />
            <Column id="bjinwonym" type="STRING" size="256"  />
            <Column id="hyun_bjinwonym" type="STRING" size="256"  />
            <Column id="bo_bjinwonym" type="STRING" size="256"  />
            <Column id="juso_cd" type="STRING" size="256"  />
            <Column id="sido_cd" type="STRING" size="256"  />
            <Column id="sigungu_cd" type="STRING" size="256"  />
        </ColumnInfo>
        <Rows>
            <Row>
                <Col id="eopjong_gbcd">1</Col>
                <Col id="eopjong_gbcd_list">11111</Col>
                <Col id="gegyumo_cd">02</Col>
                <Col id="eopche_nm" />
                <Col id="juso_cd">1100000000</Col>
                <Col id="sido_cd">1100000000</Col>
                <Col id="sigungu_cd">1168000000</Col>
            </Row>
        </Rows>
    </Dataset>
</Root>"""

def setup_driver():
    """Setup and return configured Chrome WebDriver"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-images")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    options.add_argument("--page-load-strategy=eager")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        raise

def perform_search(driver, search_params):
    """Perform search with specified parameters"""
    try:
        driver.get("https://work.mma.go.kr/caisBYIS/search/byjjecgeomjeongList.do")
        logger.info("Starting page navigation")
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        logger.info("Page loaded successfully")
        
        eopjong_gbcd = search_params.get("eopjong_gbcd", "1")  # 산업기능요원
        sigungu_cd = search_params.get("sigungu_cd", "1168000000")  # 강남구
        
        # Select 산업기능요원 checkbox
        select_industrial_technician(driver)
        
        # Select 정보처리 industry option
        select_information_processing(driver)
        
        # Select location (강남구)
        select_location(driver, sigungu_cd)
        
        click_search_button(driver)
        
        return wait_for_results(driver)
    
    except Exception as e:
        logger.error(f"Error in search process: {e}")
        return False

def select_industrial_technician(driver):
    """Select the industrial technician checkbox"""
    try:
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for checkbox in checkboxes:
            try:
                label = checkbox.find_element(By.XPATH, "./following-sibling::label").text
                if "산업기능요원" in label:
                    logger.info("Found industrial technician checkbox")
                    driver.execute_script("arguments[0].click();", checkbox)
                    time.sleep(1)
                    return
            except:
                continue
        
        logger.info("Trying JavaScript approach for checkbox")
        result = driver.execute_script("""
            const labels = document.querySelectorAll('label');
            for(let label of labels) {
                if(label.textContent.includes('산업기능요원')) {
                    const checkbox = label.previousElementSibling;
                    if(checkbox && checkbox.type === 'checkbox') {
                        checkbox.click();
                        return true;
                    }
                }
            }
            return false;
        """)
        
        if result:
            logger.info("Selected industrial technician checkbox with JavaScript")
        else:
            logger.warning("Failed to select industrial technician checkbox")
        
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error selecting industrial technician checkbox: {e}")
        raise

def select_information_processing(driver):
    """Select the information processing industry"""
    try:
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        for select in select_elements:
            options = select.find_elements(By.TAG_NAME, "option")
            for opt in options:
                if "정보처리" in opt.text:
                    logger.info("Found information processing option")
                    driver.execute_script("arguments[0].click();", opt)
                    time.sleep(1)
                    return
        
        logger.info("Trying JavaScript approach for information processing")
        result = driver.execute_script("""
            const selects = document.querySelectorAll('select');
            for(let select of selects) {
                const options = select.querySelectorAll('option');
                for(let option of options) {
                    if(option.textContent.includes('정보처리')) {
                        option.selected = true;
                        const event = new Event('change', { bubbles: true });
                        select.dispatchEvent(event);
                        return true;
                    }
                }
            }
            return false;
        """)
        
        if result:
            logger.info("Selected information processing with JavaScript")
        else:
            logger.warning("Failed to select information processing")
        
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error selecting information processing: {e}")
        raise

def select_location(driver, sigungu_cd=None):
    """Select the location (강남구)"""
    try:
        region_options = driver.find_elements(By.XPATH, "//option[contains(text(), '강남구')]")
        if region_options:
            logger.info("Found Gangnam-gu option")
            driver.execute_script("arguments[0].click();", region_options[0])
            time.sleep(1)
            return
        
        logger.info("Trying JavaScript approach for location")
        result = driver.execute_script("""
            const selects = document.querySelectorAll('select');
            for(let select of selects) {
                const options = select.querySelectorAll('option');
                for(let option of options) {
                    if(option.textContent.includes('강남구')) {
                        option.selected = true;
                        const event = new Event('change', { bubbles: true });
                        select.dispatchEvent(event);
                        return true;
                    }
                }
            }
            return false;
        """)
        
        if result:
            logger.info("Selected Gangnam-gu with JavaScript")
        else:
            logger.warning("Failed to select Gangnam-gu")
        
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error selecting location: {e}")
        raise

def click_search_button(driver):
    """Click the search button"""
    try:
        search_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")
        if search_buttons:
            logger.info("Found submit button")
            driver.execute_script("arguments[0].click();", search_buttons[0])
            return
            
        search_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '검색')]")
        if search_buttons:
            logger.info("Found search button by text")
            driver.execute_script("arguments[0].click();", search_buttons[0])
            return
            
        logger.info("Trying JavaScript approach for search button")
        result = driver.execute_script("""
            const buttons = document.querySelectorAll('button');
            for(let button of buttons) {
                if(button.textContent.includes('검색')) {
                    button.click();
                    return true;
                }
            }
            return false;
        """)
        
        if result:
            logger.info("Clicked search button with JavaScript")
        else:
            logger.warning("Failed to click search button")
            
    except Exception as e:
        logger.error(f"Error clicking search button: {e}")
        raise

def wait_for_results(driver):
    """Wait for and process search results"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        logger.info(f"Found {len(rows)} result rows")
        
        return rows
    except Exception as e:
        logger.error(f"Error waiting for results: {e}")
        return []

def process_results(rows, output_file="산업기능요원_채용정보.csv"):
    """Process and save search results"""
    try:
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["번호", "업체명", "업종", "소재지", "복무형태", "상세보기 링크"])
            
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:
                        logger.warning(f"Row {i+1} has insufficient cells: {len(cells)}")
                        continue
                    
                    company = cells[1].text.strip()
                    industry = cells[2].text.strip() if len(cells) > 2 else ""
                    location = cells[3].text.strip() if len(cells) > 3 else ""
                    service_type = cells[4].text.strip() if len(cells) > 4 else ""
                    
                    try:
                        link = cells[1].find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        link = "링크 없음"
                    
                    writer.writerow([i+1, company, industry, location, service_type, link])
                    logger.info(f"Saved: {i+1}. {company}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {i+1}: {e}")
                    continue
            
        logger.info(f"Successfully saved {len(rows)} results to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error processing results: {e}")
        return False

def extract_search_params_from_xml(xml_payload):
    """Extract search parameters from XML payload"""
    try:
        return {
            "eopjong_gbcd": "1",         
            "eopjong_gbcd_list": "11111",
            "gegyumo_cd": "02",           
            "eopche_nm": "",              
            "juso_cd": "1100000000",      
            "sido_cd": "1100000000",      
            "sigungu_cd": "1168000000",   
        }
    except Exception as e:
        logger.error(f"Error extracting search parameters from XML: {e}")
        return {}

def main():
    driver = None
    try:
        driver = setup_driver()
        search_params = extract_search_params_from_xml(XML_PAYLOAD)
        rows = perform_search(driver, search_params)
        
        if not rows:
            logger.error("No results found or error occurred during search")
            return
        
        success = process_results(rows)
        
        if success:
            logger.info(f"✅ Crawling completed! Total {len(rows)} results saved to CSV file.")
        else:
            logger.error("Failed to process results")
            
    except Exception as e:
        logger.error(f"❌ Overall process error: {e}")
        
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    main()