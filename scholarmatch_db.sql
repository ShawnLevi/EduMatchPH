-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 31, 2026 at 10:40 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `scholarmatch_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `course_category` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `course_category`) VALUES
(1, 'BS Accountancy', 'Business & Management'),
(2, 'BS Business Administration', 'Business & Management'),
(3, 'BS Commerce', 'Business & Management'),
(4, 'BS Customs Administration', 'Business & Management'),
(5, 'BS Legal Management', 'Business & Management'),
(6, 'BS Computer Science', 'Computing & Information Technology'),
(7, 'BS Information Technology', 'Computing & Information Technology'),
(8, 'BS Information Management', 'Computing & Information Technology'),
(9, '3-Year Diploma in Applied AI Technology', 'Computing & Information Technology'),
(10, 'BS Computer Engineering', 'Engineering'),
(11, 'BS Civil Engineering', 'Engineering'),
(12, 'BS Electrical Engineering', 'Engineering'),
(13, 'BS Electronics and Communications Engineering', 'Engineering'),
(14, 'BS Industrial Engineering', 'Engineering'),
(15, 'BS Mechanical Engineering', 'Engineering'),
(16, 'BS Naval Architecture and Marine Engineering', 'Engineering'),
(17, 'BS Metallurgical Engineering', 'Engineering'),
(18, '3-Year Diploma in Computer Engineering Technology', 'Engineering'),
(19, 'Elementary Education (BEEd)', 'Education'),
(20, 'Secondary Education (BSEd)', 'Education'),
(21, 'BS Nursing', 'Health Sciences'),
(22, 'BS Pharmacy', 'Health Sciences'),
(23, 'BS Radiologic Technology', 'Health Sciences'),
(24, 'BS Physical Therapy', 'Health Sciences'),
(25, 'BS Nutrition and Dietetics', 'Health Sciences'),
(26, 'BS Hotel and Restaurant Management', 'Hospitality & Tourism'),
(27, 'BS Tourism', 'Hospitality & Tourism'),
(28, 'BS Criminology', 'Public Safety & Security'),
(29, 'BS Public Administration', 'Public Service & Governance'),
(30, 'BS Marine Transportation', 'Maritime'),
(31, 'BS Marine Engineering', 'Maritime'),
(32, 'AB English', 'Social Sciences & Humanities'),
(33, 'AB Political Science', 'Social Sciences & Humanities'),
(34, 'Industrial Psychology', 'Social Sciences & Humanities'),
(35, 'BS Psychology', 'Social Sciences & Humanities'),
(36, 'Law', 'Law');

-- --------------------------------------------------------

--
-- Table structure for table `course_tags`
--

CREATE TABLE `course_tags` (
  `course_id` int(11) NOT NULL,
  `tag_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `course_tags`
--

