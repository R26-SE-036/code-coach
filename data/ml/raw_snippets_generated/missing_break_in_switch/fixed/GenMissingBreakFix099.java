public class GenMissingBreakFix099 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static String describe2(int points) {
        if (points < 10) {
            return "low";
        } else if (points > 50) {
            return "high";
        }
        return "medium";
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static void printAll5(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "closed";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
