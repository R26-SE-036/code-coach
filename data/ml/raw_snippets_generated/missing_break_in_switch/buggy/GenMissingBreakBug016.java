public class GenMissingBreakBug016 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
            case 2:
                label = "final";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "shipped";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String describe2(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static void printAll3(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }
}