INSERT INTO `course_tags` (`course_id`, `tag_id`) VALUES
(1, 22),
(1, 25),
(1, 26),
(1, 27),
(1, 28),
(1, 84),
(1, 87),
(1, 89),
(1, 90),
(2, 22),
(2, 23),
(2, 24),
(2, 26),
(2, 28),
(2, 87),
(2, 90),
(2, 91),
(2, 92),
(2, 93),
(3, 22),
(3, 23),
(3, 24),
(3, 26),
(3, 28),
(3, 29),
(3, 30),
(3, 31),
(3, 90),
(3, 92),
(4, 22),
(4, 28),
(4, 29),
(4, 30),
(4, 31),
(4, 32),
(4, 47),
(4, 48),
(4, 69),
(4, 87),
(4, 89),
(5, 22),
(5, 47),
(5, 48),
(5, 50),
(5, 57),
(5, 58),
(5, 59),
(5, 61),
(5, 79),
(5, 87),
(5, 89),
(5, 90),
(6, 1),
(6, 2),
(6, 5),
(6, 6),
(6, 7),
(6, 11),
(6, 84),
(6, 87),
(6, 88),
(6, 89),
(7, 1),
(7, 2),
(7, 3),
(7, 4),
(7, 7),
(7, 8),
(7, 9),
(7, 10),
(7, 11),
(7, 88),
(8, 1),
(8, 2),
(8, 7),
(8, 10),
(8, 11),
(8, 22),
(8, 87),
(8, 88),
(8, 90),
(9, 1),
(9, 5),
(9, 6),
(9, 11),
(9, 12),
(9, 16),
(9, 84),
(9, 87),
(9, 88),
(9, 89),
(10, 1),
(10, 5),
(10, 9),
(10, 11),
(10, 12),
(10, 15),
(10, 16),
(10, 84),
(10, 88),
(10, 89),
(11, 12),
(11, 13),
(11, 14),
(11, 21),
(11, 84),
(11, 87),
(11, 88),
(11, 89),
(12, 11),
(12, 12),
(12, 15),
(12, 16),
(12, 84),
(12, 87),
(12, 88),
(12, 89),
(13, 9),
(13, 11),
(13, 12),
(13, 15),
(13, 16),
(13, 84),
(13, 88),
(13, 89),
(14, 12),
(14, 18),
(14, 19),
(14, 22),
(14, 30),
(14, 31),
(14, 84),
(14, 87),
(14, 88),
(14, 90),
(15, 12),
(15, 17),
(15, 19),
(15, 20),
(15, 84),
(15, 87),
(15, 88),
(15, 89),
(16, 12),
(16, 13),
(16, 62),
(16, 64),
(16, 67),
(16, 68),
(16, 84),
(16, 87),
(16, 88),
(17, 12),
(17, 18),
(17, 19),
(17, 21),
(17, 84),
(17, 87),
(17, 88),
(17, 89),
(18, 1),
(18, 9),
(18, 11),
(18, 12),
(18, 15),
(18, 16),
(18, 84),
(18, 88),
(19, 42),
(19, 43),
(19, 44),
(19, 45),
(19, 46),
(19, 79),
(19, 87),
(19, 89),
(19, 91),
(19, 93),
(20, 42),
(20, 43),
(20, 45),
(20, 46),
(20, 77),
(20, 79),
(20, 87),
(20, 89),
(20, 91),
(20, 93),
(21, 33),
(21, 34),
(21, 40),
(21, 41),
(21, 83),
(21, 87),
(21, 89),
(21, 92),
(21, 93),
(22, 33),
(22, 35),
(22, 40),
(22, 41),
(22, 83),
(22, 84),
(22, 87),
(22, 89),
(22, 90),
(23, 33),
(23, 37),
(23, 41),
(23, 83),
(23, 84),
(23, 87),
(23, 89),
(23, 90),
(24, 33),
(24, 38),
(24, 40),
(24, 41),
(24, 83),
(24, 87),
(24, 89),
(24, 92),
(24, 93),
(25, 33),
(25, 39),
(25, 40),
(25, 41),
(25, 83),
(25, 84),
(25, 87),
(25, 89),
(26, 22),
(26, 70),
(26, 72),
(26, 73),
(26, 74),
(26, 75),
(26, 76),
(26, 79),
(26, 91),
(26, 93),
(27, 22),
(27, 70),
(27, 71),
(27, 72),
(27, 76),
(27, 79),
(27, 91),
(27, 93),
(28, 47),
(28, 48),
(28, 52),
(28, 53),
(28, 54),
(28, 55),
(28, 56),
(28, 57),
(28, 87),
(28, 89),
(28, 91),
(29, 47),
(29, 48),
(29, 49),
(29, 50),
(29, 51),
(29, 52),
(29, 79),
(29, 87),
(29, 89),
(29, 91),
(30, 30),
(30, 62),
(30, 63),
(30, 65),
(30, 66),
(30, 67),
(30, 69),
(30, 88),
(30, 91),
(30, 92),
(30, 93),
(31, 12),
(31, 15),
(31, 17),
(31, 62),
(31, 64),
(31, 65),
(31, 67),
(31, 84),
(31, 87),
(31, 88),
(31, 89),
(32, 43),
(32, 77),
(32, 78),
(32, 79),
(32, 80),
(32, 81),
(32, 82),
(32, 87),
(32, 89),
(32, 90),
(33, 47),
(33, 48),
(33, 50),
(33, 51),
(33, 52),
(33, 57),
(33, 58),
(33, 61),
(33, 79),
(33, 87),
(33, 91),
(34, 33),
(34, 52),
(34, 61),
(34, 79),
(34, 87),
(34, 89),
(34, 90),
(34, 91),
(34, 93),
(34, 97),
(35, 33),
(35, 40),
(35, 41),
(35, 52),
(35, 61),
(35, 79),
(35, 87),
(35, 89),
(35, 90),
(35, 97),
(36, 47),
(36, 48),
(36, 50),
(36, 51),
(36, 57),
(36, 58),
(36, 59),
(36, 60),
(36, 61),
(36, 79),
(36, 87),
(36, 89),
(36, 90);

