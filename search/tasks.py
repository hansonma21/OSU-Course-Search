from datetime import datetime
from bs4 import BeautifulSoup
from .models import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException

## TODO ##
# - write the scheduled code HERE (in functions that take arguments)
# - can create a scheduled task through the admin page
# - course_section_object.instructors.add(instructor_object) to add instructors to a course_section

def update_departments():
    """Updates the departments in the database"""

def update_courses():
    """Updates the courses in the database"""

def update_sections(term, department):
    """Updates the sections in the database"""

    def click_Add_Srch_Criteria(driver):
        more_buttons = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//img[@alt='Additional Search Criteria']")))

        if more_buttons.is_displayed():
            more_buttons.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "SSR_CLSRCH_WRK_LAST_NAME$8")))

    def submit_form(driver, url, term, department, last_name, numFails=0):
        """Submits the form on the page and returns the html of the page"""
        webDriverWait = WebDriverWait(driver, 20)
        driver.get(url)

        # selecting spring 2023 and then reopening additional search criteria
        ########################################################
        toWaitOn = webDriverWait.until(
            EC.visibility_of_element_located((By.NAME, "CLASS_SRCH_WRK2_STRM$35$")))
        # toWaitOn = driver.find_element(By.ID, "SSR_CLSRCH_WRK_LAST_NAME$8")

        select = Select(driver.find_element(By.NAME, "CLASS_SRCH_WRK2_STRM$35$"))
        select.select_by_value(term)  # change this value for different semesters

        webDriverWait.until(EC.staleness_of(toWaitOn))
        click_Add_Srch_Criteria(driver)

        # lastname search, type = text
        lastNameSearch = webDriverWait.until(
            EC.visibility_of_element_located((By.NAME, "SSR_CLSRCH_WRK_LAST_NAME$8")))
        lastNameSearch.send_keys(last_name)

        foundElement = webDriverWait.until(
            EC.visibility_of_element_located(
            (By.NAME, "SSR_CLSRCH_WRK_SSR_EXACT_MATCH2$8")))
        select = Select(foundElement)
        select.select_by_value("E")  # exactly the last name, not just begins with
        # driver.find_element(By.NAME, "SSR_CLSRCH_WRK_LAST_NAME$8").send_keys(lastName)

        # major selection (CSE), type = select
        foundElement = webDriverWait.until(
            EC.visibility_of_element_located(
            (By.NAME, "SSR_CLSRCH_WRK_SUBJECT_SRCH$1")))
        select = Select(foundElement)
        # select.select_by_visible_text("Computer Science & Engineering")
        select.select_by_value(
            department)  # DONT KNOW WHY THIS DOESN'T PROPERLY SELECT CSE
        # webDriverWait.until(EC.element_attribute_to_include((By.XPATH, "//option[@value='CSE']"), "selected"))


        ########################################################

        # final clicks (unchecking open classes only checkbox and clicking search)
        ########################################################
        try:
            webDriverWait.until(
            EC.element_to_be_clickable(
                (By.NAME, "SSR_CLSRCH_WRK_SSR_OPEN_ONLY$4"))).click()
        except ElementClickInterceptedException:
            if numFails == 0:
                # print("Element is not clickable... Trying again")
                submit_form(driver,
                            url,
                            term=term,
                            department=department,
                            last_name=last_name,
                            numFails=1)
            else:
                return None

        # driver.find_element(By.NAME, "SSR_CLSRCH_WRK_SSR_OPEN_ONLY$4").click()
        webDriverWait.until(
            EC.text_to_be_present_in_element_value(
            (By.NAME, "SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$4"), "N"))

        webDriverWait.until(
            EC.element_to_be_clickable(
            (By.NAME, "CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH"))).click()

        # looking for successful search OR an error
        successOrFail = webDriverWait.until(
            EC.any_of(
            EC.presence_of_element_located((By.ID, "DERIVED_CLSMSG_ERROR_TEXT")),
            EC.presence_of_element_located((By.CLASS_NAME, "PSLEVEL1GRIDNBONBO"))))
        # test = driver.find_element(By.ID, "DERIVED_CLSMSG_ERROR_TEXT")
        # test.accessible_name
        # test.text
        # test.get_attribute("id")
        # test.find_element(By.XPATH, "//option[value=UGRD").get_property("selected")
        # print(successOrFail.get_attribute("id"))
        if successOrFail.get_attribute("id") == "DERIVED_CLSMSG_ERROR_TEXT":
            # print(lastName + ": " + successOrFail.text)
            return None
        else:
            # print(lastName + ": Search Successful")
            return driver.page_source
        
    def parse_form(soup: BeautifulSoup):
        availabilityDict = {
            "/cs/csosuct/cache85909/PS_CS_STATUS_OPEN_ICN_1.gif": "Available",
            "/cs/csosuct/cache85909/PS_CS_STATUS_WAITLIST_ICN_1.gif": "Waitlist",
            "/cs/csosuct/cache85909/PS_CS_STATUS_CLOSED_ICN_1.gif": "Closed"
        }

        coursesRows = soup.find("table", {"id": "ACE_$ICField$4$$0"})
        coursesRows = coursesRows.find("tbody").find_all("tr") # type: ignore
        
        for row in coursesRows:
            if len(row.text):
                continue

            fullCourseTitle = row.find("td", {"class": "PAGROUPBOXLABELLEVEL1"}).text
            splitTitle = fullCourseTitle.split("-")
            deptAndNumber = splitTitle[0].strip()
            dept, number = deptAndNumber.split(" ")

            sectionRows = row.find_all("table", {"id": lambda x: x and x.startswith("ACE_SSR_CLSRSLT_WRK_GROUPBOX3")})

            for sectionRow in sectionRows:
                rowData = sectionRow.find_all("td", {"class": "PSLEVEL3GRIDODDROW"})
                section_id = rowData[0].text
                section_info = rowData[1].text.replace("\n", ",")
                days_and_times = rowData[2].text
                room = rowData[3].text
                meeting_dates = rowData[5].text
                start_date, end_date = meeting_dates.split(" - ")
                start_date= datetime.strptime(start_date, "%m/%d/%Y").date()
                end_date = datetime.strptime(end_date, "%m/%d/%Y").date()
                availabilityElement = rowData[6].find("img")
                availability = availabilityDict.get(availabilityElement.get_attribute_list("src")[0], "")

                course_section, created = Course_Section.objects.get_or_create(section_id=section_id, term=term)
                
                course_section.course = Course.objects.get(department__short_name=dept, number=number)
                course_section.section_info = section_info
                course_section.days_and_times = days_and_times
                course_section.room = room
                course_section.start_date = start_date
                course_section.end_date = end_date
                availability = availability

                course_section.save()


    def FILLER_METHOD_NAME(driver, url, term, department, nameToStart):
        instructors = Instructor.objects.filter(department__short_name=department)

        tuples_of_last_names = list(instructors.values_list('last_name').distinct().order_by('last_name'))
        # get all the last names from the instructors table given a department
        

        for last_name_tuple in tuples_of_last_names:
            last_name = last_name_tuple[0]

            if nameToStart != '' and last_name.lower() < nameToStart.lower():
                continue

            try:
                submittedForm = submit_form(driver, url, term, department, last_name, numFails=0)
                if submittedForm is not None:
                    soup = BeautifulSoup(submittedForm, 'html.parser')
                    parse_form(soup)
                    
                    
            except TimeoutException:
                return last_name
            except ElementClickInterceptedException:
                return last_name


    # selenium setup
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    # webDriverWait = WebDriverWait(driver, 20)

    # url to scrape course data from (including hidden professors attached to them)
    url = "https://courses.osu.edu/psc/csosuct/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.osu.edu%2fpsp%2fcsosuct%2f&PortalURI=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"

    try:
        failed_name = FILLER_METHOD_NAME(driver, url, term, department, '')
        while failed_name is not None:
            failed_name = FILLER_METHOD_NAME(driver, url, term, department, failed_name)
    except Exception as E:
        print(E)
    finally:
        driver.close()


def update_instructors():
    """Updates the instructors in the database"""

def update_terms():
    """Updates the terms in the database"""