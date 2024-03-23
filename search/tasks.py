from datetime import datetime, timedelta, timezone
import json
import os
import multiprocessing
import traceback
from bs4 import BeautifulSoup
import redis
from .models import *
from django_q.models import Schedule
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

## TODO ##
# - write the scheduled code HERE (in functions that take arguments)
# - can create a scheduled task through the admin page
# - course_section_object.instructors.add(instructor_object) to add instructors to a course_section

def update_departments():
    """Updates the departments in the database"""

def update_courses():
    """Updates the courses in the database"""

def update_course_sections(term_osu_id=None, department=None):
    """Updates the course sections in the database, given a term (osu_id) and department (short_name)
    If not given a term, then it will update the course sections for all display_boolean=True terms
    If not given a department, then it will update the course sections for all departments
    This function will scrape the barrett class file and update the course sections in the database"""

    def split_class_file(content):
        """Splits the content of the barrett class file into metadata, headers, and classes"""
        lines = content.split("\n")
        # store first few lines as metadata
        # metadata goes from beginning of file to the line before the headers line which looks like "class#    (autoenrolls)                                enrld/limit/+wait"
        header_index = 0
        for i, line in enumerate(lines):
            if "class#" in line and "autoenrolls" in line and "enrld/limit/+wait" in line:
                header_index = i
                break
        metadata = lines[:header_index]
        # store the headers
        headers = lines[header_index].split()
        # store the classes from line header_index+2 until we reach a line that begins with "INDependent study classes" or "waitlist"
        classes = []
        for line in lines[header_index+2:]:
            if line.startswith("IND") or line.lower().startswith("waitlist"):
                # continue to pop the last element until we reach a non-empty line
                while len(classes) > 0 and len(classes[-1]) == 0:
                    classes.pop()
                break
            classes.append(line)
        # print(classes)

        # remove leading and trailing whitespace
        metadata = [line.strip() for line in metadata]
        headers = [header.strip() for header in headers]
        classes = [class_.strip() for class_ in classes]

        return metadata, headers, classes
    
    def preprocess_classes(classes):
        """Preprocesses the classes into a list of lists of classes (inner lists are grouped classes, outer list is the list of grouped classes)"""
        # parse through the classes
        parsed_classes = []
        for class_ in classes:
            # split the class into its columns
            columns = class_.split()
            # if the columns are empty, then we have a new class
            if not columns:
                parsed_classes.append([])
            else:
                if len(parsed_classes) == 0:
                    parsed_classes.append([])
                parsed_classes[-1].append(columns)
            
        return parsed_classes
    
    def parse_classes(parsed_classes):
        """Parses the list of lists of classes into a list of dictionaries"""
        # parse through the parsed classes and continue to process the data to properly format it to be written to a csv file
        # What I currently have: department, number, section/class #, type (e.g. L or B or others), autoenrolls (not always there), days (currently across multiple elements), time (not always present due to online classes), location, enrolled, limit, +wait (not always there), duration (not always present), instructor (not always present)
        # I need to combine the days into a single element, and I need to account for the fact that some elements may not be present
        # I also need to account for the fact that some classes have multiple sections

        # I will create a list of dictionaries, where each dictionary represents a class
        # I will then write the data to a csv file

        # create a list of dictionaries
        
        try:
            classes = []
            for parsed_class in parsed_classes:
                course_info = []
                for class_ in parsed_class:
                    class_info = {}
                    class_copy = class_.copy()
                    
                    # line could begin with "and". if it does, add the entire line to the previous class_info dictionary as a "additional information" key
                    if class_copy[0] == "and":
                        class_copy.pop(0)
                        course_info[-1]["additional information"] = " ".join(class_copy) # join the rest of the elements into a single string and add it to the dictionary
                        continue

                    # extract the department and number, then remove them from the list
                    department, number = class_copy[0], class_copy[1]
                    class_info["department"] = department
                    class_info["number"] = number
                    class_copy.pop(0)
                    class_copy.pop(0)

                    # extract the campus, section/class #, type, autoenrolls, days, time, location, enrolled, limit, +wait, duration, and instructor
                    # campus is not always present, but if it is, it is the next element
                    campus = ""
                    if class_copy[0].isalpha():
                        campus = class_copy[0]
                        class_copy.pop(0)

                    # section/class # and type are the next two elements
                    section_class_number = class_copy[0]
                    type_ = class_copy[1]
                    class_copy.pop(0)
                    class_copy.pop(0)

                    # autoenrolls is not always present, but if it is, it is currently stored across two elements: element 4: "(", element 5: "{autoenrolls})" or element 4: "(autoenrolls)"
                    # I want only the {autoenrolls} part
                    autoenrolls = ""
                    if class_copy[0].startswith("("):
                        if class_copy[0] == "(":
                            class_copy.pop(0)
                            autoenrolls = class_copy[0].strip(")")
                            class_copy.pop(0)
                        else:
                            autoenrolls = class_copy[0].strip("()")
                            class_copy.pop(0)

                    
                    # days is currently stored across multiple elements, but might not be present (e.g. ONLINE classes do not have days or times)
                    # combine the days into a single element (have to check if the days are present)
                    days = ""
                    # keep adding elements to days until we reach the time
                    while class_copy[0][0].upper() in ["M", "T", "W", "R", "F", "S", "U"]:
                        days += class_copy[0]
                        class_copy.pop(0)
                    
                    # time is not always present, but if it is, it starts with a digit
                    time = ""
                    if class_copy[0][0].isdigit() and "/" not in class_copy[0]:
                        time = class_copy[0]
                        class_copy.pop(0)
                    
                    # location is the next element. not always present, but if it is present, it is the next element
                    location = ""
                    if class_copy[0][0].isalpha():
                        location = class_copy[0]
                        class_copy.pop(0)

                    # enrolled, limit, are stored across a single element as {enrolled}/{limit}. +wait is stored in the element after enrolled and limit, but +wait is not always present
                    # print(class_copy[0])
                    enrolled, limit = class_copy[0].split("/")
                    class_copy.pop(0)
                    plus_wait = ""
                    if len(class_copy) > 0 and class_copy[0].startswith("+"):
                        plus_wait = class_copy[0]
                        class_copy.pop(0)
                    
                    # duration is not always present, but if it is, it is the next element and startswith "{"
                    duration = ""
                    if len(class_copy) > 0 and class_copy[0].startswith("{"):
                        duration = class_copy[0]
                        class_copy.pop(0)
                    
                    # instructor is the next element, but is not always present
                    instructors = []
                    # print(class_copy[0])
                    while len(class_copy) > 0 and class_copy[0][0].isalpha():
                        instructors.append(class_copy[0].strip(","))
                        class_copy.pop(0)
                    
                    # final descriptor of instructor is the next element, but is not always present (starts with "(")
                    instructor_descriptor = ""
                    if len(class_copy) > 0 and class_copy[0].startswith("("):
                        instructor_descriptor = class_copy[0]
                        class_copy.pop(0)
                    
                    # add the class to the list
                    class_info["section/class #"] = section_class_number
                    class_info["type"] = type_
                    class_info["autoenrolls"] = autoenrolls
                    class_info["days"] = days
                    class_info["time"] = time
                    class_info["location"] = location
                    class_info["enrolled"] = enrolled
                    class_info["limit"] = limit
                    class_info["+wait"] = plus_wait
                    class_info["duration"] = duration
                    class_info["instructors"] = instructors
                    class_info["instructor descriptor"] = instructor_descriptor
                    course_info.append(class_info)
                classes.append(course_info)
        except Exception as e:
            # return the last class that was being processed
            return "Error", traceback.format_exc(), class_

        return "Success", "OK", classes
    
    def save_classes(classes, term_id, link_number):
        """Saves the classes to the database, under the assumption that all classes are in the same department and term"""
        # for each class, create a course_section object and save it to the database
        for class_ in classes:
            for course_info in class_:
                # get the department and number
                department = course_info["department"]
                number = course_info["number"]

                # get the term
                try:
                    term = Term.objects.get(osu_id=term_id)
                except Term.DoesNotExist:
                    term = Term.objects.create(osu_id=term_id)
                    term.save()

                # get the course
                try:
                    course = Course.objects.get(department__short_name=department, number=number)
                except Course.DoesNotExist:
                    course = Course.objects.create(department=Department.objects.get(short_name=department), number=number)
                    course.terms.add(term)
                    course.save()
                
                # create a course section for each class
                section_id = course_info["section/class #"]
                # check if the course section already exists
                try:
                    course_section = Course_Section.objects.get(section_id=section_id, term=term)
                except Course_Section.DoesNotExist:
                    course_section = Course_Section(section_id=int(section_id), term=term)

                
                course_section.course = course
                course_section.link_number = link_number
                # create a json object for the barret data with only the necessary information ("type", "autoenrolls", "days", "time", "location", "enrolled", "limit", "waitlist", "duration", "instructors")
                barrett_data = {}
                barrett_data["type"] = course_info["type"]
                barrett_data["autoenrolls"] = course_info["autoenrolls"]
                barrett_data["days"] = course_info["days"]
                barrett_data["time"] = course_info["time"]
                barrett_data["location"] = course_info["location"]
                barrett_data["enrolled"] = course_info["enrolled"]
                barrett_data["limit"] = course_info["limit"]
                barrett_data["waitlist"] = course_info["+wait"]
                barrett_data["duration"] = course_info["duration"]
                barrett_data["instructors"] = course_info["instructors"]

                course_section.barrett_data_json = barrett_data  # type: ignore
                course_section.save()

            link_number += 1

    if term_osu_id is not None:
        terms = Term.objects.filter(osu_id=term_osu_id)
    else:
        # get list of terms (only those that have display_boolean = True) and departments
        terms = Term.objects.filter(display_boolean=True)
    
    if department is not None:
        departments = Department.objects.filter(short_name=department)
    else:
        departments = Department.objects.all()

    # scrape through https://www.asc.ohio-state.edu/barrett.3/schedule/{department_short_name}/{term}.txt
    dept_term_url = "https://www.asc.ohio-state.edu/barrett.3/schedule/{}/{}.txt"

    # for each term and department, get the barrett data and update the course sections
    for term in terms:
        for dept in departments:
            # print("Currently on department: {} and term: {}".format(dept, term))
            url = dept_term_url.format(dept.short_name, term.osu_id)
            page = requests.get(url)
            # print(page.text)

            if page.status_code != 200:
                # all_classes_by_term_department[term][dept] = []
                continue

            metadata, headers, classes = split_class_file(page.text)
            preprocessed_classes = preprocess_classes(classes)
            indicator, stacktrace, parsed_classes = parse_classes(preprocessed_classes)
            if indicator == "Error":
                # add the error to the Error_Logs table
                error_message = "Error occurred while parsing the file for department: {} and term: {}".format(dept.short_name, term.osu_id)
                error_log = Error_Log.objects.create(error_message=error_message, 
                                                      stack_trace=str(stacktrace), 
                                                      function_name="update_course_sections",
                                                      additional_info=str(parsed_classes))
                error_log.save()
                continue
            else:
                try:
                    # get maximum link number
                    link_number = Course_Section.objects.filter(term=term).aggregate(models.Max('link_number'))['link_number__max']
                    if link_number is None:
                        link_number = 0
                    save_classes(parsed_classes, term.osu_id, link_number+1)
                except Exception as e:
                    # add the error to the Error_Logs table
                    error_message = "Error occurred while saving the classes for department: {} and term: {}".format(dept.short_name, term.osu_id)
                    additional_info = "Stopping the updating..."
                    error_log = Error_Log.objects.create(error_message=error_message, 
                                                      stack_trace=traceback.format_exc(), 
                                                      function_name="update_course_sections",
                                                      additional_info=additional_info)
                    error_log.save()
                    break
        else:
            continue # only executed if the inner loop did NOT break
        break # only executed if the inner loop DID break



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

        if select.first_selected_option.get_attribute("value") != str(term):
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
            "/cs/ps/cache85921/PS_CS_STATUS_OPEN_ICN_1.gif": "Available",
            "/cs/ps/cache85921/PS_CS_STATUS_WAITLIST_ICN_1.JPG": "Waitlist",
            "/cs/ps/cache85921/PS_CS_STATUS_CLOSED_ICN_1.gif": "Closed"
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

                instructors = rowData[4].text.replace("\n", "").split(",")

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

                if instructors[0].lower() != "to be announced":
                    for instructor in instructors:
                        # print(instructor.split(" ")[0], instructor.split(" ")[-1])
                        name_splits = instructor.split(" ")
                        first_name = name_splits[0]
                        last_name = name_splits[-1]
                        try:
                            instructor = Instructor.objects.get(first_name=first_name, last_name=last_name, department__short_name=dept)
                        except Instructor.DoesNotExist:
                            instructor = Instructor.objects.create(first_name=first_name, last_name=last_name, department=Department.objects.get(short_name=dept))
                        course_section.instructors.add(instructor)
                else:
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
                print("Submitting form for " + last_name + "...")
                submittedForm = submit_form(driver, url, term, department, last_name, numFails=0)
                if submittedForm is not None:
                    soup = BeautifulSoup(submittedForm, 'html.parser')
                    parse_form(soup, list_of_instructors)
                    
                    
            except TimeoutException:
                return last_name
            except ElementClickInterceptedException:
                return last_name
        
        return None
            
    
    def update_sections_helper(term, department):
        # if term is not in the database this scheduled task fails
        if not Term.objects.filter(osu_id=term).exists():
            raise Exception("Term does not exist in database")
        
        # if the department is not in the database this scheduled task fails
        if not Department.objects.filter(short_name=department).exists():
            raise Exception("Department does not exist in database")

        # selenium setup
        # print("test1")
        # options = webdriver.ChromeOptions()
        # # options.binary_location = os.environ.get("GOOGLE_CHROME_BIN") # type: ignore
        # options.add_argument('--no-sandbox')
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')

        # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options) # type: ignore
        # print("test2")
        # driver = webdriver.Chrome(options=options)
        # print("test3")

        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.CHROME,
            )
        
        # url to scrape course data from (including hidden professors attached to them)
        url = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsp%2fps%2f&PortalURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"

        try:
            failed_name = search_all_instructors_in_department(driver=driver, url=url, term=term, department=department, nameToStart=None)
            while failed_name is not None:
                failed_name = search_all_instructors_in_department(driver, url, term, department, failed_name)
            
            # return True
        except Exception as E:
            # write the error to the error logs
            error_message = "Error occurred while updating the sections for department: {} and term: {}".format(department, term)
            error_log = Error_Log.objects.create(error_message=error_message,
                                                    stack_trace=traceback.format_exc(),
                                                    function_name="update_sections")
            error_log.save()
            # return False
        finally:
            driver.quit()
    
    # # call the helper function via multiprocessing
    # p = multiprocessing.Process(target=update_sections_helper, args=(term, department))
    # # run the function in a separate process
    # p.start()
    # # wait for process to finish
    # p.join()
            
    update_sections_helper(term, department)

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