-- --------------------------------------------------------

--
-- Table structure for table `scholarships`
--

CREATE TABLE `scholarships` (
  `scholarship_id` int(11) NOT NULL,
  `scholarship_name` varchar(150) NOT NULL,
  `provider` varchar(150) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `minimum_gpa` decimal(3,2) DEFAULT NULL,
  `income_requirement` decimal(10,2) DEFAULT NULL,
  `location_requirement` varchar(100) DEFAULT NULL,
  `citizenship_requirement` varchar(100) DEFAULT NULL,
  `academic_requirements` text DEFAULT NULL,
  `required_documents` text DEFAULT NULL,
  `benefits` text DEFAULT NULL,
  `application_deadline` date DEFAULT NULL,
  `application_start_date` date DEFAULT NULL,
  `application_end_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `scholarship_courses`
--

CREATE TABLE `scholarship_courses` (
  `scholarship_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `scholarship_tags`
--

CREATE TABLE `scholarship_tags` (
  `scholarship_id` int(11) NOT NULL,
  `tag_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `scholarship_year_levels`
--

CREATE TABLE `scholarship_year_levels` (
  `scholarship_id` int(11) NOT NULL,
  `year_level_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tags`
--

CREATE TABLE `tags` (
  `tag_id` int(11) NOT NULL,
  `tag_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tags`
--

INSERT INTO `tags` (`tag_id`, `tag_name`) VALUES
(25, 'Accounting'),
(90, 'Analytical Thinking'),
(14, 'Architecture'),
(5, 'Artificial Intelligence'),
(20, 'Automotive Technology'),
(27, 'Banking'),
(22, 'Business Management'),
(44, 'Child Development'),
(28, 'Commerce'),
(79, 'Communication'),
(92, 'Communication Skills'),
(52, 'Community Development'),
(11, 'Computer Technology'),
(13, 'Construction'),
(82, 'Creative Arts'),
(55, 'Criminology'),
(89, 'Critical Thinking'),
(75, 'Culinary Arts'),
(45, 'Curriculum Development'),
(96, 'Customer Service'),
(32, 'Customs'),
(8, 'Cybersecurity'),
(6, 'Data Science'),
(7, 'Database Management'),
(43, 'Education'),
(46, 'Educational Technology'),
(15, 'Electrical Systems'),
(16, 'Electronics'),
(12, 'Engineering'),
(77, 'English'),
(23, 'Entrepreneurship'),
(86, 'Environmental Management'),
(85, 'Environmental Science'),
(76, 'Event Management'),
(26, 'Finance'),
(74, 'Food Service'),
(56, 'Forensics'),
(50, 'Governance'),
(48, 'Government'),
(33, 'Healthcare'),
(70, 'Hospitality'),
(73, 'Hotel Management'),
(61, 'Human Rights'),
(18, 'Industrial Technology'),
(10, 'Information Systems'),
(29, 'International Trade'),
(57, 'Law'),
(54, 'Law Enforcement'),
(91, 'Leadership'),
(59, 'Legal Management'),
(60, 'Legal Research'),
(58, 'Legal Studies'),
(80, 'Literature'),
(30, 'Logistics'),
(19, 'Manufacturing'),
(64, 'Marine Engineering'),
(63, 'Marine Transportation'),
(62, 'Maritime'),
(24, 'Marketing'),
(21, 'Materials Science'),
(84, 'Mathematics'),
(17, 'Mechanical Systems'),
(81, 'Media'),
(36, 'Medical Laboratory'),
(4, 'Mobile App Development'),
(68, 'Naval Architecture'),
(65, 'Navigation'),
(9, 'Networking'),
(34, 'Nursing'),
(39, 'Nutrition'),
(41, 'Patient Care'),
(35, 'Pharmacy'),
(38, 'Physical Therapy'),
(51, 'Politics'),
(88, 'Problem Solving'),
(1, 'Programming'),
(97, 'Psychology'),
(49, 'Public Administration'),
(40, 'Public Health'),
(53, 'Public Safety'),
(47, 'Public Service'),
(37, 'Radiologic Technology'),
(87, 'Research'),
(83, 'Science'),
(66, 'Seafaring'),
(67, 'Ship Operations'),
(2, 'Software Development'),
(31, 'Supply Chain'),
(42, 'Teaching'),
(93, 'Teamwork'),
(95, 'Technology'),
(94, 'Telecommunications'),
(71, 'Tourism'),
(69, 'Transportation'),
(72, 'Travel'),
(3, 'Web Development'),
(78, 'Writing');

-- --------------------------------------------------------

--
-- Table structure for table `year_levels`
--

CREATE TABLE `year_levels` (
  `year_level_id` int(11) NOT NULL,
  `year_level_name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `year_levels`
--

INSERT INTO `year_levels` (`year_level_id`, `year_level_name`) VALUES
(1, '1st Year'),
(2, '2nd Year'),
(3, '3rd Year'),
(4, '4th Year'),
(5, '5th Year'),
(6, 'Graduate');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD UNIQUE KEY `course_name` (`course_name`);

--
-- Indexes for table `course_tags`
--
ALTER TABLE `course_tags`
  ADD PRIMARY KEY (`course_id`,`tag_id`),
  ADD KEY `tag_id` (`tag_id`);

--
-- Indexes for table `scholarships`
--
ALTER TABLE `scholarships`
  ADD PRIMARY KEY (`scholarship_id`);

--
-- Indexes for table `scholarship_courses`
--
ALTER TABLE `scholarship_courses`
  ADD PRIMARY KEY (`scholarship_id`,`course_id`),
  ADD KEY `course_id` (`course_id`);

--
-- Indexes for table `scholarship_tags`
--
ALTER TABLE `scholarship_tags`
  ADD PRIMARY KEY (`scholarship_id`,`tag_id`),
  ADD KEY `tag_id` (`tag_id`);

--
-- Indexes for table `scholarship_year_levels`
--
ALTER TABLE `scholarship_year_levels`
  ADD PRIMARY KEY (`scholarship_id`,`year_level_id`),
  ADD KEY `year_level_id` (`year_level_id`);

--
-- Indexes for table `tags`
--
ALTER TABLE `tags`
  ADD PRIMARY KEY (`tag_id`),
  ADD UNIQUE KEY `tag_name` (`tag_name`);

--
-- Indexes for table `year_levels`
--
ALTER TABLE `year_levels`
  ADD PRIMARY KEY (`year_level_id`),
  ADD UNIQUE KEY `year_level_name` (`year_level_name`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `scholarships`
--
ALTER TABLE `scholarships`
  MODIFY `scholarship_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tags`
--
ALTER TABLE `tags`
  MODIFY `tag_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=98;

--
-- AUTO_INCREMENT for table `year_levels`
--
ALTER TABLE `year_levels`
  MODIFY `year_level_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `course_tags`
--
ALTER TABLE `course_tags`
  ADD CONSTRAINT `course_tags_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `course_tags_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`tag_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `scholarship_courses`
--
ALTER TABLE `scholarship_courses`
  ADD CONSTRAINT `scholarship_courses_ibfk_1` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `scholarship_courses_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE;

--
-- Constraints for table `scholarship_tags`
--
ALTER TABLE `scholarship_tags`
  ADD CONSTRAINT `scholarship_tags_ibfk_1` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `scholarship_tags_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`tag_id`) ON DELETE CASCADE;

--
-- Constraints for table `scholarship_year_levels`
--
ALTER TABLE `scholarship_year_levels`
  ADD CONSTRAINT `scholarship_year_levels_ibfk_1` FOREIGN KEY (`scholarship_id`) REFERENCES `scholarships` (`scholarship_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `scholarship_year_levels_ibfk_2` FOREIGN KEY (`year_level_id`) REFERENCES `year_levels` (`year_level_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
