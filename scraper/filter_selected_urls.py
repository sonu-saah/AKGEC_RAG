
import json
from pathlib import Path

# Load discovered navigation URLs
input_file = Path("data/navigation_urls.json")
output_file = Path("data/selected_urls.json")

with open(input_file, "r", encoding="utf-8") as file:
    pages = json.load(file)

# Only user-approved navigation topics
selected_titles = {
    "Vision And Mission",
    "Director",
    "Management",
    "Important Functionaries",
    "NBA Accreditation",
    "Approvals by Statutory Bodies",
    "AICTE Approval Letters",
    "Grievance Committee",
    "Library",
    "Hostel",
    "Centres Of Excellence",
    "College Canteen",

    "Applied Sciences & Humanities",
    "Civil Engineering",
    "Computer Science and Engineering",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "Information Technology",
    "Mechanical Engineering",
    "Master of Computer Applications",

    "Academic Calendar",
    "List of Holidays",
    "Issuance of certificates for passout students",

    "Courses Offered",
    "Fee Structure for Existing Students",
    "Fee Structure for New Students",
    "Fee Refund Norms",
    "Scholarship",

    "Mediclaim",
    "College Awards",
    "Faculty Achievements",

    "T&P Department",
    "Our Recruiters",
    "Placement Records",
    "Placement Highlights",
    "T&P Programmes",

    "About VE Cell",
    "CAREER",
}

# Sections where all listed navigation children are approved
societies = {
    "Conatus", "Nirmaan", "Oorja", "Phoenix",
    "Samveg", "Euphony", "Footprints", "Horizon",
    "Goonj", "Renaissance", "Taal", "Verve",
    "Photography and Media Club", "Sports Club",
    "CSI", "Indian Concrete Institute",
    "Robotics Club", "IEEE", "ISTE", "SAE India",
    "Electronics Club", "Communication Club",
}

selected_titles.update(societies)
selected_titles.add("Events")

# VE Cell activities from the discovered navigation
ve_activities = {
    "Transformative Sharing",
    "Participation in Societal Development",
    "Upcoming Events",
    "Faculty/Staff Development Programs (FDPs/SDPs)",
    "Student Development Programs (SDPs)",
    "Student Induction Program",
    "UHV Departmental Seminars",
    "Guest Lectures/Webinars",
    "Extension Activities",
    "Teachers Orientation Program",
}

selected_titles.update(ve_activities)

selected = [
    page for page in pages
    if page["title"].strip() in selected_titles
]

output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(selected, file, indent=2, ensure_ascii=False)

found_titles = {page["title"].strip() for page in selected}
missing = sorted(selected_titles - found_titles)

print("===== FILTER REPORT =====")
print("Original URLs:", len(pages))
print("Selected URLs:", len(selected))
print("Missing navigation titles:", len(missing))
print("Saved to:", output_file)

print("\n===== MISSING TITLES =====")
for title in missing:
    print("-", title)
