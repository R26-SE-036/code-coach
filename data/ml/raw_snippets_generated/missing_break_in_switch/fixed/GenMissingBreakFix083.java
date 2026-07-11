public class GenMissingBreakFix083 {
    static boolean isEven1(int level) {
        return level % 2 == 0;
    }

    static String describe2(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static int drain3(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }
}
