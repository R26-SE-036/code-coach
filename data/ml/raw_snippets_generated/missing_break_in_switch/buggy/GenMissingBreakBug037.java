public class GenMissingBreakBug037 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static boolean isEven2(int limit) {
        return limit % 2 == 0;
    }

    static int drain3(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static String describe4(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }

    static void printAll5(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "active";
            case 4:
                label = "final";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
