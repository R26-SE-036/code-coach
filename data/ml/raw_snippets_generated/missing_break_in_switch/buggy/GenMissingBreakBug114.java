public class GenMissingBreakBug114 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
            case 2:
                label = "closed";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int drain2(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }
}
