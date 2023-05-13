import requests
from pprint import pprint
from bs4 import BeautifulSoup
from tqdm import tqdm
import json

def getCourses():
    departments = getDepartmentShortNames()
    # oldDepartments = ["AEE", "BUSMGT", "CHBE"]
    page = requests.get("https://osuprofs.com/search/?search=+")
    soup = BeautifulSoup(page.content, 'html.parser')
    all_courses = soup.find_all(name="a", attrs={"class": "list-group-item list-group-item-action"})

    # print(all_courses[0].contents[0].strip()) # how to get class dept + number
    # print(all_courses[0].contents[1].contents[0].strip()) # how to get class official name

    model = "search.course"
    list_of_courses = []

    # name, department, number, description
    counter = 1
    for course in all_courses:
        pk = counter
        department_and_number = course.contents[0].strip()
        if department_and_number == "CSE SP 22":
            continue
        # print(department_and_number)
        if len(course.contents) < 3 or len(course.contents[1].contents) < 1:
            name = department_and_number
        else:
            # print(course.contents[1])
            name = course.contents[1].contents[0].strip()
        dept, number = department_and_number.split(" ")
        if dept not in departments:
            continue
        description = "description"
        fields = {"name": name, "department": [dept], "number": number, "description": description}
        fixture_item = {"model": model, "pk": pk, "fields": fields}
        list_of_courses.append(fixture_item)
        counter += 1

    return list_of_courses

# instructor is a tuple: (first_name, last_name, department)
# list_of_instructors is a list of instructor tuples
def isInstructorUnique(list_of_instructors, instructor):
    for i in list_of_instructors:
        if i[0] == instructor[0] and i[1] == instructor[1] and i[2] == instructor[2]:
            return False
    return True


def getProfessors(limit=10000):
    courses = getCourses()

    base_url = "https://osuprofs.com/courses/"
    
    counter = 0

    # used for isInstructorUnique
    set_of_instructors = set()

    # used to return (list of dictionaries)
    list_of_professors = []
    # make a progress bar for this for loop
    for course in tqdm(courses):
        if counter == limit:
            break
        fields = course["fields"]
        dept = fields["department"][0]
        number = fields["number"]

        url = base_url + dept + "/" + number
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        instructors = soup.find_all(name="div", attrs={"class": "card-body"})
        for instructor in instructors:
            name_element = instructor.find(name="h5", attrs={"class": "card-title"})
            name = name_element.text.strip()
            names = name.split(" ")
            first_name = names[0]
            last_name = names[-1]

            if (first_name, last_name, dept) in set_of_instructors:
                continue
            else:
                set_of_instructors.add((first_name, last_name, dept))

            fields = {"first_name": first_name, "last_name": last_name, "department": [dept]}
            fixture_item = {"model": "search.instructor", "pk": len(list_of_professors) + 1, "fields": fields}
            list_of_professors.append(fixture_item)
        
        counter += 1
            
    return list_of_professors


def getDepartments():
    url = "https://courses.osu.edu/psc/csosuct/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.osu.edu%2fpsp%2fcsosuct%2f&PortalURI=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    subject_select = soup.find(name="select", attrs={"id": "SSR_CLSRCH_WRK_SUBJECT_SRCH$1"})
    all_departments = subject_select.find_all(name="option") # type: ignore

    model = "search.department"
    list_of_departments = []

    counter = 1
    for department in all_departments:
        pk = counter
        name = department.contents[0].strip()
        short_name = department['value']
        if name == "" and short_name == "":
            continue

        fields = {"name": name, "short_name": short_name}
        fixture_item = {"model": model, "pk": pk, "fields": fields}
        list_of_departments.append(fixture_item)
        counter += 1

    return list_of_departments

def getDepartmentShortNames():
    url = "https://courses.osu.edu/psc/csosuct/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.osu.edu%2fpsp%2fcsosuct%2f&PortalURI=https%3a%2f%2fcourses.osu.edu%2fpsc%2fcsosuct%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    subject_select = soup.find(name="select", attrs={"id": "SSR_CLSRCH_WRK_SUBJECT_SRCH$1"})
    all_departments = subject_select.find_all(name="option") # type: ignore

    short_names = []
    for department in all_departments:
        name = department.contents[0].strip()
        short_name = department['value']
        if name == "" and short_name == "":
            continue
        short_names.append(short_name)
    
    return short_names
    # returns only the strings of the department short_names

def main():
    all_courses = getCourses()
    # pprint(all_courses)
    # print()
    # print()
    with open("fixtures/search/courses.json", "w") as f:
        json.dump(all_courses, f)
    
    all_departments = getDepartments()
    # pprint(all_departments)
    with open("fixtures/search/departments.json", "w") as f:
        json.dump(all_departments, f)

    all_professors = getProfessors()
    # pprint(all_professors)
    with open("fixtures/search/professors.json", "w") as f:
        json.dump(all_professors, f)

    

if __name__ == "__main__":
    main()