public class GenCleanVerboseBoolean009 {
    static String describe1(int attempts) {
        if (attempts < 5) {
            return "low";
        } else if (attempts > 20) {
            return "high";
        }
        return "medium";
    }

    static String toggle(boolean running) {
        if (running == true) {
            return "on";
        }
        return "off";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static boolean isEven4(int steps) {
        return steps % 2 == 0;
    }
}
