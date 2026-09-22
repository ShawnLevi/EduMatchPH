const STORAGE_KEYS = {
  admins: 'edumatch_demo_admins',
  currentUser: 'edumatch_admin_current_user',
  scholarships: 'edumatch_scholarships',
  shortlist: 'edumatch_shortlisted_applicants',
  currentScholarship: 'edumatch_current_scholarship',
  selectedOrg: 'edumatch_selected_org',
  adminOrganization: 'edumatch_admin_organization'
};

const ORGANIZATIONS = [
  { id: 'dost', name: 'Department of Science and Technology' },
  { id: 'uclm', name: 'University of Cebu Lapu-Lapu and Mandaue' }
];

function getOrganizations() {
  return ORGANIZATIONS;
}

function getOrganization(orgId) {
  return ORGANIZATIONS.find(o => o.id === orgId) || null;
}

function seedDemoData() {
  if (!localStorage.getItem(STORAGE_KEYS.admins)) {
    localStorage.setItem(STORAGE_KEYS.admins, JSON.stringify([
      {
        name: 'Alicia Ramos',
        email: 'admin@edumatch.ph',
        password: 'admin123',
        role: 'Scholarship Administrator',
        organization: 'uclm'
      },
      {
        name: 'Marco Villanueva',
        email: 'admin@dost.edumatch.ph',
        password: 'dost123',
        role: 'Scholarship Administrator',
        organization: 'dost'
      }
    ]));
  }

  if (!localStorage.getItem(STORAGE_KEYS.scholarships)) {
    const mockScholarships = [
      {
        id: 'uclm-academic-scholarship',
        organization: 'uclm',
        name: 'UCLM Academic Scholarship',
        provider: 'University of Cebu Lapu-Lapu and Mandaue',
        status: 'Open',
        description: 'Need-based and merit-driven support for UCLM students pursuing degree programs in good academic standing.',
        deadline: '2026-10-15',
        availableSlots: 20,
        applications: 91,
        eligibleApplicants: 61,
        minGpa: 2.5,
        eligibleCourses: ['Computer Science', 'Business Administration', 'Engineering', 'Accountancy', 'Economics'],
        incomeRequirement: 'Household income below PHP 300,000',
        locationRequirement: 'Currently enrolled at University of Cebu Lapu-Lapu and Mandaue',
        citizenshipRequirement: 'Filipino citizen',
        criteria: ['Minimum GPA requirement', 'Eligible course', 'Income requirement', 'Location requirement', 'Citizenship requirement'],
        applicants: [
          {
            id: 'app-101',
            name: 'Maria Santos',
            course: 'Computer Science',
            yearLevel: '3rd Year',
            gpa: 95.8,
            income: 180000,
            location: 'Quezon City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 1,
            rankingScore: 96.8,
            rankingFactors: [
              { name: 'Academic performance', contribution: 23, possible: 25 },
              { name: 'Course fit', contribution: 19, possible: 20 },
              { name: 'Need assessment', contribution: 17, possible: 20 },
              { name: 'Leadership record', contribution: 14, possible: 15 },
              { name: 'Community service', contribution: 11, possible: 20 }
            ]
          },
          {
            id: 'app-102',
            name: 'Juan Dela Cruz',
            course: 'Accountancy',
            yearLevel: '2nd Year',
            gpa: 92.5,
            income: 245000,
            location: 'Cebu City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 2,
            rankingScore: 94.5,
            rankingFactors: [
              { name: 'Academic performance', contribution: 22, possible: 25 },
              { name: 'Course fit', contribution: 18, possible: 20 },
              { name: 'Need assessment', contribution: 18, possible: 20 },
              { name: 'Leadership record', contribution: 12, possible: 15 },
              { name: 'Community service', contribution: 9, possible: 20 }
            ]
          },
          {
            id: 'app-103',
            name: 'Ana Reyes',
            course: 'Business Administration',
            yearLevel: '4th Year',
            gpa: 89.7,
            income: 350000,
            location: 'Davao City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Ineligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: false,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: null,
            rankingScore: null,
            rankingFactors: []
          },
          {
            id: 'app-104',
            name: 'Leo Mercado',
            course: 'Engineering',
            yearLevel: '1st Year',
            gpa: 86.2,
            income: 210000,
            location: 'Iloilo City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 5,
            rankingScore: 89.7,
            rankingFactors: [
              { name: 'Academic performance', contribution: 19, possible: 25 },
              { name: 'Course fit', contribution: 18, possible: 20 },
              { name: 'Need assessment', contribution: 17, possible: 20 },
              { name: 'Leadership record', contribution: 10, possible: 15 },
              { name: 'Community service', contribution: 9, possible: 20 }
            ]
          }
        ]
      },
      {
        id: 'uclm-presidential-scholarship',
        organization: 'uclm',
        name: 'UCLM Presidential Scholarship',
        provider: 'University of Cebu Lapu-Lapu and Mandaue',
        status: 'Review',
        description: 'Scholarship support for UCLM students with strong academic standing and active campus leadership.',
        deadline: '2026-11-20',
        availableSlots: 12,
        applications: 44,
        eligibleApplicants: 31,
        minGpa: 3.0,
        eligibleCourses: ['Computer Science', 'Engineering', 'Accounting', 'Economics'],
        incomeRequirement: 'Household income below PHP 500,000',
        locationRequirement: 'Currently enrolled at University of Cebu Lapu-Lapu and Mandaue',
        citizenshipRequirement: 'Filipino citizen',
        criteria: ['Minimum GPA requirement', 'Eligible course', 'Income requirement', 'Location requirement', 'Citizenship requirement'],
        applicants: [
          {
            id: 'app-201',
            name: 'Rhea Lim',
            course: 'Engineering',
            yearLevel: '3rd Year',
            gpa: 96.9,
            income: 280000,
            location: 'Pasay City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 1,
            rankingScore: 97.4,
            rankingFactors: [
              { name: 'Academic performance', contribution: 24, possible: 25 },
              { name: 'Course fit', contribution: 20, possible: 20 },
              { name: 'Need assessment', contribution: 15, possible: 20 },
              { name: 'Leadership record', contribution: 14, possible: 15 },
              { name: 'Community service', contribution: 13, possible: 20 }
            ]
          },
          {
            id: 'app-202',
            name: 'Bea Cruz',
            course: 'Economics',
            yearLevel: '2nd Year',
            gpa: 88.6,
            income: 520000,
            location: 'Makati City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Ineligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: false,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: null,
            rankingScore: null,
            rankingFactors: []
          }
        ]
      },
      {
        id: 'uclm-financial-assistance',
        organization: 'uclm',
        name: 'UCLM Financial Assistance Grant',
        provider: 'University of Cebu Lapu-Lapu and Mandaue',
        status: 'Open',
        description: 'Financial assistance grant for UCLM students from low-income households across any degree program.',
        deadline: '2026-12-05',
        availableSlots: 15,
        applications: 37,
        eligibleApplicants: 22,
        minGpa: 2.25,
        eligibleCourses: ['Computer Science', 'Business Administration', 'Engineering', 'Accountancy', 'Education', 'Nursing'],
        incomeRequirement: 'Household income below PHP 250,000',
        locationRequirement: 'Currently enrolled at University of Cebu Lapu-Lapu and Mandaue',
        citizenshipRequirement: 'Filipino citizen',
        criteria: ['Minimum GPA requirement', 'Eligible course', 'Income requirement', 'Location requirement', 'Citizenship requirement'],
        applicants: [
          {
            id: 'app-501',
            name: 'Nathaniel Borja',
            course: 'Nursing',
            yearLevel: '2nd Year',
            gpa: 90.3,
            income: 150000,
            location: 'Mandaue City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 1,
            rankingScore: 91.8,
            rankingFactors: [
              { name: 'Academic performance', contribution: 20, possible: 25 },
              { name: 'Course fit', contribution: 18, possible: 20 },
              { name: 'Need assessment', contribution: 19, possible: 20 },
              { name: 'Leadership record', contribution: 12, possible: 15 },
              { name: 'Community service', contribution: 14, possible: 20 }
            ]
          },
          {
            id: 'app-502',
            name: 'Jasmine Ty',
            course: 'Education',
            yearLevel: '1st Year',
            gpa: 85.6,
            income: 265000,
            location: 'Lapu-Lapu City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Ineligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: false,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: null,
            rankingScore: null,
            rankingFactors: []
          }
        ]
      },
      {
        id: 'dost-sei-merit-scholarship',
        organization: 'dost',
        name: 'DOST-SEI Merit Scholarship Program',
        provider: 'Department of Science and Technology — Science Education Institute',
        status: 'Open',
        description: 'Merit-based support for Filipino students pursuing priority science, technology, and engineering programs.',
        deadline: '2026-10-30',
        availableSlots: 25,
        applications: 68,
        eligibleApplicants: 40,
        minGpa: 2.0,
        eligibleCourses: ['Computer Science', 'Information Technology', 'Electronics Engineering', 'Civil Engineering', 'Chemistry'],
        incomeRequirement: 'Household income below PHP 400,000',
        locationRequirement: 'Any DOST-recognized higher education institution nationwide',
        citizenshipRequirement: 'Filipino citizen',
        criteria: ['Minimum GPA requirement', 'Eligible course', 'Income requirement', 'Location requirement', 'Citizenship requirement'],
        applicants: [
          {
            id: 'app-301',
            name: 'Kristine Abad',
            course: 'Computer Science',
            yearLevel: '2nd Year',
            gpa: 97.2,
            income: 250000,
            location: 'Cebu City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 1,
            rankingScore: 98.1,
            rankingFactors: [
              { name: 'Academic performance', contribution: 25, possible: 25 },
              { name: 'Course fit', contribution: 20, possible: 20 },
              { name: 'Need assessment', contribution: 16, possible: 20 },
              { name: 'Leadership record', contribution: 13, possible: 15 },
              { name: 'Community service', contribution: 12, possible: 20 }
            ]
          },
          {
            id: 'app-302',
            name: 'Paolo Ignacio',
            course: 'Electronics Engineering',
            yearLevel: '1st Year',
            gpa: 84.0,
            income: 420000,
            location: 'Mandaue City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Ineligible',
            screening: {
              minimumGpa: false,
              eligibleCourse: true,
              incomeRequirement: false,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: null,
            rankingScore: null,
            rankingFactors: []
          }
        ]
      },
      {
        id: 'dost-rise-scholarship',
        organization: 'dost',
        name: 'DOST RA 7687 S&T Undergraduate Scholarship',
        provider: 'Department of Science and Technology',
        status: 'Review',
        description: 'Undergraduate scholarship support under RA 7687 for students pursuing CHED-recognized science and technology programs.',
        deadline: '2026-11-10',
        availableSlots: 18,
        applications: 52,
        eligibleApplicants: 29,
        minGpa: 1.9,
        eligibleCourses: ['Civil Engineering', 'Chemistry', 'Biology', 'Information Technology'],
        incomeRequirement: 'Household income below PHP 350,000',
        locationRequirement: 'Nationwide, priority for CHED-recognized STEM programs',
        citizenshipRequirement: 'Filipino citizen',
        criteria: ['Minimum GPA requirement', 'Eligible course', 'Income requirement', 'Location requirement', 'Citizenship requirement'],
        applicants: [
          {
            id: 'app-401',
            name: 'Diego Fernandez',
            course: 'Civil Engineering',
            yearLevel: '3rd Year',
            gpa: 91.4,
            income: 190000,
            location: 'Lapu-Lapu City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 1,
            rankingScore: 93.6,
            rankingFactors: [
              { name: 'Academic performance', contribution: 22, possible: 25 },
              { name: 'Course fit', contribution: 19, possible: 20 },
              { name: 'Need assessment', contribution: 18, possible: 20 },
              { name: 'Leadership record', contribution: 12, possible: 15 },
              { name: 'Community service', contribution: 10, possible: 20 }
            ]
          },
          {
            id: 'app-402',
            name: 'Samantha Uy',
            course: 'Biology',
            yearLevel: '4th Year',
            gpa: 88.9,
            income: 300000,
            location: 'Talisay City',
            citizenship: 'Filipino',
            eligibilityStatus: 'Eligible',
            screening: {
              minimumGpa: true,
              eligibleCourse: true,
              incomeRequirement: true,
              locationRequirement: true,
              citizenshipRequirement: true
            },
            rank: 2,
            rankingScore: 90.2,
            rankingFactors: [
              { name: 'Academic performance', contribution: 20, possible: 25 },
              { name: 'Course fit', contribution: 17, possible: 20 },
              { name: 'Need assessment', contribution: 17, possible: 20 },
              { name: 'Leadership record', contribution: 11, possible: 15 },
              { name: 'Community service', contribution: 9, possible: 20 }
            ]
          }
        ]
      }
    ];

    localStorage.setItem(STORAGE_KEYS.scholarships, JSON.stringify(mockScholarships));
  }

  if (!localStorage.getItem(STORAGE_KEYS.shortlist)) {
    localStorage.setItem(STORAGE_KEYS.shortlist, JSON.stringify([]));
  }
}

// Unscoped by design: authenticating a login attempt has to look an admin up by
// email across every organization BEFORE any organization context exists. Nothing
// that displays data to an already-logged-in admin should ever call this directly —
// use the org-scoped helpers below instead.
function getAdmins() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.admins)) || [];
  } catch (e) {
    return [];
  }
}

