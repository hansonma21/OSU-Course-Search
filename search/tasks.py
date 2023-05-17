from datetime import datetime
import os
import traceback
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
        """Clicks the 'Additional Search Criteria' button on the page to reveal additional options (e.g. lookup by last name)"""
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
        select.select_by_value(str(term))  # change this value for different semesters

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
                print("Element is not clickable... Trying again")
                submit_form(driver=driver,
                            url=url,
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
            print(last_name + ": " + successOrFail.text)
            return None
        else:
            print(last_name + ": Search Successful")
            return driver.page_source
        
    def parse_form(soup: BeautifulSoup, queryset_of_instructors):
        """Parses the html of the form and returns a list of courses"""

        print("Parsing form")
        # with open("test.html", "w") as f:
        #     f.write(soup.prettify())

        availabilityDict = {
            "/cs/csosuct/cache85909/PS_CS_STATUS_OPEN_ICN_1.gif": "Available",
            "/cs/csosuct/cache85909/PS_CS_STATUS_WAITLIST_ICN_1.gif": "Waitlist",
            "/cs/csosuct/cache85909/PS_CS_STATUS_CLOSED_ICN_1.gif": "Closed"
        }

        coursesRows = soup.find("table", {"id": "ACE_$ICField$4$$0"})
        coursesRows = coursesRows.find("tbody", recursive=False).find_all("tr", recursive=False) # type: ignore
        # print(len(coursesRows))
        for row in coursesRows:
            # this find keeps making the program crash
            fullCourseTitleElement = row.find("td", {"class": "PAGROUPBOXLABELLEVEL1"})
            if fullCourseTitleElement is None:
                continue

            fullCourseTitle = fullCourseTitleElement.get_text().strip()
            # print(fullCourseTitle)
            splitTitle = fullCourseTitle.split("-", maxsplit=1)
            deptAndNumber = splitTitle[0].strip()
            dept, number = deptAndNumber.split(" ", maxsplit=1)

            sectionRows = row.find_all(id=lambda x: x and x.startswith("ACE_SSR_CLSRSLT_WRK_GROUPBOX3"))

            # print(len(sectionRows))
            for sectionRow in sectionRows:
                rowData = sectionRow.find_all("td", {"class": "PSLEVEL3GRIDODDROW"})
                section_id = rowData[0].text.strip()
                section_info = rowData[1].text.strip().replace("\n", ",")
                days_and_times = rowData[2].text.strip()
                room = rowData[3].text.strip()
                meeting_dates = rowData[5].text.strip().split("\n")
                meeting_dates = meeting_dates[0].strip()
                # only get the first two for start and end date
                dates = meeting_dates.split(" - ")
                start_date = dates[0].strip()
                end_date = dates[1].strip()
                start_date = datetime.strptime(start_date, "%m/%d/%Y").date()
                end_date = datetime.strptime(end_date, "%m/%d/%Y").date()
                availabilityElement = rowData[6].find("img")
                availability = availabilityDict.get(availabilityElement.get_attribute_list("src")[0], "")

                try:
                    course_section = Course_Section.objects.get(section_id=int(section_id), term = Term.objects.get(osu_id=term))
                except Course_Section.DoesNotExist:
                    course_section = Course_Section(section_id=int(section_id), term=Term.objects.get(osu_id=term))
                
                try:
                    course_section.course = Course.objects.get(department__short_name=dept, number=number)
                    # check if the course is already in the term
                    if not course_section.course.terms.filter(osu_id=term).exists():
                        course_section.course.terms.add(Term.objects.get(osu_id=term))
                except Course.DoesNotExist:
                    newCourse = Course.objects.create(name=splitTitle[1], department=Department.objects.get(short_name=dept), number=number)
                    newCourse.terms.add(Term.objects.get(osu_id=term))
                    course_section.course = newCourse
                
                course_section.section_info = section_info
                course_section.days_and_times = days_and_times
                course_section.room = room
                course_section.start_date = start_date
                course_section.end_date = end_date
                course_section.availability = availability

                course_section.save()

                course_section.instructors.clear()
                course_section.instructors.add(*queryset_of_instructors)
                # print(course_section)


    def search_all_instructors_in_department(driver, url, term, department, nameToStart=None):
        # get all the last names from the instructors table given a department (in alphabetical order)
        instructors = Instructor.objects.filter(department__short_name=department)
        tuples_of_last_names = list(instructors.values_list('last_name').distinct().order_by('last_name'))
        

        for last_name_tuple in tuples_of_last_names:
            last_name = last_name_tuple[0]
            list_of_instructors = instructors.filter(last_name__iexact=last_name)

            if nameToStart is not None and last_name.lower() < nameToStart.lower():
                continue

            try:
                submittedForm = submit_form(driver, url, term, department, last_name, numFails=0)
                if submittedForm is not None:
                    soup = BeautifulSoup(submittedForm, 'html.parser')
                    parse_form(soup, list_of_instructors)
                    
                    
            except TimeoutException:
                return last_name
            except ElementClickInterceptedException:
                return last_name
        
        return None
            
    
    # if term is not in the database this scheduled task fails
    if not Term.objects.filter(osu_id=term).exists():
        raise Exception("Term does not exist in database")
    
    # if the department is not in the database this scheduled task fails
    if not Department.objects.filter(short_name=department).exists():
        raise Exception("Department does not exist in database")

    # selenium setup
    # print("test")
    options = webdriver.ChromeOptions()
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN") # type: ignore
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options) # type: ignore

    # url to scrape course data from (including hidden professors attached to them)
    url = "https://courses.osu.edu/psc/csosuct/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.osu.edu%2fpsp%2fcsosuct%2f&PortalURI=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"

    try:
        failed_name = search_all_instructors_in_department(driver=driver, url=url, term=term, department=department, nameToStart=None)
        while failed_name is not None:
            failed_name = search_all_instructors_in_department(driver, url, term, department, failed_name)
        
        return True
    except Exception as E:
        print(traceback.format_exc())
        return False
    finally:
        driver.quit()

def update_all_sections(term, start_at=None):
    """Updates all the sections in the database for a given term"""

    # if term is not in the database this scheduled task fails
    if not Term.objects.filter(osu_id=term).exists():
        raise Exception("Term does not exist in database")

    if start_at is not None:
        if not Department.objects.filter(short_name=start_at).exists():
            raise Exception("Department does not exist in database")
        
        departments = Department.objects.filter(short_name__gte=start_at).order_by('short_name')
    else:
        departments = Department.objects.all().order_by('short_name')
    
    for dept in departments.iterator():
        update_sections(term, dept.short_name)

def update_instructors():
    """Updates the instructors in the database"""

def update_terms():
    """Updates the terms in the database"""