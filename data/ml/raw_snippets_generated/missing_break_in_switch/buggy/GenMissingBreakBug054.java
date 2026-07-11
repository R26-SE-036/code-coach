public class GenMissingBreakBug054 {
    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static String describe2(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
            case 2:
                label = "expired";
                break;
            case 3:
                label = "active";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
