public class GenMissingBreakBug103 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "archived";
            case 3:
                label = "active";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
