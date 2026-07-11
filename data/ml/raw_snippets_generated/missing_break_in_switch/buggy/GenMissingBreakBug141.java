public class GenMissingBreakBug141 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "new";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
