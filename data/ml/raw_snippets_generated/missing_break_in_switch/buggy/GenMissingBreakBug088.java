public class GenMissingBreakBug088 {
    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "closed";
                break;
            case 5:
                label = "archived";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String describe1(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll4(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}
