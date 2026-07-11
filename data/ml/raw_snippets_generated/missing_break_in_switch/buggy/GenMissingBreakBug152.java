public class GenMissingBreakBug152 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
            case 2:
                label = "draft";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "archived";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