function getAllScholarships() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.scholarships)) || [];
  } catch (e) {
    return [];
  }
}

function getScholarships() {
  const org = getAdminOrganizationId();
  if (!org) return [];
  return getAllScholarships().filter(scholarship => scholarship.organization === org);
}

function getCurrentScholarshipId() {
  const scholarships = getScholarships();
  const current = localStorage.getItem(STORAGE_KEYS.currentScholarship);
  if (current && scholarships.some(item => item.id === current)) {
    return current;
  }
  return (scholarships[0] && scholarships[0].id) || '';
}

function setCurrentScholarship(id) {
  localStorage.setItem(STORAGE_KEYS.currentScholarship, id);
}

function getScholarship(id) {
  const scholarships = getScholarships();
  if (!id) {
    return scholarships[0] || null;
  }
  return scholarships.find(item => item.id === id) || null;
}

function getApplicants(scholarshipId = getCurrentScholarshipId()) {
  const scholarship = getScholarship(scholarshipId);
  return scholarship ? (scholarship.applicants || []) : [];
}

function getEligibleApplicants(scholarshipId = getCurrentScholarshipId()) {
  return getApplicants(scholarshipId).filter(applicant => applicant.eligibilityStatus === 'Eligible');
}

function getRanking(scholarshipId = getCurrentScholarshipId()) {
  const scholarship = getScholarship(scholarshipId);
  if (!scholarship) return [];

  const eligibleApplicants = getEligibleApplicants(scholarshipId)
    .map(applicant => ({
      ...applicant,
      rank: applicant.rank || 0,
      rankingScore: applicant.rankingScore || 0
    }))
    .sort((a, b) => (a.rank || Number.MAX_SAFE_INTEGER) - (b.rank || Number.MAX_SAFE_INTEGER));

  return eligibleApplicants;
}

