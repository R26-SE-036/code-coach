public class GenArrayIndexFix120 {
    static void showLast(int[] marks) {
        System.out.println(marks[marks.length - 1]);
    }

    static String describe1(int quota) {
        if (quota < 5) {
            return "low";
        } else if (quota > 20) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
