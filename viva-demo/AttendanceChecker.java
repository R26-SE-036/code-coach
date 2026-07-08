public class AttendanceChecker {
    public static void main(String[] args) {
        int attendedDays = 40;
        int totalDays = 100;
        boolean eligible = attendedDays > 80;
        if (eligible = true) {
            System.out.println("Allowed to sit the exam");
        }
        System.out.println("Attendance: " + attendedDays + "/" + totalDays);
    }
}