function getApplicantDetails(applicantId) {
  const scholarships = getScholarships();
  for (const scholarship of scholarships) {
    const applicant = (scholarship.applicants || []).find(item => item.id === applicantId);
    if (applicant) return applicant;
  }
  return null;
}

function getAllShortlistEntries() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.shortlist) || '[]');
  } catch (e) {
    return [];
  }
}

function shortlistApplicant(applicantId, scholarshipId = getCurrentScholarshipId()) {
  const org = getAdminOrganizationId();
  if (!org) return [];

  const shortlist = getAllShortlistEntries();
  const alreadyAdded = shortlist.some(item => item.applicantId === applicantId && item.scholarshipId === scholarshipId);

  if (!alreadyAdded) {
    const applicant = getApplicantDetails(applicantId) || getApplicants(scholarshipId).find(item => item.id === applicantId);
    if (applicant) {
      shortlist.push({
        applicantId,
        scholarshipId,
        organization: org,
        applicantName: applicant.name,
        scholarshipName: getScholarship(scholarshipId)?.name || 'Scholarship',
        rank: applicant.rank || 'Pending',
        rankingScore: applicant.rankingScore || 'N/A',
        eligibilityStatus: applicant.eligibilityStatus || 'Pending',
        dateShortlisted: new Date().toISOString().slice(0, 10)
      });
      localStorage.setItem(STORAGE_KEYS.shortlist, JSON.stringify(shortlist));
    }
  }

  return shortlist.filter(item => item.organization === org);
}

function compareApplicants(applicantIds = []) {
  if (!Array.isArray(applicantIds) || applicantIds.length === 0) return [];

  const applicants = getScholarships().flatMap(scholarship => (scholarship.applicants || []).filter(applicant => applicantIds.includes(applicant.id)));
  return applicants;
}

function screenApplicant(applicantId, scholarshipId = getCurrentScholarshipId()) {
  const scholarship = getScholarship(scholarshipId);
  if (!scholarship) return null;

  const applicant = (scholarship.applicants || []).find(item => item.id === applicantId);
  if (!applicant) return null;

  const screening = applicant.screening || {};
  const isEligible = Object.values(screening).every(Boolean);
  applicant.eligibilityStatus = isEligible ? 'Eligible' : 'Ineligible';

  const updatedScholarships = getAllScholarships().map(item => {
    if (item.id !== scholarshipId) return item;
    return {
      ...item,
      applicants: (item.applicants || []).map(current => current.id === applicantId ? applicant : current)
    };
  });

  localStorage.setItem(STORAGE_KEYS.scholarships, JSON.stringify(updatedScholarships));
  return applicant;
}

function getShortlist() {
  const org = getAdminOrganizationId();
  if (!org) return [];
  return getAllShortlistEntries().filter(item => item.organization === org);
}

// --- Session / organization context -----------------------------------------
// edumatch_selected_org (sessionStorage): which organization's login screen is
// showing, set on org-select.html BEFORE any credentials are verified.
// edumatch_admin_organization (sessionStorage): the organization the CURRENTLY
// AUTHENTICATED admin actually belongs to, set only after a successful login.
// All data scoping must use edumatch_admin_organization, never the selected-org
// value — otherwise picking an organization from the list would expose its data
// without ever logging in.

function getSelectedOrganizationId() {
  try {
    return sessionStorage.getItem(STORAGE_KEYS.selectedOrg) || null;
  } catch (e) {
    return null;
  }
}

function setSelectedOrganizationId(orgId) {
  sessionStorage.setItem(STORAGE_KEYS.selectedOrg, orgId);
}

function getAdminOrganizationId() {
  try {
    return sessionStorage.getItem(STORAGE_KEYS.adminOrganization) || null;
  } catch (e) {
    return null;
  }
}

function setAdminOrganizationId(orgId) {
  sessionStorage.setItem(STORAGE_KEYS.adminOrganization, orgId);
}

function hasValidAdminSession() {
  return Boolean(localStorage.getItem(STORAGE_KEYS.currentUser) && getAdminOrganizationId());
}

function completeAdminLogin(email, orgId) {
  localStorage.setItem(STORAGE_KEYS.currentUser, email);
  setAdminOrganizationId(orgId);
}

function clearAdminSession() {
  localStorage.removeItem(STORAGE_KEYS.currentUser);
  localStorage.removeItem(STORAGE_KEYS.currentScholarship);
  try {
    sessionStorage.removeItem(STORAGE_KEYS.adminOrganization);
    sessionStorage.removeItem(STORAGE_KEYS.selectedOrg);
  } catch (e) {
    // ignore
  }
}

function initAdminSession() {
  const hasStoredUser = Boolean(localStorage.getItem(STORAGE_KEYS.currentUser));
  const validSession = hasValidAdminSession();

  if (hasStoredUser && !validSession) {
    clearAdminSession();
  }

  const protectedPages = [
    'dashboard.html',
    'scholarships.html',
    'applicants.html',
    'applicant-details.html',
    'ranking.html',
    'saved.html',
    'matches.html',
    'profile.html'
  ];

  if (!validSession && protectedPages.some(page => window.location.pathname.endsWith(page))) {
    window.location.href = 'index.html';
  }
}

seedDemoData();

if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    initAdminSession();

    document.querySelectorAll('[data-logout]').forEach(button => {
      button.addEventListener('click', () => {
        clearAdminSession();
        window.location.href = 'index.html';
      });
    });
  });
}
