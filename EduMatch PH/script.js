const STORAGE_KEYS = {
  admins: 'edumatch_demo_admins',
  currentUser: 'edumatch_admin_current_user',
  scholarships: 'edumatch_scholarships',
  shortlist: 'edumatch_shortlisted_applicants',
  currentScholarship: 'edumatch_current_scholarship'
};

function seedDemoData() {
  if (!localStorage.getItem(STORAGE_KEYS.admins)) {
    localStorage.setItem(STORAGE_KEYS.admins, JSON.stringify([
      {
        name: 'Alicia Ramos',
        email: 'admin@edumatch.ph',
        password: 'admin123',
        role: 'Scholarship Administrator'
      }
    ]));
  }

  if (!localStorage.getItem(STORAGE_KEYS.scholarships)) {
    const mockScholarships = [
      {
        id: 'sm-foundation',
        name: 'SM Foundation College Scholarship',
        provider: 'SM Foundation',
        status: 'Open',
        description: 'Need-based and merit-driven support for Filipino college students pursuing degree programs in accredited institutions.',
        deadline: '2026-10-15',
        availableSlots: 20,
        applications: 91,
        eligibleApplicants: 61,
        minGpa: 2.5,
        eligibleCourses: ['Computer Science', 'Business Administration', 'Engineering', 'Accountancy', 'Economics'],
        incomeRequirement: 'Household income below PHP 300,000',
        locationRequirement: 'Metro Manila, Cebu, Davao, or provincial partner areas',
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
        id: 'dlsu-scholarship',
        name: 'DLSU Merit Grant',
        provider: 'De La Salle University',
        status: 'Review',
        description: 'Scholarship support for students with strong academic standing and active campus leadership.',
        deadline: '2026-11-20',
        availableSlots: 12,
        applications: 44,
        eligibleApplicants: 31,
        minGpa: 3.0,
        eligibleCourses: ['Computer Science', 'Engineering', 'Accounting', 'Economics'],
        incomeRequirement: 'Household income below PHP 500,000',
        locationRequirement: 'Metro Manila or recognized partner school network',
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
      }
    ];

    localStorage.setItem(STORAGE_KEYS.scholarships, JSON.stringify(mockScholarships));
  }

  if (!localStorage.getItem(STORAGE_KEYS.shortlist)) {
    localStorage.setItem(STORAGE_KEYS.shortlist, JSON.stringify([]));
  }
}

function getAdmins() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.admins)) || [];
  } catch (e) {
    return [];
  }
}

function getScholarships() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.scholarships)) || [];
  } catch (e) {
    return [];
  }
}

function getCurrentScholarshipId() {
  const current = localStorage.getItem(STORAGE_KEYS.currentScholarship);
  return current || (getScholarships()[0] && getScholarships()[0].id) || '';
}

function setCurrentScholarship(id) {
  localStorage.setItem(STORAGE_KEYS.currentScholarship, id);
}

function getScholarship(id = getCurrentScholarshipId()) {
  return getScholarships().find(item => item.id === id) || getScholarships()[0] || null;
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
  const applicants = getScholarships().flatMap(scholarship => scholarship.applicants || []);
  return applicants.find(applicant => applicant.id === applicantId) || null;
}

function shortlistApplicant(applicantId, scholarshipId = getCurrentScholarshipId()) {
  const shortlist = JSON.parse(localStorage.getItem(STORAGE_KEYS.shortlist) || '[]');
  const alreadyAdded = shortlist.some(item => item.applicantId === applicantId && item.scholarshipId === scholarshipId);
  if (alreadyAdded) return shortlist;

  const applicant = getApplicantDetails(applicantId) || getApplicants(scholarshipId).find(item => item.id === applicantId);
  if (!applicant) return shortlist;

  shortlist.push({
    applicantId,
    scholarshipId,
    applicantName: applicant.name,
    scholarshipName: getScholarship(scholarshipId)?.name || 'Scholarship',
    rank: applicant.rank || 'Pending',
    rankingScore: applicant.rankingScore || 'N/A',
    eligibilityStatus: applicant.eligibilityStatus || 'Pending',
    dateShortlisted: new Date().toISOString().slice(0, 10)
  });

  localStorage.setItem(STORAGE_KEYS.shortlist, JSON.stringify(shortlist));
  return shortlist;
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

  const updatedScholarships = getScholarships().map(item => {
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
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.shortlist) || '[]');
  } catch (e) {
    return [];
  }
}

function setAdminSession(email) {
  localStorage.setItem(STORAGE_KEYS.currentUser, email);
}

function clearAdminSession() {
  localStorage.removeItem(STORAGE_KEYS.currentUser);
}

function initAdminSession() {
  const currentUser = localStorage.getItem(STORAGE_KEYS.currentUser);
  if (!currentUser) {
    if (window.location.pathname.endsWith('dashboard.html') || window.location.pathname.endsWith('scholarships.html') || window.location.pathname.endsWith('applicants.html') || window.location.pathname.endsWith('applicant-details.html') || window.location.pathname.endsWith('ranking.html') || window.location.pathname.endsWith('saved.html') || window.location.pathname.endsWith('profile.html')) {
      window.location.href = 'index.html';
    }
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