def update_next_section(task):
    """Updates the next section in the database for a given term"""

    term = task.kwargs.get('term')

    previous_department = task.kwargs.get('department')
    next_department = Department.objects.filter(short_name__gt=previous_department).order_by('short_name').first()

    if next_department is not None:
        next_department_short_name = next_department.short_name
        print(next_department_short_name)

        # create a new task to update the next department
        schedule_name = '{}_{}_auto'.format(next_department, term)
        new_kwargs = {'term': term, 'department': next_department_short_name}
        Schedule.objects.create(name=schedule_name, 
                                func=task.func, 
                                kwargs=new_kwargs, 
                                schedule_type=Schedule.ONCE, 
                                hook=task.hook)

def schedule_all_update_sections(term=None, start_at=None):
    """Schedules all the update_sections tasks for all departments and terms"""

    if start_at is not None:
        if not Department.objects.filter(short_name=start_at).exists():
            raise Exception("Department does not exist in database")
        
        departments = Department.objects.filter(short_name__gte=start_at).order_by('short_name')
    else:
        departments = Department.objects.all().order_by('short_name')

    if term is not None:
        if not Term.objects.filter(osu_id=term).exists():
            raise Exception("Term does not exist in database")
        
        terms = Term.objects.filter(osu_id=term)
    else:
        terms = Term.objects.filter(display_boolean=True)


    for term_ in terms.iterator():
        for department in departments.iterator():
            schedule_name = '{}_{}_auto'.format(department.short_name, term_.osu_id)
            kwargs = {'term': term_.osu_id, 'department': department.short_name}

            Schedule.objects.create(name=schedule_name, 
                                    func='search.tasks.update_sections', 
                                    kwargs=kwargs, 
                                    schedule_type=Schedule.ONCE)


def update_instructors():
    """Updates the instructors in the database"""

def update_terms():
    """Updates the terms in the database"""

def clear_redis_cache():
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushdb()