from bs4 import BeautifulSoup
import requests
from search.models import *
from datetime import datetime
import traceback
from typing import Tuple
from django_q.models import Schedule

class OSUCourseScraper:
    """Base class for scraping course information from the OSU course website"""

    def __init__(self, 
                 term: int, 
                 department: str, 
                 url: str = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL"):
        """Initializes the OSUCourseScraper object with the term, department, and url to scrape from"""
        # if term is not in the database this scheduled task fails
        if not Term.objects.filter(osu_id=term).exists():
            raise Exception("Term does not exist in database")
        
        # if the department is not in the database this scheduled task fails
        if not Department.objects.filter(short_name=department).exists():
            raise Exception("Department does not exist in database")
        
        self.term: int = term
        self.department: str = department
        self.url: str = url
        self._session: requests.Session | None = None
        self._cookie: str | None = None
        self._sessionId: str | None = None
    
    def _get_cookie_and_sessionId(self, session: requests.Session) -> dict[str, str] | None:
        """Gets the cookie and session id from the initial request to the url"""
        try:
            response = session.post(self.url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)  # remove later
            return None
        
        # formatting the cookies to be used in the next request
        cookie_str = "; ".join([f"{c.name}={c.value}" for c in response.cookies])

        # parsing the response to get the session id
        soup = BeautifulSoup(response.content, 'html.parser')
        session_id_input = soup.find('input', {'name': 'ICSID'})

        if session_id_input is None:
            print("Unable to read ICSID, input not found")
            return None
        
        # check type of session_id_input to avoid type error
        if not isinstance(session_id_input, str):
            session_id = session_id_input['value']
        else:
            print("Unable to read ICSID value")
            return None

        # return the cookie and session id
        result = {'cookie': cookie_str, 'sessionId': session_id}
        # print(result)   # remove later
        return result
    
    def _create_new_session(self) -> Tuple[requests.Session, str, str]:
        """Creates a new session and gets the cookie and session id and returns them as a tuple"""
        new_session = requests.Session()

        # get the cookie and session id
        cookie_and_sessionId = self._get_cookie_and_sessionId(new_session)
        if cookie_and_sessionId is None:
            raise Exception("Unable to get cookie and session id")
        
        cookie = cookie_and_sessionId['cookie']
        sessionId = cookie_and_sessionId['sessionId']

        return new_session, cookie, sessionId
    
    def create_new_session(self):
        """Closes existing session and creates a new session and sets the session, cookie, and sessionId attributes"""
        self._close_session(self._session)
        self._session, self._cookie, self._sessionId = self._create_new_session()

    def _close_session(self, session: requests.Session | None):
        """Closes the current session"""
        if session is not None:
            session.close()

    
    def close_session(self):
        """Closes the current session and sets the session, cookie, and sessionId attributes to None"""
        self._close_session(self._session)
        self._session = None
        self._cookie = None
        self._sessionId = None
    
    def extract(self):
        """Extracts the data from the website"""
        raise NotImplementedError("Subclasses must implement this method")
    def transform(self):
        """Transforms the extracted data into the format to be saved in the database"""
        raise NotImplementedError("Subclasses must implement this method")
    def load(self):
        """Loads the transformed data into the database"""
        raise NotImplementedError("Subclasses must implement this method")
    def run(self):
        """Runs the scraper to extract, transform, and load the data into the database"""
        raise NotImplementedError("Subclasses must implement this method")
    


class CourseInstructorScraper(OSUCourseScraper):
    """Scraper for extracting course and instructor information from the OSU course website, mainly used to attach instructors to course sections"""
    def __init__(self, 
                 term: int, 
                 department: str, 
                 url: str = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL"):
        
        super().__init__(term, department, url)

        self._current_instructor: Instructor | None = None

        self._sections: list[dict[str, str]] | None = None
        self._sections_to_save: list[Tuple[Course_Section, list[str]]] | None = None
        self._sections_saved: list[int] | None = None   # list of section ids that have been saved
    
    def _send_request(self, session: requests.Session, actionStr: str, cookie: str, sessionId: str) -> requests.Response:
        data = {
            "ICAction": actionStr,
            "ICSID": sessionId,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "cookie": cookie,
        }

        if actionStr == "select_term":
            data["CLASS_SRCH_WRK2_STRM$35$"] = str(self.term)
        elif actionStr == "expand_search_criteria":
            data["CLASS_SRCH_WRK2_STRM$35$"] = str(self.term)
            data["SSR_CLSRCH_WRK_SUBJECT_SRCH$1"] = self.department
            data["SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$4"] = "N"
            data["SSR_CLSRCH_WRK_SSR_EXACT_MATCH2$8"] = "E"

        response = session.post(self.url, data=data, headers=headers)
        return response
    
    def _send_instructor_request(self, session: requests.Session, instructor: Instructor, cookie: str, sessionId: str) -> requests.Response:
        
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/x-www-form-urlencoded",
            "cookie": cookie,
        }

        data = {
            "ICAction": "CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH",
            "ICSID": sessionId,
            "SSR_CLSRCH_WRK_LAST_NAME$8": instructor.last_name,
            "SSR_CLSRCH_WRK_SSR_EXACT_MATCH2$8": "E",
            "SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$4": "N",
        }

        try: 
            response = session.post(self.url, data=data, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            return response
        
        return response
    
    def _parse_instructor_response(self, response: requests.Response) -> list[dict[str, str]]:
        soup = BeautifulSoup(response.text, 'html.parser')
        sections = []

        # availabilityDict = {
        #     "/cs/ps/cache85921/PS_CS_STATUS_OPEN_ICN_1.gif": "Available",
        #     "/cs/ps/cache85921/PS_CS_STATUS_WAITLIST_ICN_1.JPG": "Waitlist",
        #     "/cs/ps/cache85921/PS_CS_STATUS_CLOSED_ICN_1.gif": "Closed"
        # }

        coursesRows = soup.select("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX2\$]")

        for row in coursesRows:
            # this find keeps making the program crash
            fullCourseTitleElement = row.find("td", {"class": "PAGROUPBOXLABELLEVEL1"})
            fullCourseTitleElement = row.select_one("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX2GP]")
            if fullCourseTitleElement is None:
                continue

            fullCourseTitle = fullCourseTitleElement.get_text().strip()
            # print(fullCourseTitle)
            splitTitle = fullCourseTitle.split("-", maxsplit=1)
            deptAndNumber = splitTitle[0].strip()
            dept, number = deptAndNumber.split(" ", maxsplit=1)

            sectionRows = row.select("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX3]")

            # print(len(sectionRows))
            for sectionRow in sectionRows:
                rowData = sectionRow.find_all("td", {"class": "PSLEVEL3GRIDODDROW"})
                section_id = rowData[0].text.strip()
                section_info = rowData[1].text.strip().replace("\n", ",")
                days_and_times = rowData[2].text.strip()
                room = rowData[3].text.strip()

                instructors = rowData[4].text.replace("\n", "")

                meeting_dates = rowData[5].text.strip().split("\n")
                meeting_dates = meeting_dates[0].strip()
                # only get the first two for start and end date
                dates = meeting_dates.split(" - ")
                start_date = dates[0].strip()
                end_date = dates[1].strip()
                # start_date = datetime.strptime(start_date, "%m/%d/%Y").date()
                # end_date = datetime.strptime(end_date, "%m/%d/%Y").date()
                availabilityElement = rowData[6].find("img")

                # get the alt="" attribute of the availabilityElement
                availability = availabilityElement['alt']
                # availability = availabilityDict.get(availabilityElement.get_attribute_list("src")[0], "")

                section = {
                    'section_id': section_id,
                    'dept': dept,
                    'number': number,
                    'name': splitTitle[1],
                    'section_info': section_info,
                    'days_and_times': days_and_times,
                    'room': room,
                    'start_date': start_date,
                    'end_date': end_date,
                    'availability': availability,
                    'instructors_str': instructors,
                }
                sections.append(section)

        return sections

    def run(self):
        self._instructors = Instructor.objects.filter(department__short_name=self.department)

        for instructor in self._instructors:
            self._current_instructor = instructor

            self._session, self._cookie, self._sessionId = self._create_new_session()
            
            self._extract(instructor)
            # extracts = self.get_extracted_sections()
            # if extracts is not None and len(extracts) > 0:
            #     pprint(extracts[0])
            #     print(len(extracts))
            self._transform(instructor)
            # pprint(self.get_transformed_sections())
            self._load(instructor)
        
            self._close_session(self._session)
        self._session = None

    def _extract(self, instructor: Instructor):
        if self._session is None or self._cookie is None or self._sessionId is None:
            raise Exception("Session is not initialized")
        
        if self._sections is None:
            self._sections = []
        
        self._search_session = requests.Session()
        # select the term
        response = self._send_request(self._search_session, "select_term", self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to select term")
        
        # expand search criteria
        response = self._send_request(self._search_session, "expand_search_criteria", self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to expand search criteria")
        
        # search for the instructor
        response = self._send_instructor_request(self._search_session, instructor, self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to search for instructor")
        
        # parse the response
        self._sections.extend(self._parse_instructor_response(response))

        self._search_session.close()
        self._search_session = None
    
    def extract(self):
        if self._current_instructor is None:
            raise Exception("No current instructor set")
        self._extract(self._current_instructor)
        

    def _transform(self, instructor: Instructor):
        if self._sections is None:
            raise Exception("No sections to transform")
        
        self._sections_to_save = []
        for section in self._sections:
            section_id = section['section_id']
            course_title = section['name']
            course_dept = section['dept']
            course_number = section['number']
            term = self.term

            section_info = section['section_info']
            days_and_times = section['days_and_times']
            room = section['room']
            start_date = section['start_date']
            end_date = section['end_date']
            availability = section['availability']
            instructor_info = section['instructors_str']

            start_date = datetime.strptime(start_date, "%m/%d/%Y").date()
            end_date = datetime.strptime(end_date, "%m/%d/%Y").date()

            try:
                course_section = Course_Section.objects.get(section_id=int(section_id), term = Term.objects.get(osu_id=term))
            except Course_Section.DoesNotExist:
                course_section = Course_Section(section_id=int(section_id), term=Term.objects.get(osu_id=term))
            
            try:
                course_section.course = Course.objects.get(department__short_name=course_dept, number=course_number)
                # check if the course is already in the term
                if not course_section.course.terms.filter(osu_id=term).exists():
                    course_section.course.terms.add(Term.objects.get(osu_id=term))
            except Course.DoesNotExist:
                newCourse = Course.objects.create(name=course_title, department=Department.objects.get(short_name=course_dept), number=course_number)
                newCourse.terms.add(Term.objects.get(osu_id=term))
                course_section.course = newCourse
            
            course_section.section_info = section_info
            course_section.days_and_times = days_and_times
            course_section.room = room
            course_section.start_date = start_date
            course_section.end_date = end_date
            course_section.availability = availability

            self._sections_to_save.append((course_section, instructor_info.split(",")))
        
        self._sections = None
        
    def transform(self):
        if self._current_instructor is None:
            raise Exception("No current instructor set")
        self._transform(self._current_instructor)

    def _load(self, instructor: Instructor):
        if self._sections_to_save is None:
            raise Exception("No sections to save")
        
        if self._sections_saved is None:
            self._sections_saved = []
        
        for course_section_tuple in self._sections_to_save:
            course_section = course_section_tuple[0]
            instructor_info = course_section_tuple[1]

            course_section.save()
            if course_section.section_id not in self._sections_saved:
                course_section.instructors.clear()

            if instructor_info[0].lower() != "to be announced":
                for instructor_str in instructor_info:
                    name_splits = instructor_str.split(" ")
                    first_name = name_splits[0]
                    last_name = name_splits[-1]
                    course_section_dept = course_section.course.department
                    try:
                        instructor_to_add = Instructor.objects.get(first_name=first_name, last_name=last_name, department=course_section_dept)
                    except Instructor.DoesNotExist:
                        instructor_to_add = Instructor.objects.create(first_name=first_name, last_name=last_name, department=course_section_dept)
                    
                    course_section.instructors.add(instructor_to_add)
            else:
                # find all instructors in the department that have the same last name
                all_instructors_same_last_name = self._instructors.filter(last_name__iexact=instructor.last_name)
                course_section.instructors.add(*all_instructors_same_last_name)
            
            print(course_section)
            self._sections_saved.append(course_section.section_id)
        
        self._sections_to_save = None
    
    def load(self):
        if self._current_instructor is None:
            raise Exception("No current instructor set")
        self._load(self._current_instructor)
    
    def set_current_instructor(self, instructor: Instructor):
        self._current_instructor = instructor

    def get_extracted_sections(self) -> list[dict[str, str]] | None:
        return self._sections
    
    def get_transformed_sections(self) -> list[Tuple[Course_Section, list[str]]] | None:
        return self._sections_to_save



class InstructorScraper(OSUCourseScraper):
    """Scraper for extracting instructor information from the OSU course website, mainly used for instructors that are not in the database yet"""

    def __init__(self, 
                 term: int, 
                 department: str, 
                 url: str = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL"):
        """Initializes the InstructorScraper object with the term, department, and url to scrape from"""
        super().__init__(term, department, url)

        self._current_course: Course | None = None

        self._instructors: list[str] | None = None
        self._instructors_to_save: list[Instructor] | None = None
    
    def _send_request(self, session: requests.Session, actionStr: str, cookie: str, sessionId: str) -> requests.Response:
        data = {
            "ICAction": actionStr,
            "ICSID": sessionId,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "cookie": cookie,
        }

        if actionStr == "select_term":
            data["CLASS_SRCH_WRK2_STRM$35$"] = str(self.term)
        elif actionStr == "select_department":
            data["CLASS_SRCH_WRK2_STRM$35$"] = str(self.term)
            data["SSR_CLSRCH_WRK_SUBJECT_SRCH$1"] = self.department

        response = session.post(self.url, data=data, headers=headers)
        return response
    
    def _send_course_request(self, session: requests.Session, course: Course, cookie: str, sessionId: str) -> requests.Response:
        
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/x-www-form-urlencoded",
            "cookie": cookie,
        }

        data = {
            "ICAction": "CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH",
            "ICSID": sessionId,
            "SSR_CLSRCH_WRK_CATALOG_NBR$2": course.number,
            "SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2": "E",
            "SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$4": "N",
        }

        try: 
            response = session.post(self.url, data=data, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            return response
        
        return response
    
    def _parse_course_response(self, response: requests.Response) -> list[str]:
        soup = BeautifulSoup(response.text, 'html.parser')
        instructors_strs = []

        coursesRows = soup.select("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX2\$]")

        for row in coursesRows:
            # this find keeps making the program crash
            fullCourseTitleElement = row.find("td", {"class": "PAGROUPBOXLABELLEVEL1"})
            fullCourseTitleElement = row.select_one("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX2GP]")
            if fullCourseTitleElement is None:
                continue

            sectionRows = row.select("div[id^=win0divSSR_CLSRSLT_WRK_GROUPBOX3]")

            # print(len(sectionRows))
            for sectionRow in sectionRows:
                rowData = sectionRow.find_all("td", {"class": "PSLEVEL3GRIDODDROW"})

                instructors = rowData[4].text.replace("\n", "")

                instructors_strs.append(instructors)

        return instructors_strs
    
    def _extract(self, course: Course):
        if self._session is None or self._cookie is None or self._sessionId is None:
            raise Exception("Session is not initialized")
        
        if self._instructors is None:
            self._instructors = []
        
        self._search_session = requests.Session()
        # select the term
        response = self._send_request(self._search_session, "select_term", self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to select term")
        
        # expand search criteria
        response = self._send_request(self._search_session, "select_department", self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to expand search criteria")
        
        # search for the instructor
        response = self._send_course_request(self._search_session, course, self._cookie, self._sessionId)
        if response.status_code != 200:
            raise Exception("Unable to search for instructor")
        
        # parse the response
        self._instructors.extend(self._parse_course_response(response))

        self._search_session.close()
        self._search_session = None
    
    def _transform(self, course: Course):
        if self._instructors is None:
            raise Exception("No instructors to transform")
        
        self._instructors_to_save = []
        for instructor_str in self._instructors:
            instructor_info = instructor_str.split(",")
            if instructor_info[0].lower() != "to be announced":
                for instructor_str in instructor_info:
                    name_splits = instructor_str.split(" ")
                    first_name = name_splits[0]
                    last_name = name_splits[-1]
                    instructor_dept = course.department
                    try:
                        instructor_to_add = Instructor.objects.get(first_name=first_name, last_name=last_name, department=instructor_dept)
                    except Instructor.DoesNotExist:
                        instructor_to_add = Instructor.objects.create(first_name=first_name, last_name=last_name, department=instructor_dept)
                        self._instructors_to_save.append(instructor_to_add)
        
        self._instructors = None
    
    def _load(self, course: Course):
        if self._instructors_to_save is None:
            raise Exception("No instructors to save")
        
        for instructor in self._instructors_to_save:
            print(instructor)
            instructor.save()
        
        self._instructors_to_save = None
    
    def extract(self):
        if self._current_course is None:
            raise Exception("No current course set")
        self._extract(self._current_course)
    
    def transform(self):
        if self._current_course is None:
            raise Exception("No current course set")
        self._transform(self._current_course)
    
    def load(self):
        if self._current_course is None:
            raise Exception("No current course set")
        self._load(self._current_course)
    
    def run(self):
        self._courses = Course.objects.filter(department__short_name=self.department)

        for course in self._courses:
            self._current_course = course

            self._session, self._cookie, self._sessionId = self._create_new_session()
            
            self._extract(course)

            self._transform(course)
            # pprint(self.get_transformed_sections())
            self._load(course)
        
            self._close_session(self._session)
        self._session = None

    def set_current_course(self, course: Course):
        self._current_course = course




### Scheduling Functions for a single department ###
def search_instructors_of_courses(term: int, department: str):
    """Searches for instructor information of course sections in the department of the term by searching by instructor last name"""
    
    if not Term.objects.filter(osu_id=term).exists():
            raise Exception("Term does not exist in database")
        
    # if the department is not in the database this scheduled task fails
    if not Department.objects.filter(short_name=department).exists():
        raise Exception("Department does not exist in database")
    
    try:
        scraper = CourseInstructorScraper(term, department)
        scraper.run()
    except Exception as e:
        # write the error to the error logs
        error_message = "Error occurred while updating the sections for department: {} and term: {}".format(department, term)
        error_log = Error_Log.objects.create(error_message=error_message,
                                                stack_trace=traceback.format_exc(),
                                                function_name="search_instructors_of_courses")
        error_log.save()

def add_new_instructors(term: int, department: str):
    """Searches for instructors in the department from a previous term by going through all of the courses in the department of that term"""
    
    if not Term.objects.filter(osu_id=term).exists():
            raise Exception("Term does not exist in database")
        
    # if the department is not in the database this scheduled task fails
    if not Department.objects.filter(short_name=department).exists():
        raise Exception("Department does not exist in database")    
    
    try:
        scraper = InstructorScraper(term, department)
        scraper.run()
    except Exception as e:
        # write the error to the error logs
        error_message = "Error occurred while updating the instructors for department: {} and term: {}".format(department, term)
        error_log = Error_Log.objects.create(error_message=error_message,
                                                stack_trace=traceback.format_exc(),
                                                function_name="add_new_instructors")
        error_log.save()






### Scheduling Functions for ALL departments ###
def schedule_all_search_instructors_of_courses(term=None, start_at=None):
    """Schedules all the search_instructors_of_courses tasks for all departments and terms"""

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
                                    func='search.request_tasks.search_instructors_of_courses', 
                                    kwargs=kwargs, 
                                    schedule_type=Schedule.ONCE)

def schedule_all_add_new_instructors(term=None, start_at=None):
    """Schedules all the add_new_instructors tasks for all departments and terms"""

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
                                    func='search.request_tasks.add_new_instructors', 
                                    kwargs=kwargs, 
                                    schedule_type=Schedule.ONCE)