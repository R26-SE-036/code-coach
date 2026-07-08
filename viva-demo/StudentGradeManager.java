public class StudentGradeManager {

    public static void main(String[] args) {
        String[] students = {"Amara", "Bimal", "Chathura", "Dilini"};
        int[] marks = {72, 45, 88, 63};

        System.out.println("=== Student Grade Manager ===");

        for (int i = 0; i < marks.length; i++) {
            String grade = gradeFor(marks[i]);
            System.out.println(students[i] + " scored " + marks[i] + " -> grade " + grade)
        }

        verifyRecord(new String("Chathura"));
        System.out.println("All students processed.");
    }

    static String gradeFor(int mark) {
        if (mark >= 75) {
            return "A";
        } else if (mark >= 65) {
            return "B";
        } else if (mark >= 65) {
            return "C";
        } else {
            return "F";
        }
    }

    static void verifyRecord(String name) {
        if (name == "Chathura") {
            System.out.println("Record verified for " + name);
        } else {
            System.out.println("WARNING: could not verify record for " + name);
        }
    }
}
